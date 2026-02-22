"""Products CRUD API — ProductFamilies and ProductVersions (full CRUD)."""
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import (
    ProductFamily, ProductVersion, BillOfMaterial,
    RiskAssessment, ProductCategory, VersionStatus,
    HazardType, RiskLevel, ResponsiblePerson
)
from app.services.amazon_generator.amazon_service import generate_amazon_image_html

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class BomItemIn(BaseModel):
    material_name: str
    quantity: str | None = None
    origin_country: str | None = None
    notes: str | None = None


class RiskItemIn(BaseModel):
    hazard_type: str = "other"
    hazard_description: str
    probability: int = 1
    severity: int = 1
    risk_score: float = 1.0
    risk_level: str = "low"
    mitigation: str | None = None
    safety_warning_text: str | None = None


class ProductIn(BaseModel):
    product_name: str
    category: str
    version_number: str = "1.0"
    batch_code: str
    description: str
    intended_use: str
    foreseeable_misuse: str | None = None
    target_consumers: str = "Público general adulto"
    warnings: list[str] = []
    bom: list[BomItemIn] = []
    risks: list[RiskItemIn] = []
    label_size_key: str = "brother_62x100"
    manufacturer_name: str = ""
    manufacturer_email: str = ""
    manufacturer_address: str = ""


class ProductOut(BaseModel):
    id: str
    product_name: str
    category: str
    version_number: str
    batch_code: str
    description: str
    intended_use: str
    foreseeable_misuse: str | None
    target_consumers: str
    warnings: list[str]
    bom: list[dict]
    risks: list[dict]
    label_size_key: str
    manufacturer_name: str
    manufacturer_email: str
    manufacturer_address: str
    logo_data: str | None = None
    saved_at: str | None


def _safe_enum(enum_class, value, default):
    try:
        return enum_class(value)
    except Exception:
        return default


def _version_to_out(pv: ProductVersion) -> ProductOut:
    bom_out = [
        {"material_name": b.material_name, "quantity": b.quantity, "origin_country": b.origin_country}
        for b in (pv.bill_of_materials or [])
    ]
    risk_out = [
        {
            "hazard_type": r.hazard_type.value if hasattr(r.hazard_type, 'value') else str(r.hazard_type),
            "hazard_description": r.hazard_description,
            "probability": r.probability,
            "severity": r.severity,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level.value if hasattr(r.risk_level, 'value') else str(r.risk_level),
            "mitigation": r.mitigation_measure,
        }
        for r in (pv.risk_assessments or [])
    ]
    # Recover extra fields stored in notes
    try:
        extra = json.loads(pv.foreseeable_misuse or "{}") if pv.foreseeable_misuse and pv.foreseeable_misuse.startswith("{") else {}
    except Exception:
        extra = {}
    warnings = extra.get("warnings", [])
    label_size_key = extra.get("label_size_key", "brother_62x100")
    mfr_name = extra.get("manufacturer_name", "")
    mfr_email = extra.get("manufacturer_email", "")
    mfr_addr = extra.get("manufacturer_address", "")

    return ProductOut(
        id=str(pv.id),
        product_name=pv.product_name,
        category=pv.family.category.value if pv.family else "other",
        version_number=pv.version_number,
        batch_code=pv.batch_code or "",
        description=pv.product_description,
        intended_use=pv.intended_use,
        foreseeable_misuse=pv.foreseeable_misuse if not pv.foreseeable_misuse or not pv.foreseeable_misuse.startswith("{") else None,
        target_consumers=pv.target_consumers or "Público general adulto",
        warnings=warnings,
        bom=bom_out,
        risks=risk_out,
        label_size_key=label_size_key,
        manufacturer_name=mfr_name,
        manufacturer_email=mfr_email,
        manufacturer_address=mfr_addr,
        logo_data=pv.responsible_person.logo_data if pv.responsible_person else "",
        saved_at=pv.created_at.isoformat() if pv.created_at else None,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductVersion)
        .options(
            selectinload(ProductVersion.family),
            selectinload(ProductVersion.bill_of_materials),
            selectinload(ProductVersion.risk_assessments),
            selectinload(ProductVersion.responsible_person),
        )
    )
    versions = result.scalars().all()
    return [_version_to_out(pv) for pv in versions]


@router.post("/", response_model=ProductOut, status_code=201)
async def create_product(payload: ProductIn, db: AsyncSession = Depends(get_db)):
    try:
        return await _create_product_impl(payload, db)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in create_product: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

async def _create_product_impl(payload: ProductIn, db: AsyncSession):
    # 1. Get or create a ResponsiblePerson (use first existing or create a placeholder)
    rp_result = await db.execute(select(ResponsiblePerson).limit(1))
    rp = rp_result.scalar_one_or_none()
    if not rp:
        rp = ResponsiblePerson(
            id=uuid.uuid4(),
            name=payload.manufacturer_name or "Artesano (configurar en Ajustes)",
            address=payload.manufacturer_address or "Dirección no configurada",
            country="España",
            email=payload.manufacturer_email or "email@noconfigurado.com",
            is_self=True,
        )
        db.add(rp)
        await db.flush()

    # 2. Get or create ProductFamily
    cat = _safe_enum(ProductCategory, payload.category, ProductCategory.OTHER)
    fam_result = await db.execute(
        select(ProductFamily).where(ProductFamily.name == payload.product_name)
    )
    family = fam_result.scalar_one_or_none()
    if not family:
        family = ProductFamily(
            id=uuid.uuid4(),
            name=payload.product_name,
            category=cat,
            description=payload.description,
        )
        db.add(family)
        await db.flush()

    # 3. Store extra fields as JSON in foreseeable_misuse column (temp approach without schema change)
    extra = json.dumps({
        "warnings": payload.warnings,
        "label_size_key": payload.label_size_key,
        "manufacturer_name": payload.manufacturer_name,
        "manufacturer_email": payload.manufacturer_email,
        "manufacturer_address": payload.manufacturer_address,
    })

    # 4. Check if this version already exists for this family
    existing_version_result = await db.execute(
        select(ProductVersion).where(
            ProductVersion.family_id == family.id,
            ProductVersion.version_number == payload.version_number
        )
    )
    if existing_version_result.scalar_one_or_none():
        # Option 1: Raise error
        # raise HTTPException(status_code=400, detail=f"La versión {payload.version_number} para este producto ya existe. Por favor, usa un nombre diferente o incrementa la versión.")
        # Option 2: For this POC, let's just append a random suffix to version if it exists, or update?
        # Let's go with raise error for now as it's safer for data integrity.
        raise HTTPException(status_code=400, detail=f"Ya existe un producto con el nombre '{payload.product_name}' y versión {payload.version_number}. Cambia el nombre o la versión en el primer paso.")

    # 5. Create ProductVersion
    pv = ProductVersion(
        id=uuid.uuid4(),
        family_id=family.id,
        responsible_person_id=rp.id,
        version_number=payload.version_number,
        batch_code=payload.batch_code,
        product_name=payload.product_name,
        product_description=payload.description,
        intended_use=payload.intended_use,
        foreseeable_misuse=extra,
        target_consumers=payload.target_consumers,
        status=VersionStatus.DRAFT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(pv)
    await db.flush()

    # 5. BOM
    for item in payload.bom:
        bom = BillOfMaterial(
            id=uuid.uuid4(),
            product_version_id=pv.id,
            material_name=item.material_name,
            quantity=item.quantity,
            origin_country=item.origin_country,
            notes=item.notes,
        )
        db.add(bom)

    # 6. Risks
    for r in payload.risks:
        ra = RiskAssessment(
            id=uuid.uuid4(),
            product_version_id=pv.id,
            hazard_type=_safe_enum(HazardType, r.hazard_type, HazardType.OTHER),
            hazard_description=r.hazard_description,
            probability=r.probability,
            severity=r.severity,
            risk_score=r.risk_score,
            risk_level=_safe_enum(RiskLevel, r.risk_level, RiskLevel.LOW),
            mitigation_measure=r.mitigation or "Sin mitigación especificada",
            safety_warning_text=r.safety_warning_text,
        )
        db.add(ra)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(ProductVersion)
        .where(ProductVersion.id == pv.id)
        .options(
            selectinload(ProductVersion.family),
            selectinload(ProductVersion.bill_of_materials),
            selectinload(ProductVersion.risk_assessments),
            selectinload(ProductVersion.responsible_person),
        )
    )
    pv_loaded = result.scalar_one()
    return _version_to_out(pv_loaded)


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, payload: ProductIn, db: AsyncSession = Depends(get_db)):
    try:
        # Convert string ID to UUID
        try:
            val_id = uuid.UUID(product_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID de producto no válido")

        # 1. Fetch current version
        result = await db.execute(
            select(ProductVersion)
            .where(ProductVersion.id == val_id)
            .options(
                selectinload(ProductVersion.family),
                selectinload(ProductVersion.bill_of_materials),
                selectinload(ProductVersion.risk_assessments)
            )
        )
        pv = result.scalar_one_or_none()
        if not pv:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        # 2. Update basic fields
        pv.product_name = payload.product_name
        pv.product_description = payload.description
        pv.intended_use = payload.intended_use
        pv.batch_code = payload.batch_code
        pv.updated_at = datetime.utcnow()

        # Update family data if matches
        if pv.family:
            pv.family.name = payload.product_name
            pv.family.category = _safe_enum(ProductCategory, payload.category, ProductCategory.OTHER)
            pv.family.description = payload.description

        # Update extra fields in manageable JSON column
        extra = json.dumps({
            "warnings": payload.warnings,
            "label_size_key": payload.label_size_key,
            "manufacturer_name": payload.manufacturer_name,
            "manufacturer_email": payload.manufacturer_email,
            "manufacturer_address": payload.manufacturer_address,
        })
        pv.foreseeable_misuse = extra

        # 3. Handle children (BOM/Risks). Simple approach: delete all and recreate
        from sqlalchemy import delete
        
        await db.execute(delete(BillOfMaterial).where(BillOfMaterial.product_version_id == pv.id))
        await db.execute(delete(RiskAssessment).where(RiskAssessment.product_version_id == pv.id))
        
        # Add new BOM
        for item in payload.bom:
            bom = BillOfMaterial(
                id=uuid.uuid4(),
                product_version_id=pv.id,
                material_name=item.material_name,
                quantity=item.quantity,
                origin_country=item.origin_country,
                notes=item.notes,
            )
            db.add(bom)

        # Add new Risks
        for r in payload.risks:
            ra = RiskAssessment(
                id=uuid.uuid4(),
                product_version_id=pv.id,
                hazard_type=_safe_enum(HazardType, r.hazard_type, HazardType.OTHER),
                hazard_description=r.hazard_description,
                probability=r.probability,
                severity=r.severity,
                risk_score=r.risk_score,
                risk_level=_safe_enum(RiskLevel, r.risk_level, RiskLevel.LOW),
                mitigation_measure=r.mitigation or "Sin mitigación especificada",
                safety_warning_text=r.safety_warning_text,
            )
            db.add(ra)

        await db.commit()
        
        # Reload and return
        result = await db.execute(
            select(ProductVersion)
            .where(ProductVersion.id == pv.id)
            .options(
                selectinload(ProductVersion.family),
                selectinload(ProductVersion.bill_of_materials),
                selectinload(ProductVersion.risk_assessments),
                selectinload(ProductVersion.responsible_person),
            )
        )
        pv_loaded = result.scalar_one()
        return _version_to_out(pv_loaded)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in update_product: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    # Convert string ID to UUID object for SQLite compatibility
    try:
        val_id = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de producto no válido")

    result = await db.execute(
        select(ProductVersion)
        .where(ProductVersion.id == val_id)
        .options(
            selectinload(ProductVersion.family),
            selectinload(ProductVersion.bill_of_materials),
            selectinload(ProductVersion.risk_assessments),
            selectinload(ProductVersion.responsible_person),
        )
    )
    pv = result.scalar_one_or_none()
    if not pv:
        raise HTTPException(status_code=404, detail="Product not found")
    return _version_to_out(pv)


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductVersion).where(ProductVersion.id == product_id))
    pv = result.scalar_one_or_none()
    if not pv:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(pv)

@router.get("/{product_id}/amazon-image", response_class=HTMLResponse)
async def generate_amazon_image_route(product_id: str, db: AsyncSession = Depends(get_db)):
    try:
        # Convert string ID to UUID object for SQLite compatibility if needed
        try:
            val_id = uuid.UUID(product_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de producto no válido")

        result = await db.execute(
            select(ProductVersion)
            .where(ProductVersion.id == val_id)
            .options(
                selectinload(ProductVersion.responsible_person),
                selectinload(ProductVersion.risk_assessments)
            )
        )
        pv = result.scalar_one_or_none()
        if not pv:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        if not pv.responsible_person:
            raise HTTPException(
                status_code=400, 
                detail="Este producto no tiene una Persona Responsable asignada. Por favor, edita el producto o configura tus datos en Ajustes."
            )

        # Group safety warnings from risk assessments
        warnings = [ra.safety_warning_text for ra in pv.risk_assessments if ra.safety_warning_text]
        
        m_addr = pv.responsible_person.address or ""
        m_country = pv.responsible_person.country or ""
        full_address = f"{m_addr}, {m_country}" if m_country else m_addr

        data = {
            "product_name": pv.product_name,
            "batch_code": pv.batch_code or "N/A",
            "manufacturer_name": pv.responsible_person.name,
            "manufacturer_address": full_address,
            "manufacturer_email": pv.responsible_person.email,
            "logo_data": pv.responsible_person.logo_data,
            "safety_warnings": warnings
        }

        return generate_amazon_image_html(data)
    except Exception as e:
        import traceback
        error_msg = f"Error in generate_amazon_image_route: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
