"""
Amazon Art. 19 Image Generator — GPSR Compliance
------------------------------------------------
Generates a 1:1 (square) high-resolution HTML template that can be 
converted to PNG for Amazon listings.
"""
import base64

def generate_amazon_image_html(data: dict) -> str:
    """
    data expects:
      - product_name
      - batch_code
      - manufacturer_name
      - manufacturer_address
      - manufacturer_email
      - logo_data (base64)
      - safety_warnings (list of strings)
    """
    
    warnings_list = data.get("safety_warnings", [])
    if not warnings_list:
        warnings_html = "<li>No se requieren advertencias específicas de seguridad para el uso normal de este producto.</li>"
    else:
        warnings_html = "".join([f"<li>{w}</li>" for w in warnings_list])

    logo_html = ""
    if data.get("logo_data"):
        logo_html = f'<img src="{data["logo_data"]}" class="logo" />'

    safe_product_name = data.get('product_name', 'producto').replace(' ', '-').replace('"', '').replace("'", "")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Amazon GPSR - {data['product_name']}</title>
    <style>
        :root {{
            --primary: #232f3e; /* Amazon Dark Blue */
            --accent: #ff9900;  /* Amazon Orange */
            --text: #111;
            --border: #ddd;
            --bg: #fff;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: "Helvetica Neue", Arial, sans-serif;
            background: #f0f0f0;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px;
        }}
        .amazon-image-container {{
            width: 800px;
            height: 800px;
            background: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            padding: 0;
            position: relative;
            overflow: hidden;
            border: 1px solid #eee;
        }}
        
        .header {{
            background: var(--primary);
            color: white;
            padding: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header-title {{
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }}
        .header-tag {{
            font-size: 14px;
            background: var(--accent);
            color: var(--primary);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .main-content {{
            flex: 1;
            padding: 40px;
            display: flex;
            flex-direction: column;
            gap: 30px;
        }}

        .section {{
            border-left: 4px solid var(--accent);
            padding-left: 20px;
        }}
        .section-title {{
            font-size: 16px;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 8px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .content-text {{
            font-size: 20px;
            font-weight: 500;
            line-height: 1.4;
            color: var(--text);
        }}

        .warnings-box {{
            background: #fffafa;
            border: 2px solid #fee;
            border-radius: 12px;
            padding: 25px;
            flex: 1;
        }}
        .warnings-title {{
            display: flex;
            align-items: center;
            gap: 10px;
            color: #d32f2f;
            font-weight: 700;
            font-size: 18px;
            margin-bottom: 15px;
        }}
        .warnings-list {{
            list-style: none;
        }}
        .warnings-list li {{
            font-size: 17px;
            margin-bottom: 10px;
            line-height: 1.4;
            position: relative;
            padding-left: 20px;
        }}
        .warnings-list li::before {{
            content: "•";
            position: absolute;
            left: 0;
            color: var(--accent);
            font-weight: bold;
        }}

        .footer {{
            padding: 30px 40px;
            border-top: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            background: #fafafa;
        }}
        .logo-container {{
            max-width: 180px;
            max-height: 60px;
        }}
        .logo {{
            max-width: 100%;
            max-height: 60px;
            object-fit: contain;
        }}
        .batch-info {{
            text-align: right;
            font-size: 14px;
            color: #888;
        }}

        .toolbar {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }}
        .btn {{
            padding: 10px 20px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .btn-primary {{ background: var(--accent); color: var(--primary); }}
        .btn-primary:hover {{ filter: brightness(1.1); }}

        @media print {{
            .toolbar {{ display: none; }}
            body {{ padding: 0; background: white; }}
            .amazon-image-container {{ box-shadow: none; border: none; }}
        }}
    </style>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
</head>
<body>
    <div class="toolbar">
        <button class="btn btn-primary" onclick="downloadImage()">⬇ Guardar como Imagen (PNG)</button>
        <button class="btn" style="background: #ddd" onclick="window.close()">Cerrar</button>
    </div>

    <div class="amazon-image-container" id="amazon-capture">
        <div class="header">
            <div>
                <div class="header-title">INFORMACIÓN DE SEGURIDAD</div>
                <div style="font-size: 14px; opacity: 0.8;">Cumplimiento Reglamento (UE) 2023/988 (GPSR)</div>
            </div>
            <div class="header-tag">Art. 19</div>
        </div>

        <div class="main-content">
            <div class="section">
                <div class="section-title">Fabricante / Persona Responsable</div>
                <div class="content-text">{data['manufacturer_name']}</div>
                <div style="font-size: 16px; color: #555; margin-top: 4px;">
                    {data['manufacturer_address']}
                </div>
                <div style="font-size: 16px; color: var(--primary); font-weight: 600; margin-top: 4px;">
                    {data['manufacturer_email']}
                </div>
            </div>

            <div class="section">
                <div class="section-title">Producto</div>
                <div class="content-text">{data['product_name']}</div>
            </div>

            <div class="warnings-box">
                <div class="warnings-title">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m12 9 4 7H8l4-7Z"/><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Zm0 16a1 1 0 1 1 0-2 1 1 0 0 1 0 2Zm1-5h-2V7h2Z"/></svg>
                    ADVERTENCIAS DE SEGURIDAD
                </div>
                <ul class="warnings-list">
                    {warnings_html}
                </ul>
            </div>
        </div>

        <div class="footer">
            <div class="logo-container">
                {logo_html}
            </div>
            <div class="batch-info">
                <strong>Lote / Trazabilidad:</strong><br/>
                {data.get('batch_code', 'N/A')}
            </div>
        </div>
    </div>

    <script>
        function downloadImage() {{
            const btn = document.querySelector('.btn-primary');
            btn.disabled = true;
            btn.innerText = 'Generando...';
            
            html2canvas(document.getElementById('amazon-capture'), {{
                scale: 2,
                useCORS: true,
                backgroundColor: "#ffffff"
            }}).then(canvas => {{
                const link = document.createElement('a');
                link.download = "Amazon-GPSR-{safe_product_name}.png";
                link.href = canvas.toDataURL("image/png");
                link.click();
                
                btn.disabled = false;
                btn.innerText = '⬇ Guardar como Imagen (PNG)';
            }});
        }}
    </script>
</body>
</html>"""
    return html
