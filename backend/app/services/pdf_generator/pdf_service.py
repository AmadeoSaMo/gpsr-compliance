"""
PDF Generator Service — GPSR Technical File
---------------------------------------------
Hexagonal Architecture: this is an OUTPUT ADAPTER.
It takes a pure domain data dict and produces a PDF file.

Uses:
  - Jinja2 for HTML templating
  - WeasyPrint for HTML→PDF conversion

Usage:
    from app.services.pdf_generator.pdf_service import generate_technical_file_pdf
    pdf_bytes = generate_technical_file_pdf(data)
"""
import io
from datetime import datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "static" / "templates"

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


CATEGORY_LABELS = {
    "textile": "Textiles (ropa, bufandas, accesorios)",
    "jewellery": "Joyería y bisutería",
    "candle": "Velas y aromaterapia",
    "ceramic": "Cerámica y alfarería",
    "wood": "Madera y carpintería",
    "cosmetic": "Cosméticos y jabones",
    "toy": "Juguetes",
    "paper": "Papel y cuadernos",
    "other": "Otro",
}


def _compute_retention(issued_date: datetime) -> str:
    """10 years from issue date as required by GPSR Art. 9."""
    delta = issued_date + timedelta(days=365 * 10 + 2)  # +2 for leap years
    return delta.strftime("%d/%m/%Y")


def render_technical_file_html(data: dict) -> str:
    """
    Renders the Jinja2 template with domain data.
    Returns the HTML string (useful for testing/preview).
    """
    template = jinja_env.get_template("technical_file.html")
    issued = data.get("issued_date", datetime.utcnow())
    if isinstance(issued, str):
        try:
            issued = datetime.fromisoformat(issued)
        except ValueError:
            issued = datetime.utcnow()

    context = {
        "product_name": data.get("product_name", "—"),
        "category_label": CATEGORY_LABELS.get(data.get("category", "other"), data.get("category", "—")),
        "version_number": data.get("version_number", "1.0"),
        "batch_code": data.get("batch_code", "N/A"),
        "manufacturer_name": data.get("manufacturer_name", "—"),
        "manufacturer_email": data.get("manufacturer_email", "—"),
        "manufacturer_address": data.get("manufacturer_address", "—"),
        "issued_date": issued.strftime("%d/%m/%Y"),
        "retention_until": _compute_retention(issued),
        "target_consumers": data.get("target_consumers", "Público general adulto"),
        "description": data.get("description", "—"),
        "intended_use": data.get("intended_use", "—"),
        "foreseeable_misuse": data.get("foreseeable_misuse"),
        "bom": data.get("bom", []),
        "risks": data.get("risks", []),
        "mandatory_checks": data.get("mandatory_checks", []),
        "warnings": data.get("warnings", []),
        "languages": data.get("languages", "Español (ES)"),
    }
    return template.render(**context)


def generate_technical_file_pdf(data: dict) -> bytes:
    """
    Generates a complete GPSR Technical File PDF.
    Returns PDF as bytes (ready to stream to client or save to disk).
    """
    try:
        from weasyprint import HTML, CSS
        html_content = render_technical_file_html(data)
        pdf_bytes = HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()
        return pdf_bytes
    except ImportError:
        raise RuntimeError(
            "WeasyPrint no está instalado correctamente. "
            "En Windows necesita GTK. Instala con: pip install weasyprint"
        )
