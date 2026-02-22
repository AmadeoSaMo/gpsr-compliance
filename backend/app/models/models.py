"""
Database Models — GPSR Compliance SaaS
---------------------------------------
Hexagonal Architecture: Domain layer (the legal core) is modelled here.
Key design decisions:
  - Products are VERSIONED. Once a version is released you CANNOT delete it.
    You create a new version instead. This is legally required (10yr retention).
  - Every Product belongs to a ProductFamily for grouping (bufandas de lana, etc.)
  - Risk Assessment lives in its own table linked to a ProductVersion.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProductCategory(str, enum.Enum):
    TEXTILE = "textile"          # Ropa, bufandas, bolsos
    JEWELLERY = "jewellery"      # Joyería y bisutería
    TOY = "toy"                  # Juguetes
    CANDLE = "candle"            # Velas y aromaterapia
    COSMETIC = "cosmetic"        # Jabones, cremas (requiere CPNP adicional)
    CERAMIC = "ceramic"          # Cerámica, alfarería
    WOOD = "wood"                # Productos de madera
    PAPER = "paper"              # Papel, cuadernos artesanales
    OTHER = "other"


class HazardType(str, enum.Enum):
    PHYSICAL = "physical"          # Cortes, asfixia, atrapamiento
    CHEMICAL = "chemical"          # Pinturas, barnices, tintes
    THERMAL = "thermal"            # Quemaduras, inflamabilidad
    ELECTRICAL = "electrical"      # Circuitos, baterías
    BIOLOGICAL = "biological"      # Alérgenos, moho
    MECHANICAL = "mechanical"      # Rotura, astillas
    OTHER = "other"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VersionStatus(str, enum.Enum):
    DRAFT = "draft"          # En construcción
    RELEASED = "released"    # Publicado (edición bloqueada)
    SUPERSEDED = "superseded"  # Reemplazado por una versión más nueva
    RECALLED = "recalled"    # Retirado del mercado


# ---------------------------------------------------------------------------
# Responsible Person (Persona Responsable EU)
# ---------------------------------------------------------------------------

class ResponsiblePerson(Base):
    """
    The EU Responsible Person (Art. 4 GPSR): the legal entity in the EU
    accountable for the product. For EU-based artisans, this is themselves.
    """
    __tablename__ = "responsible_persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    trade_name = Column(String(255), nullable=True)
    address = Column(Text, nullable=False)
    country = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    logo_data = Column(Text, nullable=True)   # Base64 string for the brand logo
    is_self = Column(Boolean, default=True)   # True = artisan IS the RP

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product_versions = relationship("ProductVersion", back_populates="responsible_person")


# ---------------------------------------------------------------------------
# Supplier / Material Traceability
# ---------------------------------------------------------------------------

class Supplier(Base):
    """Traceability of material suppliers. Required by GPSR."""
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    country_of_origin = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    bill_of_materials = relationship("BillOfMaterial", back_populates="supplier")


# ---------------------------------------------------------------------------
# Product Family (Agrupación de Productos)
# ---------------------------------------------------------------------------

class ProductFamily(Base):
    """
    Groups similar products that share the same base materials and risk profile.
    Example: 'Bufandas de lana merino' covers all colors/sizes.
    """
    __tablename__ = "product_families"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(Enum(ProductCategory), nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    versions = relationship("ProductVersion", back_populates="family")


# ---------------------------------------------------------------------------
# Product Version (El core del Expediente Técnico)
# ---------------------------------------------------------------------------

class ProductVersion(Base):
    """
    IMMUTABLE after status=RELEASED.
    Represents a specific version of a product with its full technical file.
    Creating a new variation = create a new ProductVersion (v1.1, v2.0, etc.)
    """
    __tablename__ = "product_versions"
    __table_args__ = (
        UniqueConstraint("family_id", "version_number", name="uq_family_version"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_id = Column(UUID(as_uuid=True), ForeignKey("product_families.id"), nullable=False)
    responsible_person_id = Column(UUID(as_uuid=True), ForeignKey("responsible_persons.id"), nullable=False)

    version_number = Column(String(20), nullable=False)  # e.g. "1.0", "1.1"
    batch_code = Column(String(100), nullable=True)      # e.g. "2024-BUFANDA-001"
    status = Column(Enum(VersionStatus), default=VersionStatus.DRAFT, nullable=False)

    # Technical File fields
    product_name = Column(String(255), nullable=False)
    product_description = Column(Text, nullable=False)
    intended_use = Column(Text, nullable=False)
    foreseeable_misuse = Column(Text, nullable=True)
    target_consumers = Column(String(255), nullable=True)  # JSON array stored as string

    # Legal
    applied_standards = Column(Text, nullable=True)        # JSON list of EN/ISO standards
    declaration_of_conformity_path = Column(String(500), nullable=True)

    # Retention: legally required for 10 years
    released_at = Column(DateTime, nullable=True)
    retention_until = Column(DateTime, nullable=True)  # released_at + 10 years

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    family = relationship("ProductFamily", back_populates="versions")
    responsible_person = relationship("ResponsiblePerson", back_populates="product_versions")
    bill_of_materials = relationship("BillOfMaterial", back_populates="product_version", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="product_version", cascade="all, delete-orphan")
    generated_documents = relationship("GeneratedDocument", back_populates="product_version", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="product_version")


# ---------------------------------------------------------------------------
# Bill of Materials (BOM)
# ---------------------------------------------------------------------------

class BillOfMaterial(Base):
    """Materials used in a product version with supplier traceability."""
    __tablename__ = "bill_of_materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_version_id = Column(UUID(as_uuid=True), ForeignKey("product_versions.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)

    material_name = Column(String(255), nullable=False)   # e.g. "Lana merino"
    quantity = Column(String(100), nullable=True)          # e.g. "500g"
    origin_country = Column(String(100), nullable=True)
    certificate_path = Column(String(500), nullable=True)  # Supplier's quality cert
    notes = Column(Text, nullable=True)

    product_version = relationship("ProductVersion", back_populates="bill_of_materials")
    supplier = relationship("Supplier", back_populates="bill_of_materials")


# ---------------------------------------------------------------------------
# Risk Assessment
# ---------------------------------------------------------------------------

class RiskAssessment(Base):
    """
    One risk assessment per identified hazard per product version.
    The risk engine pre-populates these based on category + materials.
    """
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_version_id = Column(UUID(as_uuid=True), ForeignKey("product_versions.id"), nullable=False)

    hazard_type = Column(Enum(HazardType), nullable=False)
    hazard_description = Column(Text, nullable=False)

    # Risk matrix: 1-5 scale
    probability = Column(Integer, nullable=False)  # 1=rare, 5=almost certain
    severity = Column(Integer, nullable=False)      # 1=negligible, 5=critical
    risk_score = Column(Float, nullable=False)      # probability * severity
    risk_level = Column(Enum(RiskLevel), nullable=False)

    # Mitigation
    mitigation_measure = Column(Text, nullable=False)
    safety_warning_text = Column(Text, nullable=True)  # Exact label text

    created_at = Column(DateTime, default=datetime.utcnow)

    product_version = relationship("ProductVersion", back_populates="risk_assessments")


# ---------------------------------------------------------------------------
# Generated Documents
# ---------------------------------------------------------------------------

class DocumentType(str, enum.Enum):
    TECHNICAL_FILE = "technical_file"       # Expediente Técnico PDF
    LABEL_PRINT = "label_print"             # Etiqueta física PDF
    AMAZON_IMAGE = "amazon_image"           # Imagen Art. 19
    AMAZON_TEXT = "amazon_text"             # Texto para Seller Central
    DECLARATION_CONFORMITY = "declaration_of_conformity"


class GeneratedDocument(Base):
    """Tracks all generated outputs per product version."""
    __tablename__ = "generated_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_version_id = Column(UUID(as_uuid=True), ForeignKey("product_versions.id"), nullable=False)

    doc_type = Column(Enum(DocumentType), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    product_version = relationship("ProductVersion", back_populates="generated_documents")


# ---------------------------------------------------------------------------
# Post-Sale Complaint / Incident Log
# ---------------------------------------------------------------------------

class Complaint(Base):
    """
    GPSR requires logging all safety complaints.
    Serious incidents must be reported to Safety Business Gateway.
    """
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_version_id = Column(UUID(as_uuid=True), ForeignKey("product_versions.id"), nullable=False)

    reported_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=False)
    is_serious = Column(Boolean, default=False)           # Triggers Safety Business Gateway alert
    authority_notified = Column(Boolean, default=False)
    resolution = Column(Text, nullable=True)

    product_version = relationship("ProductVersion", back_populates="complaints")
