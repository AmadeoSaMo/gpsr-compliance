"""
Label Generator Service — GPSR Physical Label
-----------------------------------------------
Generates a physical label HTML/PDF in the exact size selected by the user.

Each label contains the GPSR mandatory fields per Art. 19:
  - Manufacturer name
  - Postal address & email
  - Batch/lot code (traceability)
  - Safety warnings
  - Country of origin (optional)

Screen rendering: text never clips (min-height, no overflow:hidden).
Print rendering:  exact @page dimensions; JS auto-fit shrinks font if needed.
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "static" / "templates"

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)

# ---------------------------------------------------------------------------
# Label size catalogue
# ---------------------------------------------------------------------------

LABEL_SIZES = {
    # key: (width_mm, height_mm, display_name, font_scale)
    "brother_29x90":  (29,  90,  "Brother QL — 29×90mm (dirección pequeña)", 0.72),
    "brother_38x90":  (38,  90,  "Brother QL — 38×90mm (estándar)", 0.85),
    "brother_62x29":  (62,  29,  "Brother QL — 62×29mm (tag pequeño)", 0.75),
    "brother_62x100": (62,  100, "Brother QL — 62×100mm (grande)", 1.0),
    "generic_50x30":  (50,  30,  "Genérica — 50×30mm (tag producto)", 0.7),
    "dymo_57x32":     (57,  32,  "Dymo LabelWriter — 57×32mm (pequeña)", 0.75),
    "dymo_89x36":     (89,  36,  "Dymo LabelWriter — 89×36mm (estándar)", 0.85),
    "dymo_101x54":    (101, 54,  "Dymo LabelWriter — 101×54mm (grande)", 1.0),
    "zebra_100x150":  (100, 150, "Zebra / Genérica — 100×150mm (envío)", 1.1),
    "a6_148x105":     (148, 105, "A6 — 148×105mm (hoja de etiquetas)", 1.2),
}

DEFAULT_SIZE_KEY = "brother_62x100"


def get_label_sizes_for_ui() -> list[dict]:
    """Returns the list of label sizes for the frontend selector."""
    return [
        {"key": k, "label": v[2], "width_mm": v[0], "height_mm": v[1]}
        for k, v in LABEL_SIZES.items()
    ]


def _mm_to_pt(mm: float) -> float:
    return mm * 2.8346


def generate_label_html(data: dict, print_mode: bool = False) -> str:
    """Renders the label as a standalone HTML page sized to the chosen label.

    Screen behaviour : label expands vertically to show all content (no clipping).
    Print behaviour  : exact @page dimensions; JS auto-fit shrinks font if needed.
    """
    size_key = data.get("label_size_key", DEFAULT_SIZE_KEY)
    w_mm, h_mm, size_name, font_scale = LABEL_SIZES.get(size_key, LABEL_SIZES[DEFAULT_SIZE_KEY])

    landscape = w_mm > h_mm

    # Larger base fonts for better readability
    base_font = round(9 * font_scale, 1)
    title_font = round(11 * font_scale, 1)

    # Build warning HTML
    warnings = data.get("warnings", [])
    warning_html = ""
    if warnings:
        items = "".join(f"<div class='warn-line'>{w}</div>" for w in warnings)
        warning_html = f"<div class='warn-block'>{items}</div>"

    # Logo HTML
    logo_html = ""
    if data.get("logo_data"):
        logo_html = f'<img src="{data["logo_data"]}" class="brand-logo" />'

    # Toolbar (print-mode only)
    toolbar_html = ""
    print_script = ""
    if print_mode:
        toolbar_html = f"""
<div class="print-toolbar">
  <div class="toolbar-info">
    <strong>Etiqueta: {size_name}</strong>
    <span>{w_mm}&times;{h_mm} mm &mdash; {data.get('batch_code','')}</span>
  </div>
  <div class="toolbar-actions">
    <button class="btn-print" onclick="window.print()">🖨️ Imprimir / Guardar como PDF</button>
    <button class="btn-close" onclick="window.close()">✕ Cerrar</button>
  </div>
</div>"""
        print_script = "<script>window.addEventListener('load', () => { setTimeout(() => window.print(), 600) })</script>"

    toolbar_css = """
  .print-toolbar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 20px; gap: 16px;
    background: #1e293b; color: #f8fafc;
    font-family: system-ui, sans-serif; font-size: 13px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  }
  .toolbar-info { display: flex; flex-direction: column; gap: 2px; }
  .toolbar-actions { display: flex; gap: 10px; }
  .btn-print {
    background: #3b82f6; color: #fff; border: none; border-radius: 6px;
    padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer;
  }
  .btn-print:hover { background: #2563eb; }
  .btn-close {
    background: transparent; color: #94a3b8; border: 1px solid #475569;
    border-radius: 6px; padding: 8px 12px; font-size: 13px; cursor: pointer;
  }
  .btn-close:hover { color: #f8fafc; border-color: #94a3b8; }
  .label-wrapper {
    display: flex; justify-content: center; align-items: flex-start;
    min-height: 100vh; background: #0f172a;
    padding: 80px 24px 40px;
  }
  @media print {
    .print-toolbar { display: none !important; }
    body { background: white !important; margin: 0; padding: 0; }
    .label-wrapper { display: block; padding: 0; min-height: unset; background: none; }
    .label { height: """ + f"{h_mm}mm" + """ !important; min-height: unset !important; overflow: hidden !important; }
  }""" if print_mode else ""

    wrapper_open = '<div class="label-wrapper">' if print_mode else ""
    wrapper_close = "</div>" if print_mode else ""

    # Auto-fit: shrinks font until content fits in the fixed print area
    autofit_script = """
<script>
(function() {
  var label = document.getElementById('gpsr-label');
  if (!label) return;
  var minPx = 6;
  requestAnimationFrame(function() {
    var fs = parseFloat(window.getComputedStyle(label).fontSize);
    var tries = 0;
    while (tries++ < 60 &&
           (label.scrollHeight > label.clientHeight + 2 ||
            label.scrollWidth  > label.clientWidth  + 2) &&
           fs > minPx) {
      fs -= 0.5;
      label.style.fontSize = fs + 'px';
    }
  });
})();
</script>"""

    pad = f"{max(2, 2.5 * font_scale):.1f}mm"
    gap = f"{max(1.5, 2 * font_scale):.1f}mm"
    col_gap = f"{max(1.5, 1.8 * font_scale):.1f}mm"
    col_pad = f"{max(2, 2.5 * font_scale):.1f}mm"
    col_mar = f"{max(1, 1.5 * font_scale):.1f}mm"
    fg_mb = f"{max(1, 1.2 * font_scale):.1f}mm"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Etiqueta {data.get('batch_code','')}</title>
<style>
  @page {{
    size: {w_mm}mm {h_mm}mm;
    margin: 0;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: {base_font}pt;
    color: #111;
  }}
  .label {{
    width: {w_mm}mm;
    min-height: {h_mm}mm;   /* expands on screen */
    border: 0.3mm solid #333;
    display: flex;
    flex-direction: {'row' if landscape else 'column'};
    padding: {pad};
    gap: {gap};
    background: #fff;
  }}
  .col-left {{
    flex: {'0 0 55%' if landscape else '1'};
    display: flex;
    flex-direction: column;
    gap: {col_gap};
  }}
  .col-right {{
    flex: {'0 0 43%' if landscape else '0 0 auto'};
    display: flex;
    flex-direction: column;
    align-items: {'flex-end' if landscape else 'flex-start'};
    justify-content: {'center' if landscape else 'flex-start'};
    gap: {col_gap};
    border-{'left' if landscape else 'top'}: 0.3mm solid #ccc;
    padding-{'left' if landscape else 'top'}: {col_pad};
    margin-{'left' if landscape else 'top'}: {col_mar};
  }}
  .product-name {{
    font-size: {title_font}pt;
    font-weight: 700;
    line-height: 1.25;
    color: #000;
  }}
  .field-label {{
    font-size: {base_font * 0.78:.1f}pt;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 0.4mm;
  }}
  .field-value {{
    font-size: {base_font:.1f}pt;
    line-height: 1.4;
    word-break: break-word;
  }}
  .field-group {{ margin-bottom: {fg_mb}; }}
  .batch-box {{
    border: 0.4mm solid #000;
    border-radius: 0.5mm;
    padding: {max(0.8, 1*font_scale):.1f}mm {max(1.5, 2*font_scale):.1f}mm;
    font-family: monospace;
    font-size: {base_font * 0.9:.1f}pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    white-space: nowrap;
  }}
  .batch-label {{
    font-size: {base_font * 0.72:.1f}pt;
    color: #555;
    margin-bottom: 0.3mm;
  }}
  .warn-block {{
    border: 0.4mm solid #a00;
    border-radius: 0.5mm;
    padding: {max(0.8, 1*font_scale):.1f}mm;
    background: #fff5f5;
  }}
  .warn-line {{
    font-size: {base_font * 0.85:.1f}pt;
    color: #900;
    line-height: 1.35;
  }}
  .gpsr-tag {{
    font-size: {base_font * 0.72:.1f}pt;
    color: #777;
    border: 0.3mm solid #ccc;
    border-radius: 0.4mm;
    padding: 0.3mm {max(1, 1.2*font_scale):.1f}mm;
    white-space: nowrap;
    align-self: flex-start;
  }}
  .brand-logo {{
    max-height: {max(8, 12*font_scale):.1f}mm;
    max-width: 100%;
    object-fit: contain;
    margin-bottom: 1.5mm;
  }}
  {toolbar_css}
</style>
</head>
<body>
{toolbar_html}
{wrapper_open}
<div class="label" id="gpsr-label">
  <div class="col-left">
    <div class="product-name">{data.get('product_name','Producto')}</div>

    <div class="field-group">
      <div class="field-label">Fabricante / Persona Responsable</div>
      <div class="field-value">{data.get('manufacturer_name','—')}</div>
      <div class="field-value">{data.get('manufacturer_address','')}</div>
      <div class="field-value">{data.get('manufacturer_email','')}</div>
    </div>

    {warning_html}
  </div>

  <div class="col-right">
    {logo_html}
    <div>
      <div class="batch-label">LOTE / BATCH</div>
      <div class="batch-box">{data.get('batch_code','N/A')}</div>
    </div>
    <div style="flex:1"></div>
    <div class="gpsr-tag">Reg. (UE) 2023/988</div>
  </div>
</div>
{wrapper_close}
{autofit_script}
{print_script}
</body>
</html>"""
    return html


def generate_label_pdf(data: dict) -> bytes:
    """
    Returns the label as PDF bytes.
    Tries WeasyPrint first; if unavailable raises so the caller falls back to HTML.
    """
    try:
        from weasyprint import HTML
        html = generate_label_html(data, print_mode=False)
        return HTML(string=html).write_pdf()
    except (ImportError, Exception):
        raise RuntimeError("weasyprint_unavailable")
