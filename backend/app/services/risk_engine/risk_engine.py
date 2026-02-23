"""
Risk Engine — GPSR Compliance SaaS
------------------------------------
This is the CORE DOMAIN of the hexagonal architecture.
It contains NO database or HTTP logic — only legal/business rules.

Key data:
  - MATERIAL_RISK_MAP: Pre-loaded hazard suggestions per material keyword.
  - CATEGORY_REQUIRED_CHECKS: Mandatory checks per product category.
  - calculate_risk_level(): Implements the 5x5 risk matrix.
  - analyze_materials(): Returns risks WITH pre-filled mitigation suggestions.
  - suggest_warnings(): Generates safety warnings from detected risks.
"""
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# 5×5 Risk Matrix
# ---------------------------------------------------------------------------

def calculate_risk_level(probability: int, severity: int) -> tuple[float, str]:
    """
    Returns (risk_score, risk_level) based on a 5x5 matrix.
    probability: 1 (rare) → 5 (almost certain)
    severity:    1 (negligible) → 5 (critical)
    """
    score = probability * severity
    if score <= 4:
        level = "low"
    elif score <= 12:
        level = "medium"
    else:
        level = "high"
    return float(score), level


# ---------------------------------------------------------------------------
# Mitigation suggestions keyed by (hazard_type, keyword)
# These are shown as editable defaults in the Wizard Step 3
# ---------------------------------------------------------------------------

MITIGATION_SUGGESTIONS: dict[str, str] = {
    # Chemical
    "chemical_allergen":    "Utilizar tintes y acabados con certificación OEKO-TEX Std 100 o equivalente. Solicitar declaración de conformidad REACH al proveedor y conservarla en el expediente.",
    "chemical_pesticide":   "Exigir algodón orgánico certificado (GOTS o equivalente) y conservar el certificado del proveedor en el expediente técnico.",
    "chemical_voc":         "Asegurar curado completo del material antes del embalaje. Ventilar el espacio de trabajo. Solicitar FDS (Ficha de Datos de Seguridad) al proveedor.",
    "chemical_nickel":      "Solicitar al proveedor certificado EN 1811 de liberación de níquel ≤ 0,2 µg/cm²/semana. Rechazar lotes sin certificado.",
    "chemical_epoxy":       "Asegurar tiempo de curado completo según las instrucciones del fabricante de la resina. Realizar test organoléptico por lote.",
    "chemical_lead":        "Usar exclusivamente esmaltes sin plomo certificados para uso alimentario. Test de migración según EN 1388.",
    "chemical_resin":       "Garantizar curado completo de la resina antes del embalaje. Incluir Test de dureza Shore como control de calidad por lote.",
    "chemical_chromium":    "Solicitar certificado de ausencia de cromo VI (≤3 mg/kg). Conservar en el expediente técnico.",
    # Thermal
    "thermal_fire":         "Incluir en la etiqueta instrucción de seguridad contra el fuego. Empaquetar con instrucciones de uso. Mantener alejado de materiales inflamables.",
    "thermal_candle":       "Etiquetar con las advertencias obligatorias para velas (EN 15493). Indicar distancia mínima 10 cm a objetos inflamables y tiempo máximo de quemado.",
    "thermal_melt":         "Advertir sobre temperatura máxima de uso. Incluir instrucción: 'No exponer a fuentes de calor directas'.",
    # Physical
    "physical_choking":     "Añadir advertencia de edad mínima (≥3 años) en la etiqueta. Aseguramiento mecánico de todos los accesorios (prueba de tracción según EN 71-1 si aplica).",
    "physical_splinter":    "Lijado completo de todas las superficies y aristas (grano ≥180). Inspección visual y táctil por lote. No comercializar piezas con defectos.",
    "physical_broken":      "Añadir advertencia: 'Desechar si el producto presenta grietas o roturas'. Verificar resistencia mecánica por muestra de lote.",
    # Mechanical
    "mechanical_splinter":  "Lijado completo de todas las superficies y cantos. Verificación visual y táctil por cada lote fabricado.",
    "mechanical_cut":       "Proteger bordes con acabado redondeado o protección. Incluir advertencia de manipulación con cuidado.",
}

# Map from (hazard_type, keyword_in_description) → suggestion key
_MITIGATION_CLASSIFIER: list[tuple[str, str, str]] = [
    # (hazard_type, keyword_in_description, suggestion_key)
    ("chemical", "alérgen",   "chemical_allergen"),
    ("chemical", "tinte",     "chemical_allergen"),
    ("chemical", "aprest",    "chemical_allergen"),
    ("chemical", "pesticida", "chemical_pesticide"),
    ("chemical", "cov",       "chemical_voc"),
    ("chemical", "barniz",    "chemical_voc"),
    ("chemical", "formald",   "chemical_voc"),
    ("chemical", "níquel",    "chemical_nickel"),
    ("chemical", "resina",    "chemical_epoxy"),
    ("chemical", "epoxi",     "chemical_epoxy"),
    ("chemical", "plomo",     "chemical_lead"),
    ("chemical", "cadmio",    "chemical_lead"),
    ("chemical", "esmalte",   "chemical_lead"),
    ("chemical", "cromo",     "chemical_chromium"),
    ("thermal",  "vela",      "thermal_candle"),
    ("thermal",  "cera",      "thermal_candle"),
    ("thermal",  "incendi",   "thermal_candle"),
    ("thermal",  "funde",     "thermal_melt"),
    ("thermal",  "fund",      "thermal_melt"),
    ("physical", "asfixia",   "physical_choking"),
    ("physical", "pieza",     "physical_choking"),
    ("physical", "astilla",   "physical_splinter"),
    ("physical", "rompe",     "physical_broken"),
    ("physical", "fragm",     "physical_broken"),
    ("mechanical","astilla",  "mechanical_splinter"),
    ("mechanical","borde",    "mechanical_cut"),
    ("mechanical","arista",   "mechanical_cut"),
]

# Warning texts to suggest for label/packaging, grouped by hazard type
HAZARD_WARNING_TEMPLATES: dict[str, list[str]] = {
    "chemical": [
        "⚠️ Puede causar reacciones alérgicas. Lavar antes del primer uso.",
        "Mantener fuera del alcance de los niños.",
    ],
    "thermal": [
        "⚠️ Mantener alejado del fuego y fuentes de calor directas.",
        "No exponer a temperaturas extremas.",
    ],
    "physical": [
        "⚠️ No apto para niños menores de 3 años. Riesgo de asfixia por piezas pequeñas.",
    ],
    "mechanical": [
        "⚠️ Inspeccionar antes de cada uso. Desechar si presenta grietas, astillas o bordes dañados.",
    ],
    "candle": [
        "⚠️ No dejar la vela encendida sin supervisión.",
        "⚠️ Mantener alejada de materiales inflamables. Distancia mínima: 10 cm.",
        "Apagar antes de que la cera llegue a 1 cm del fondo.",
        "Colocar sobre una superficie resistente al calor.",
    ],
}


def _get_mitigation_suggestion(hazard_type: str, hazard_description: str) -> str:
    """Returns the best mitigation suggestion for a given hazard."""
    desc_lower = hazard_description.lower()
    for h_type, keyword, suggestion_key in _MITIGATION_CLASSIFIER:
        if h_type == hazard_type and keyword in desc_lower:
            return MITIGATION_SUGGESTIONS.get(suggestion_key, "")
    # Fallback by hazard type only
    fallbacks = {
        "thermal":    MITIGATION_SUGGESTIONS["thermal_fire"],
        "chemical":   MITIGATION_SUGGESTIONS["chemical_allergen"],
        "physical":   MITIGATION_SUGGESTIONS["physical_choking"],
        "mechanical": MITIGATION_SUGGESTIONS["mechanical_splinter"],
    }
    return fallbacks.get(hazard_type, "Documentar la medida de control adoptada y registrarla en el expediente técnico.")


# ---------------------------------------------------------------------------
# Material → Risk Suggestions
# ---------------------------------------------------------------------------

MATERIAL_RISK_MAP: dict[str, list[dict]] = {

    # ===== TEXTILES =====
    "lana": [
        {"hazard_type": "chemical", "hazard_description": "Posibles alérgenos en tintes o aprestos de la lana.", "probability": 2, "severity": 2},
        {"hazard_type": "thermal", "hazard_description": "La lana es inflamable si está en contacto con llamas directas.", "probability": 2, "severity": 3},
    ],
    "algodón": [
        {"hazard_type": "chemical", "hazard_description": "Posibles residuos de pesticidas si no es algodón orgánico certificado.", "probability": 2, "severity": 2},
        {"hazard_type": "thermal", "hazard_description": "El algodón puede arder si entra en contacto con llamas.", "probability": 2, "severity": 3},
    ],
    "poliéster": [
        {"hazard_type": "thermal", "hazard_description": "El poliéster funde y puede causar quemaduras graves en contacto con llamas.", "probability": 2, "severity": 4},
        {"hazard_type": "chemical", "hazard_description": "Posibles sustancias químicas REACH en acabados sintéticos.", "probability": 1, "severity": 3},
    ],
    "seda": [
        {"hazard_type": "chemical", "hazard_description": "Posibles alérgenos en tintes o aprestos de la seda.", "probability": 2, "severity": 2},
        {"hazard_type": "thermal", "hazard_description": "La seda es inflamable y puede arder rápidamente.", "probability": 2, "severity": 3},
    ],
    "lino": [
        {"hazard_type": "chemical", "hazard_description": "Posibles alérgenos en tintes o tratamientos de acabado del lino.", "probability": 2, "severity": 2},
        {"hazard_type": "thermal", "hazard_description": "El lino es inflamable. Mantener alejado de llamas.", "probability": 2, "severity": 3},
    ],
    "acrílico": [
        {"hazard_type": "thermal", "hazard_description": "Las fibras acrílicas funden en contacto con calor/llamas y pueden causar quemaduras.", "probability": 2, "severity": 4},
        {"hazard_type": "chemical", "hazard_description": "Posibles residuos de acrilonitrilo. Verificar conformidad REACH.", "probability": 1, "severity": 3},
    ],
    "acrilico": [
        {"hazard_type": "thermal", "hazard_description": "Las fibras acrílicas funden en contacto con calor/llamas y pueden causar quemaduras.", "probability": 2, "severity": 4},
        {"hazard_type": "chemical", "hazard_description": "Posibles residuos de acrilonitrilo. Verificar conformidad REACH.", "probability": 1, "severity": 3},
    ],
    "viscosa": [
        {"hazard_type": "chemical", "hazard_description": "Posibles trazas de disulfuro de carbono del proceso de fabricación. Solicitar FDS al proveedor.", "probability": 1, "severity": 2},
        {"hazard_type": "thermal", "hazard_description": "La viscosa es inflamable, similar al algodón.", "probability": 2, "severity": 3},
    ],
    "rayón": [
        {"hazard_type": "chemical", "hazard_description": "Posibles trazas de disulfuro de carbono del proceso de fabricación.", "probability": 1, "severity": 2},
        {"hazard_type": "thermal", "hazard_description": "El rayón es inflamable, similar al algodón.", "probability": 2, "severity": 3},
    ],
    "elastano": [
        {"hazard_type": "chemical", "hazard_description": "Posibles residuos de isocianatos o colorantes reactivos. Verificar conformidad REACH.", "probability": 1, "severity": 3},
    ],
    "spandex": [
        {"hazard_type": "chemical", "hazard_description": "Posibles residuos de isocianatos o colorantes reactivos. Verificar conformidad REACH.", "probability": 1, "severity": 3},
    ],
    "lycra": [
        {"hazard_type": "chemical", "hazard_description": "Posibles residuos de isocianatos. Verificar conformidad REACH.", "probability": 1, "severity": 3},
    ],
    "bambú": [
        {"hazard_type": "chemical", "hazard_description": "Si es fibra de bambú textil (viscosa de bambú), pueden quedar trazas del proceso químico.", "probability": 1, "severity": 2},
    ],
    "poliamida": [
        {"hazard_type": "chemical", "hazard_description": "Posibles sustancias REACH en acabados. Solicitar declaración de conformidad.", "probability": 1, "severity": 2},
    ],
    "nylon": [
        {"hazard_type": "chemical", "hazard_description": "Posibles sustancias REACH en acabados de nylon.", "probability": 1, "severity": 2},
        {"hazard_type": "thermal", "hazard_description": "El nylon funde a altas temperaturas, riesgo de quemaduras.", "probability": 1, "severity": 3},
    ],
    "fleece": [
        {"hazard_type": "chemical", "hazard_description": "Material sintético (poliéster). Posibles sustancias REACH en acabados.", "probability": 1, "severity": 2},
        {"hazard_type": "thermal", "hazard_description": "Inflamable. Puede fundir en contacto con fuentes de calor.", "probability": 2, "severity": 3},
    ],
    "fieltro": [
        {"hazard_type": "chemical", "hazard_description": "Posibles alérgenos en colorantes o tintes del fieltro.", "probability": 2, "severity": 2},
    ],
    "terciopelo": [
        {"hazard_type": "chemical", "hazard_description": "Posibles alérgenos en tintes o aprestos del terciopelo.", "probability": 2, "severity": 2},
        {"hazard_type": "thermal", "hazard_description": "El terciopelo puede arder en contacto con fuentes de calor.", "probability": 2, "severity": 3},
    ],
    "cuero": [
        {"hazard_type": "chemical", "hazard_description": "Los curtientes de cromo pueden ser alergénicos (cromo VI). Solicitar certificado libre de cromo VI.", "probability": 3, "severity": 3},
        {"hazard_type": "thermal", "hazard_description": "El cuero es inflamable y puede liberar humos tóxicos al arder.", "probability": 2, "severity": 3},
    ],
    "piel": [
        {"hazard_type": "chemical", "hazard_description": "Los curtientes de cromo pueden ser alergénicos (cromo VI). Solicitar certificado.", "probability": 3, "severity": 3},
    ],
    "ante": [
        {"hazard_type": "chemical", "hazard_description": "Los curtientes y tintes del ante pueden contener cromo o alérgenos. Solicitar certificado.", "probability": 2, "severity": 3},
    ],
    "encaje": [
        {"hazard_type": "chemical", "hazard_description": "Posibles alérgenos en tintes o blanqueadores del encaje.", "probability": 2, "severity": 2},
    ],
    "hilo": [
        {"hazard_type": "chemical", "hazard_description": "Posibles alérgenos en tintes del hilo de coser o bordar.", "probability": 1, "severity": 2},
    ],
    "cordón": [
        {"hazard_type": "physical", "hazard_description": "Los cordones en capuchas para niños suponen riesgo de estrangulamiento (ISO 13688).", "probability": 3, "severity": 5},
    ],
    "cremallera": [
        {"hazard_type": "chemical", "hazard_description": "Las cremalleras de metal pueden contener níquel. Verificar límites EN 1811.", "probability": 2, "severity": 3},
        {"hazard_type": "physical", "hazard_description": "Bordes y dientes de cremallera pueden causar pequeños cortes.", "probability": 2, "severity": 2},
    ],
    "velcro": [
        {"hazard_type": "physical", "hazard_description": "La cara abrojo del velcro puede generar pequeños araños en la piel.", "probability": 2, "severity": 1},
    ],
    "elástico": [
        {"hazard_type": "chemical", "hazard_description": "Posibles alérgenos al látex en elásticos de goma natural. Indicar si contiene látex.", "probability": 2, "severity": 3},
    ],

    # ===== MADERA =====
    "madera": [
        {"hazard_type": "mechanical", "hazard_description": "Riesgo de astillas o aristas cortantes si no está correctamente lijada.", "probability": 3, "severity": 2},
        {"hazard_type": "chemical", "hazard_description": "Los barnices y pinturas pueden contener COVs o metales pesados.", "probability": 2, "severity": 3},
    ],
    "pino": [
        {"hazard_type": "mechanical", "hazard_description": "La madera de pino puede generar astillas si no está correctamente lijada.", "probability": 3, "severity": 2},
        {"hazard_type": "chemical", "hazard_description": "Resinas naturales del pino pueden ser irritantes. Los barnices pueden contener COVs.", "probability": 2, "severity": 2},
    ],
    "roble": [
        {"hazard_type": "mechanical", "hazard_description": "Bordes y aristas afilados si no están correctamente acabados.", "probability": 2, "severity": 2},
        {"hazard_type": "chemical", "hazard_description": "El polvo de roble es alergénico y potencialmente cancerígeno (madera dura). Riesgo solo en fabricación.", "probability": 1, "severity": 3},
    ],
    "mdf": [
        {"hazard_type": "chemical", "hazard_description": "El MDF puede emitir formaldehído (COV) del adhesivo urea-formaldehyde. Verificar clase E1.", "probability": 3, "severity": 3},
        {"hazard_type": "mechanical", "hazard_description": "Bordes del MDF pueden ser afilados si no están acabados.", "probability": 2, "severity": 2},
    ],
    "contrachapado": [
        {"hazard_type": "chemical", "hazard_description": "Puede emitir formaldehído del adhesivo. Exigir certificación E1.", "probability": 2, "severity": 3},
    ],
    "barniz": [
        {"hazard_type": "chemical", "hazard_description": "Los barnices contienen COVs. Asegurar ventilación y curado completo antes de entregar el producto.", "probability": 3, "severity": 2},
    ],
    "lacado": [
        {"hazard_type": "chemical", "hazard_description": "Las lacas pueden contener COVs, metales pesados o isocianatos. Solicitar FDS.", "probability": 2, "severity": 3},
    ],
    "pintura": [
        {"hazard_type": "chemical", "hazard_description": "Algunas pinturas pueden contener plomo, cadmio u otros metales pesados. Verificar conformidad REACH.", "probability": 2, "severity": 4},
    ],
    "corcho": [
        {"hazard_type": "chemical", "hazard_description": "Posibles trazas de TCA o pesticidas en corcho no certificado. Pedir certificado FSC.", "probability": 1, "severity": 2},
    ],

    # ===== VELAS / AROMATERAPIA =====
    "cera": [
        {"hazard_type": "thermal", "hazard_description": "Riesgo de incendio si la vela se deja desatendida o cerca de materiales inflamables.", "probability": 4, "severity": 5},
        {"hazard_type": "chemical", "hazard_description": "La cera de parafina puede emitir COVs al quemarse.", "probability": 3, "severity": 2},
    ],
    "parafina": [
        {"hazard_type": "thermal", "hazard_description": "Alta inflamabilidad. Riesgo de ignición espontánea a altas temperaturas.", "probability": 3, "severity": 5},
    ],
    "soja": [
        {"hazard_type": "thermal", "hazard_description": "La cera de soja es inflamable. Riesgo de incendio si la vela se deja desatendida.", "probability": 4, "severity": 5},
        {"hazard_type": "chemical", "hazard_description": "Los aceites esenciales añadidos pueden ser alérgenos. Indicar composición en etiqueta.", "probability": 2, "severity": 2},
    ],
    "aceite esencial": [
        {"hazard_type": "chemical", "hazard_description": "Los aceites esenciales pueden causar reacciones alérgicas o irritación. Incluir alérgenos IFRA en etiqueta.", "probability": 3, "severity": 3},
        {"hazard_type": "thermal", "hazard_description": "Los aceites esenciales son inflamables. Mantener alejados de llamas.", "probability": 3, "severity": 4},
    ],
    "fragancia": [
        {"hazard_type": "chemical", "hazard_description": "Las fragancias pueden contener alérgenos regulados por la UE. Declarar los 26 alérgenos obligatorios en etiqueta.", "probability": 3, "severity": 3},
    ],
    "mecha": [
        {"hazard_type": "chemical", "hazard_description": "Las mechas con núcleo metálico pueden emitir metales al quemarse. Usar solo mechas de algodón certificadas.", "probability": 2, "severity": 3},
        {"hazard_type": "thermal", "hazard_description": "La mecha es el elemento de ignición. Mantener recortada a 5mm para evitar llama excesiva.", "probability": 3, "severity": 4},
    ],

    # ===== METALES / JOYERÍA =====
    "plata": [
        {"hazard_type": "chemical", "hazard_description": "Posible contaminación con níquel u otros metales en aleaciones. Alérgeno confirmado por REACH.", "probability": 2, "severity": 3},
    ],
    "cobre": [
        {"hazard_type": "chemical", "hazard_description": "Oxidación del cobre puede generar verdín (carbonato de cobre), irritante cutáneo.", "probability": 2, "severity": 2},
    ],
    "oro": [
        {"hazard_type": "chemical", "hazard_description": "El oro de baja pureza puede contener níquel u otros metales alérgenos. Verificar quilates y certificar aleación.", "probability": 2, "severity": 3},
    ],
    "bronce": [
        {"hazard_type": "chemical", "hazard_description": "El bronce contiene cobre y estaño. Posible verdinización (carbonato de cobre), irritante cutáneo.", "probability": 2, "severity": 2},
    ],
    "latón": [
        {"hazard_type": "chemical", "hazard_description": "El latón contiene zinc y cobre. Puede liberar zinc en contacto prolongado con piel. Verificar REACH.", "probability": 2, "severity": 2},
    ],
    "aluminio": [
        {"hazard_type": "mechanical", "hazard_description": "Bordes y virutas de aluminio pueden ser cortantes.", "probability": 2, "severity": 2},
        {"hazard_type": "chemical", "hazard_description": "Anodizados o recubrimientos pueden contener cromo. Verificar proceso.", "probability": 1, "severity": 2},
    ],
    "acero": [
        {"hazard_type": "chemical", "hazard_description": "El acero inoxidable en joyería puede contener níquel. Verificar límites EN 1811 (≤0.2 µg/cm²/sem).", "probability": 2, "severity": 3},
        {"hazard_type": "mechanical", "hazard_description": "Bordes o cierres metálicos pueden causar pequeños cortes.", "probability": 1, "severity": 2},
    ],
    "bisutería": [
        {"hazard_type": "chemical", "hazard_description": "La bisutería de bajo coste frecuentemente supera los límites de níquel y plomo de REACH. Exigir test EN 1811.", "probability": 4, "severity": 3},
        {"hazard_type": "physical", "hazard_description": "Piezas pequeñas (dijes, cierres) representan riesgo de asfixia para menores de 3 años.", "probability": 3, "severity": 5},
    ],
    "esmalte": [
        {"hazard_type": "chemical", "hazard_description": "Los esmaltes pueden contener plomo o cadmio. Para uso alimentario: test de migración EN 1388.", "probability": 2, "severity": 4},
    ],
    "nácar": [
        {"hazard_type": "physical", "hazard_description": "El nácar puede romperse en fragmentos afilados.", "probability": 2, "severity": 3},
    ],
    "perla": [
        {"hazard_type": "physical", "hazard_description": "Las perlas de imitación pueden desprender la capa exterior. Riesgo de asfixia en niños.", "probability": 2, "severity": 3},
    ],
    "cristal": [
        {"hazard_type": "physical", "hazard_description": "El cristal puede romperse generando fragmentos cortantes.", "probability": 2, "severity": 4},
        {"hazard_type": "chemical", "hazard_description": "El cristal al plomo puede liberar plomo en contacto con alimentos.", "probability": 2, "severity": 4},
    ],

    # ===== RESINA / CERÁMICA / ARCILLA =====
    "resina": [
        {"hazard_type": "chemical", "hazard_description": "La resina epóxica sin curar es irritante/alérgena. Asegurar curado completo.", "probability": 3, "severity": 3},
        {"hazard_type": "physical", "hazard_description": "Las piezas de resina pueden romperse en fragmentos afilados.", "probability": 2, "severity": 3},
    ],
    "arcilla": [
        {"hazard_type": "mechanical", "hazard_description": "Bordes afilados en piezas rotas. Riesgo de astillas.", "probability": 2, "severity": 3},
        {"hazard_type": "chemical", "hazard_description": "Los esmaltes no alimentarios pueden contener plomo o cadmio.", "probability": 2, "severity": 4},
    ],
    "porcelana": [
        {"hazard_type": "mechanical", "hazard_description": "La porcelana puede romperse generando fragmentos muy afilados.", "probability": 2, "severity": 4},
        {"hazard_type": "chemical", "hazard_description": "Los esmaltes decorativos pueden contener plomo o cadmio. Test de migración EN 1388 para uso alimentario.", "probability": 2, "severity": 4},
    ],
    "gres": [
        {"hazard_type": "mechanical", "hazard_description": "El gres puede romperse generando bordes afilados.", "probability": 2, "severity": 3},
        {"hazard_type": "chemical", "hazard_description": "Los esmaltes pueden contener plomo. Test de migración para uso alimentario.", "probability": 2, "severity": 4},
    ],
    "terracota": [
        {"hazard_type": "chemical", "hazard_description": "La terracota sin esmaltar puede acumular bacterias. No apta para alimentos sin barniz alimentario.", "probability": 2, "severity": 3},
        {"hazard_type": "mechanical", "hazard_description": "Riesgo de rotura y bordes afilados.", "probability": 2, "severity": 3},
    ],
    "yeso": [
        {"hazard_type": "chemical", "hazard_description": "El yeso en polvo puede irritar vías respiratorias. Verificar pigmentos en piezas pintadas.", "probability": 2, "severity": 2},
        {"hazard_type": "physical", "hazard_description": "Las piezas de yeso son frágiles y pueden romperse en fragmentos.", "probability": 3, "severity": 3},
    ],
    "escayola": [
        {"hazard_type": "chemical", "hazard_description": "El polvo de escayola es irritante respiratorio. Las piezas acabadas son generalmente seguras.", "probability": 2, "severity": 2},
        {"hazard_type": "physical", "hazard_description": "Puede romperse en fragmentos al caer.", "probability": 3, "severity": 3},
    ],

    # ===== COSMÉTICA / HIGIENE =====
    "jabón": [
        {"hazard_type": "chemical", "hazard_description": "El jabón artesanal puede contener NaOH residual si no está correctamente curado. Verificar pH.", "probability": 2, "severity": 3},
        {"hazard_type": "chemical", "hazard_description": "Los aceites esenciales o colorantes añadidos pueden ser alérgenos. Declarar en etiqueta.", "probability": 3, "severity": 2},
    ],
    "naoh": [
        {"hazard_type": "chemical", "hazard_description": "El hidróxido de sodio es corrosivo. Solo es seguro si la saponificación está completa. Verificar pH.", "probability": 3, "severity": 4},
    ],
    "sosa": [
        {"hazard_type": "chemical", "hazard_description": "La sosa cáustica es corrosiva. Solo es segura si la saponificación está completa.", "probability": 3, "severity": 4},
    ],
    "aceite vegetal": [
        {"hazard_type": "chemical", "hazard_description": "Los aceites vegetales pueden volverse rancios. Indicar fecha de caducidad y conservación.", "probability": 1, "severity": 2},
    ],
    "manteca": [
        {"hazard_type": "chemical", "hazard_description": "Mantecas naturales (karité, cacao) pueden ser alérgenas. Declarar en etiqueta INCI.", "probability": 2, "severity": 2},
    ],
    "karité": [
        {"hazard_type": "chemical", "hazard_description": "La manteca de karité puede causar reacciones alérgicas. Declarar en etiqueta INCI.", "probability": 2, "severity": 2},
    ],
    "ácido cítrico": [
        {"hazard_type": "chemical", "hazard_description": "El ácido cítrico puro es irritante ocular y cutáneo. En concentraciones de uso cosmético el riesgo es bajo.", "probability": 1, "severity": 2},
    ],
    "conservante": [
        {"hazard_type": "chemical", "hazard_description": "Algunos conservantes (parabenos, MIT) pueden ser alérgenos o estar restringidos. Verificar lista positiva del Reglamento Cosmético.", "probability": 2, "severity": 3},
    ],

    # ===== ACCESORIOS PEQUEÑOS =====
    "botones": [
        {"hazard_type": "physical", "hazard_description": "Piezas pequeñas. Riesgo de asfixia para niños menores de 3 años.", "probability": 3, "severity": 5},
    ],
    "relleno": [
        {"hazard_type": "physical", "hazard_description": "El relleno suelto (polyester fiberfill) puede causar asfixia si el producto se rompe.", "probability": 2, "severity": 4},
    ],
    "alambre": [
        {"hazard_type": "mechanical", "hazard_description": "Los extremos del alambre son muy punzantes y cortantes. Asegurar que todos los extremos estén protegidos.", "probability": 4, "severity": 3},
    ],
    "glitter": [
        {"hazard_type": "physical", "hazard_description": "La purpurina puede desprenderse e irritar ojos y mucosas. No apta para menores de 3 años.", "probability": 3, "severity": 3},
        {"hazard_type": "chemical", "hazard_description": "El glitter metálico puede contener trazas de metales pesados.", "probability": 2, "severity": 3},
    ],
    "purpurina": [
        {"hazard_type": "physical", "hazard_description": "La purpurina puede desprenderse e irritar ojos y mucosas. No apta para menores de 3 años.", "probability": 3, "severity": 3},
    ],

    # ===== TINTES =====
    "tinte": [
        {"hazard_type": "chemical", "hazard_description": "Los tintes pueden contener colorantes azo prohibidos por REACH Anexo XVII.", "probability": 2, "severity": 3},
    ],

    # ===== PLÁSTICOS =====
    "plástico": [
        {"hazard_type": "chemical", "hazard_description": "Algunos plásticos contienen ftalatos, BPA u otras sustancias SVHC. Verificar conformidad REACH.", "probability": 2, "severity": 3},
    ],
    "pvc": [
        {"hazard_type": "chemical", "hazard_description": "El PVC puede contener ftalatos (DEHP, DBP…) restringidos por REACH. No apto para productos infantiles sin certificación.", "probability": 3, "severity": 4},
    ],
    "abs": [
        {"hazard_type": "chemical", "hazard_description": "El ABS puede contener acrilonitrilo residual. Para contacto alimentario: no recomendado sin certificación.", "probability": 2, "severity": 3},
        {"hazard_type": "thermal", "hazard_description": "El ABS puede emitir humos tóxicos al quemarse.", "probability": 2, "severity": 3},
    ],

    # ===== PAPEL / CARTÓN =====
    "papel": [
        {"hazard_type": "chemical", "hazard_description": "Tintas y pegamentos pueden contener VOCs. Para productos infantiles, verificar ausencia de sustancias SVHC.", "probability": 1, "severity": 2},
    ],
    "cartón": [
        {"hazard_type": "chemical", "hazard_description": "Los cartones reciclados pueden contener hidrocarburos (MOAH/MOSH). Para contacto alimentario: usar barrera funcional.", "probability": 2, "severity": 3},
    ],
    "pegamento": [
        {"hazard_type": "chemical", "hazard_description": "Los pegamentos pueden contener disolventes orgánicos (COVs) o isocianatos. Asegurar curado completo.", "probability": 2, "severity": 3},
    ],

    # ===== OTROS =====
    "vidrio": [
        {"hazard_type": "physical", "hazard_description": "El vidrio puede romperse generando fragmentos muy cortantes.", "probability": 2, "severity": 5},
        {"hazard_type": "thermal", "hazard_description": "El vidrio expuesto a cambios bruscos de temperatura puede romperse (choque térmico).", "probability": 2, "severity": 4},
    ],
}


# ---------------------------------------------------------------------------
# Category → Mandatory Checks
# ---------------------------------------------------------------------------

CATEGORY_REQUIRED_CHECKS: dict[str, list[str]] = {
    "textile": [
        "Verificar que los tintes cumplen REACH (sin colorantes azo prohibidos).",
        "Comprobar que no hay cordones en capuchas para niños (ISO 13688).",
        "Incluir instrucciones de lavado y mantenimiento.",
    ],
    "toy": [
        "⚠️ Los juguetes requieren Marcado CE y cumplir la Directiva 2009/48/CE.",
        "Advertencia de piezas pequeñas (asfixia) si aplica.",
        "Test de inflamabilidad requerido.",
        "Documentar límites de migración de metales pesados en pinturas.",
    ],
    "candle": [
        "Etiqueta obligatoria: 'No dejar la vela encendida sin supervisión'.",
        "Indicar distancia mínima de seguridad a materiales inflamables.",
        "Especificar tiempo máximo de quemado.",
        "Incluir información sobre el recipiente (si es vidrio, riesgo de rotura).",
    ],
    "cosmetic": [
        "⚠️ Los cosméticos requieren notificación CPNP adicional.",
        "Listado INCI de ingredientes obligatorio.",
        "Test de seguridad cosmetica (Cosmetologist Safety Assessment).",
        "Advertencias de alérgenos si contiene fragancias.",
    ],
    "jewellery": [
        "Verificar límites de níquel (EN 1811). Límite: 0.2 µg/cm²/semana.",
        "Si contiene piezas pequeñas: advertencia para menores de 3 años.",
        "Documentar origen y certificación de metales preciosos si aplica.",
    ],
    "ceramic": [
        "Para uso alimentario: test de migración de plomo y cadmio (EN 1388).",
        "Indicar si es apto o no para microondas / lavavajillas.",
        "Advertir sobre riesgo de rotura.",
    ],
    "wood": [
        "Documentar el acabado superficial (barniz, aceite, pintura) y su certificación.",
        "Lijar todos los cantos y aristas. Incluir en análisis de riesgos.",
        "Para productos en contacto con alimentos: usar solo aceites alimentarios.",
    ],
    "paper": [
        "Indicar si contiene tintas o pegamentos con componentes REACH.",
        "Para niños: verificar ausencia de aristas cortantes.",
    ],
    "other": [
        "Realizar análisis de riesgos general.",
        "Consultar normativa específica del sector si existe.",
    ],
}


# ---------------------------------------------------------------------------
# Main interface functions
# ---------------------------------------------------------------------------

def analyze_materials(material_names: list[str]) -> list[dict]:
    """
    Receives a list of material names.
    Returns risk suggestions WITH pre-filled mitigation suggestions.
    """
    suggestions = []
    seen = set()  # avoid exact duplicates
    for material in material_names:
        key = material.lower().strip()
        for map_key, risks in MATERIAL_RISK_MAP.items():
            if map_key in key:
                for risk in risks:
                    dedup_key = (risk["hazard_type"], risk["hazard_description"])
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)
                    score, level = calculate_risk_level(risk["probability"], risk["severity"])
                    mitigation_suggestion = _get_mitigation_suggestion(
                        risk["hazard_type"], risk["hazard_description"]
                    )
                    suggestions.append({
                        **risk,
                        "risk_score": score,
                        "risk_level": level,
                        "source_material": material,
                        "mitigation_suggestion": mitigation_suggestion,
                    })
    return suggestions


def suggest_warnings(risks: list[dict], category: str) -> list[dict]:
    """
    Generates suggested safety warnings from detected risks.
    Returns a list of {text, accepted, source} dicts for the frontend checkbox UI.
    
    Each warning has:
      - text: the warning text to display on the label
      - source: "risk" | "category" — why it was included
      - accepted: True (pre-checked, user can uncheck)
    """
    warnings = []
    seen_texts = set()

    def add(text: str, source: str):
        if text not in seen_texts:
            seen_texts.add(text)
            warnings.append({"text": text, "source": source, "accepted": True})

    # From risk types
    seen_types = set()
    for risk in risks:
        h_type = risk.get("hazard_type", "")
        desc = risk.get("hazard_description", "").lower()
        level = risk.get("risk_level", "low")

        # Special case: candle risks → candle warnings
        if "vela" in desc or "incendi" in desc or "cera" in desc:
            for w in HAZARD_WARNING_TEMPLATES.get("candle", []):
                add(w, "riesgo")
        elif h_type not in seen_types and h_type in HAZARD_WARNING_TEMPLATES:
            for w in HAZARD_WARNING_TEMPLATES[h_type]:
                add(w, "riesgo")
            seen_types.add(h_type)

    # Category-specific extra warnings
    CATEGORY_EXTRA_WARNINGS = {
        "textile": ["Lavar a mano. No usar secadora.", "Ver instrucciones de lavado en la etiqueta interior."],
        "candle":  ["⚠️ No dejar la vela encendida sin supervisión.", "Mantener fuera del alcance de los niños y animales."],
        "toy":     ["⚠️ No apto para menores de 3 años.", "Supervisión adulta recomendada."],
        "cosmetic":["Realizar test de alergia 24h antes del primer uso.", "Conservar en lugar fresco y seco. No exponer a la luz solar directa."],
        "jewellery":["Limpiar con paño suave. Evitar contacto con agua y productos químicos."],
        "ceramic": ["⚠️ Riesgo de rotura. Desechar en caso de grietas.", "No apto para microondas (salvo indicación contraria)."],
        "wood":    ["Proteger del agua y la humedad. Aceitar periódicamente para conservar el acabado."],
    }
    for w in CATEGORY_EXTRA_WARNINGS.get(category, []):
        add(w, "categoría")

    return warnings


def get_category_checks(category: str) -> list[str]:
    """Returns the mandatory compliance checks for a product category."""
    return CATEGORY_REQUIRED_CHECKS.get(category, CATEGORY_REQUIRED_CHECKS["other"])
