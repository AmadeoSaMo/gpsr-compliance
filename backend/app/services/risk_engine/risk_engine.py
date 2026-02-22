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
    ("chemical", "níquel",    "chemical_nickel"),
    ("chemical", "resina",    "chemical_epoxy"),
    ("chemical", "epoxi",     "chemical_epoxy"),
    ("chemical", "plomo",     "chemical_lead"),
    ("chemical", "cadmio",    "chemical_lead"),
    ("chemical", "esmalte",   "chemical_lead"),
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
    # TEXTILES
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

    # MADERA
    "madera": [
        {"hazard_type": "mechanical", "hazard_description": "Riesgo de astillas o aristas cortantes si no está correctamente lijada.", "probability": 3, "severity": 2},
        {"hazard_type": "chemical", "hazard_description": "Los barnices y pinturas pueden contener COVs o metales pesados.", "probability": 2, "severity": 3},
    ],

    # VELAS / CERA
    "cera": [
        {"hazard_type": "thermal", "hazard_description": "Riesgo de incendio si la vela se deja desatendida o cerca de materiales inflamables.", "probability": 4, "severity": 5},
        {"hazard_type": "chemical", "hazard_description": "La cera de parafina puede emitir COVs al quemarse.", "probability": 3, "severity": 2},
    ],
    "parafina": [
        {"hazard_type": "thermal", "hazard_description": "Alta inflamabilidad. Riesgo de ignición espontánea a altas temperaturas.", "probability": 3, "severity": 5},
    ],

    # METALES
    "plata": [
        {"hazard_type": "chemical", "hazard_description": "Posible contaminación con níquel u otros metales en aleaciones. Alérgeno confirmado por REACH.", "probability": 2, "severity": 3},
    ],
    "cobre": [
        {"hazard_type": "chemical", "hazard_description": "Oxidación del cobre puede generar verdín (carbonato de cobre), irritante cutáneo.", "probability": 2, "severity": 2},
    ],
    "resina": [
        {"hazard_type": "chemical", "hazard_description": "La resina epóxica sin curar es irritante/alérgena. Asegurar curado completo.", "probability": 3, "severity": 3},
        {"hazard_type": "physical", "hazard_description": "Las piezas de resina pueden romperse en fragmentos afilados.", "probability": 2, "severity": 3},
    ],

    # ARCILLA / CERÁMICA
    "arcilla": [
        {"hazard_type": "mechanical", "hazard_description": "Bordes afilados en piezas rotas. Riesgo de astillas.", "probability": 2, "severity": 3},
        {"hazard_type": "chemical", "hazard_description": "Los esmaltes no alimentarios pueden contener plomo o cadmio.", "probability": 2, "severity": 4},
    ],

    # ACCESORIOS PEQUEÑOS
    "botones": [
        {"hazard_type": "physical", "hazard_description": "Piezas pequeñas. Riesgo de asfixia para niños menores de 3 años.", "probability": 3, "severity": 5},
    ],
    "relleno": [
        {"hazard_type": "physical", "hazard_description": "El relleno suelto (polyester fiberfill) puede causar asfixia si el producto se rompe.", "probability": 2, "severity": 4},
    ],

    # TINTES
    "tinte": [
        {"hazard_type": "chemical", "hazard_description": "Los tintes pueden contener colorantes azo prohibidos por REACH Anexo XVII.", "probability": 2, "severity": 3},
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
