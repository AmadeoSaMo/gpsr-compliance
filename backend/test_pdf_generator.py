"""
Test the PDF generator by calling the preview endpoint and saving the HTML output.
Run: python test_pdf_generator.py
"""
import json
import urllib.request
import urllib.error

payload = {
    "product_name": "Bufanda de Lana Merino Azul Marino",
    "category": "textile",
    "version_number": "1.0",
    "batch_code": "2024-TEX-001",
    "manufacturer_name": "Artesanía Ejemplo S.L.",
    "manufacturer_email": "contacto@artesania-ejemplo.com",
    "manufacturer_address": "Calle Mayor 12, 28001 Madrid, España",
    "target_consumers": "Público adulto general (mayores de 14 años)",
    "description": "Bufanda artesanal tejida a mano en lana merino 100% natural, teñida con colorantes certificados OEKO-TEX. Dimensiones: 180 × 30 cm. Disponible en azul marino, verde bosque y burdeos.",
    "intended_use": "Prenda de abrigo para uso en cuello, destinada a proteger del frío en condiciones de temperatura baja.",
    "foreseeable_misuse": "Uso como juguete por menores de 3 años. Uso como elemento de sujeción o atado.",
    "bom": [
        {"material_name": "Lana Merino 100%", "supplier": "LanaTop S.L.", "origin_country": "España", "certificate": "OEKO-TEX Std 100"},
        {"material_name": "Hilo de refuerzo poliéster", "supplier": "TextilPro", "origin_country": "Portugal", "certificate": "REACH declaración"},
        {"material_name": "Tinte azul marino", "supplier": "ColorNat", "origin_country": "Alemania", "certificate": "OEKO-TEX Std 100"},
    ],
    "risks": [
        {
            "hazard_type": "chemical",
            "hazard_description": "Posibles alérgenos en tintes o aprestos de la lana.",
            "probability": 2, "severity": 2, "risk_score": 4.0, "risk_level": "low",
            "mitigation": "Uso de tintes certificados OEKO-TEX. Declaración del proveedor adjunta en BOM."
        },
        {
            "hazard_type": "thermal",
            "hazard_description": "La lana es inflamable si está en contacto directo con llamas.",
            "probability": 2, "severity": 3, "risk_score": 6.0, "risk_level": "medium",
            "mitigation": "Incluir advertencia en etiqueta: mantener alejado de fuentes de calor y llamas."
        },
        {
            "hazard_type": "physical",
            "hazard_description": "Riesgo de enredo en cuello para niños pequeños.",
            "probability": 3, "severity": 4, "risk_score": 12.0, "risk_level": "medium",
            "mitigation": "Etiqueta con advertencia: no apto para menores de 3 años. No dejar sin supervisión."
        },
    ],
    "mandatory_checks": [
        "Verificar que los tintes cumplen REACH (sin colorantes azo prohibidos).",
        "Comprobar ausencia de cordones en capuchas para niños (ISO 13688).",
        "Incluir instrucciones de lavado y mantenimiento.",
    ],
    "warnings": [
        "⚠️ No apto para niños menores de 3 años. Riesgo de enredo.",
        "⚠️ Mantener alejado del fuego y fuentes de calor directas.",
        "Lavado a mano en agua fría. No usar secadora.",
    ],
    "languages": "Español (ES), English (EN)",
}

url = "http://localhost:8000/api/v1/documents/technical-file/preview"
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
    with open("test_output_expediente.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML generado correctamente: {len(html):,} bytes")
    print("📄 Abre 'test_output_expediente.html' en tu navegador para ver el resultado.")
except urllib.error.URLError as e:
    print(f"❌ Error conectando al servidor: {e}")
    print("    ¿Está corriendo uvicorn? → uvicorn app.main:app --reload")
