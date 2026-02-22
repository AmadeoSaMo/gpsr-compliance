"""Document Generator API — Technical File + Physical Label"""
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import Response, HTMLResponse
from pydantic import BaseModel

from app.services.pdf_generator.pdf_service import generate_technical_file_pdf, render_technical_file_html
from app.services.label_generator.label_service import (
    generate_label_pdf, generate_label_html, get_label_sizes_for_ui
)


router = APIRouter()


class BomItem(BaseModel):
    material_name: str
    supplier: str | None = None
    origin_country: str | None = None
    certificate: str | None = None


class RiskItem(BaseModel):
    hazard_type: str
    hazard_description: str
    probability: int
    severity: int
    risk_score: float
    risk_level: str
    mitigation: str | None = None


class TechnicalFileRequest(BaseModel):
    product_name: str
    category: str
    version_number: str = "1.0"
    batch_code: str
    manufacturer_name: str
    manufacturer_email: str
    manufacturer_address: str
    logo_data: str | None = None
    target_consumers: str = "Público general adulto"
    description: str
    intended_use: str
    foreseeable_misuse: str | None = None
    bom: list[BomItem] = []
    risks: list[RiskItem] = []
    mandatory_checks: list[str] = []
    warnings: list[str] = []
    languages: str = "Español (ES)"


@router.post("/technical-file/pdf")
async def generate_technical_file(payload: TechnicalFileRequest):
    """
    Generates and streams the GPSR Technical File as a downloadable PDF.
    """
    data = payload.model_dump()
    data["issued_date"] = datetime.utcnow()

    try:
        pdf_bytes = generate_technical_file_pdf(data)
        filename = f"expediente_tecnico_{payload.batch_code}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except RuntimeError:
        # WeasyPrint not available — tell frontend to open the print page
        return {"print_url": f"/api/v1/documents/technical-file/print"}


@router.post("/technical-file/preview", response_class=HTMLResponse)
async def preview_technical_file(payload: TechnicalFileRequest):
    """
    Returns the rendered HTML for browser preview (without PDF conversion).
    Useful for development and testing.
    """
    data = payload.model_dump()
    data["issued_date"] = datetime.utcnow()
    html = render_technical_file_html(data)
    return HTMLResponse(content=html)


@router.post("/technical-file/print", response_class=HTMLResponse)
async def print_technical_file(payload: TechnicalFileRequest):
    """
    Returns the Technical File HTML with a print toolbar injected.
    Open in a new tab; the browser handles printing / Save as PDF.
    """
    data = payload.model_dump()
    data["issued_date"] = datetime.utcnow()
    html = render_technical_file_html(data)
    # Inject print toolbar and auto-print script into the HTML
    toolbar = """
<div style="position:fixed;top:0;left:0;right:0;z-index:9999;
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 24px;background:#1e293b;color:#f8fafc;
  font-family:system-ui,sans-serif;font-size:13px;
  box-shadow:0 2px 8px rgba(0,0,0,0.4);">
  <div style="display:flex;flex-direction:column;gap:2px">
    <strong>Expediente Técnico GPSR</strong>
    <span style="color:#94a3b8">Usa el diálogo de impresión para guardar como PDF</span>
  </div>
  <div style="display:flex;gap:10px">
    <button onclick="window.print()" style="background:#3b82f6;color:#fff;border:none;border-radius:6px;padding:9px 18px;font-size:13px;font-weight:600;cursor:pointer">
      🖨️ Imprimir / Guardar PDF
    </button>
    <button onclick="window.close()" style="background:transparent;color:#94a3b8;border:1px solid #475569;border-radius:6px;padding:9px 14px;font-size:13px;cursor:pointer">
      ✕ Cerrar
    </button>
  </div>
</div>
<style>
@media print { div[style*="position:fixed"] { display:none!important; } body { padding-top: 0!important; } }
body { padding-top: 60px; }
</style>
<script>window.addEventListener('load', () => setTimeout(() => window.print(), 800))</script>"""
    # Insert toolbar just after <body>
    if "<body" in html:
        idx = html.index("<body") + html[html.index("<body"):].index(">") + 1
        html = html[:idx] + toolbar + html[idx:]
    return HTMLResponse(content=html)


# -------------------------------------------------------------------------
# Label routes
# -------------------------------------------------------------------------

class LabelRequest(BaseModel):
    product_name: str
    batch_code: str
    manufacturer_name: str
    manufacturer_email: str
    manufacturer_address: str
    logo_data: str | None = None
    warnings: list[str] = []
    label_size_key: str = "brother_62x100"


@router.get("/label/sizes")
async def get_label_sizes():
    """Returns all available label sizes for the frontend selector."""
    return {"sizes": get_label_sizes_for_ui()}


@router.post("/label/preview", response_class=HTMLResponse)
async def preview_label(payload: LabelRequest):
    """Returns the label as a rendered HTML page (browser preview)."""
    html = generate_label_html(payload.model_dump())
    return HTMLResponse(content=html)


@router.post("/label/pdf")
async def download_label(payload: LabelRequest):
    """Generates and streams the label as a downloadable PDF."""
    try:
        pdf_bytes = generate_label_pdf(payload.model_dump())
        filename = f"etiqueta_{payload.batch_code}_{payload.label_size_key}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except RuntimeError:
        # WeasyPrint not available — tell frontend to open the print page
        return {"print_url": "/label/print"}


@router.post("/label/print", response_class=HTMLResponse)
async def print_label(payload: LabelRequest):
    """
    Returns the label HTML with print toolbar + auto-print.
    Open in a new tab for printing or saving as PDF.
    """
    html = generate_label_html(payload.model_dump(), print_mode=True)
    return HTMLResponse(content=html)


@router.post("/{product_version_id}/amazon-pack")
async def generate_amazon_pack(product_version_id: str):
    return {"message": f"Amazon Pack (image + text) for {product_version_id} — próximamente"}
