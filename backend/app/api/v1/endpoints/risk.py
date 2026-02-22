"""Risk Engine API — suggests hazards based on materials and category."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.risk_engine.risk_engine import (
    analyze_materials,
    get_category_checks,
    calculate_risk_level,
    suggest_warnings,
)

router = APIRouter()


class RiskAnalysisRequest(BaseModel):
    category: str
    materials: list[str]


class RiskScoreRequest(BaseModel):
    probability: int
    severity: int


@router.post("/analyze")
async def analyze_risk(payload: RiskAnalysisRequest):
    """
    Given a product category and list of materials, returns:
    - Pre-populated risk suggestions with mitigation_suggestion pre-filled
    - Mandatory category-specific compliance checks
    - Suggested safety warnings (pre-checked) for the label
    """
    suggestions = analyze_materials(payload.materials)
    checks = get_category_checks(payload.category)
    warnings = suggest_warnings(suggestions, payload.category)
    return {
        "risk_suggestions": suggestions,
        "mandatory_checks": checks,
        "suggested_warnings": warnings,
        "total_hazards_detected": len(suggestions),
    }


@router.post("/score")
async def calculate_score(payload: RiskScoreRequest):
    """Calculate the risk score and level for a given probability/severity."""
    score, level = calculate_risk_level(payload.probability, payload.severity)
    return {"risk_score": score, "risk_level": level}
