"""
POST /api/risk/calculate — Risk calculation endpoint
Development endpoint that exposes the deterministic risk engine.
"""

from fastapi import APIRouter
from app.schemas.risk import RiskInput, RiskAssessment, RiskBreakdown, RiskFactor
from app.services.risk_service import calculate_risk
from app.api.errors import APIError

router = APIRouter()


@router.post(
    "/calculate",
    response_model=RiskAssessment,
    summary="Calculate risk score (development endpoint)",
    description=(
        "Accepts four normalized risk factors (0–1) and returns an explainable "
        "risk assessment including risk score (0–10), priority category, and a "
        "per-factor breakdown. "
        "**Disclaimer:** The weighting and priority thresholds are prototype design "
        "choices for this hackathon and are NOT an official disaster-risk standard."
    ),
    tags=["Risk Engine"],
)
def calculate_risk_endpoint(risk_input: RiskInput) -> RiskAssessment:
    try:
        result = calculate_risk(
            flood_severity=risk_input.flood_severity,
            building_exposure=risk_input.building_exposure,
            road_disruption=risk_input.road_disruption,
            critical_facility_exposure=risk_input.critical_facility_exposure,
        )
    except ValueError as e:
        raise APIError(str(e), status_code=422)

    bd = result["breakdown"]
    return RiskAssessment(
        normalized_risk=result["normalized_risk"],
        risk_score=result["risk_score"],
        priority=result["priority"],
        weights=result["weights"],
        breakdown=RiskBreakdown(
            flood_severity=RiskFactor(**bd["flood_severity"]),
            building_exposure=RiskFactor(**bd["building_exposure"]),
            road_disruption=RiskFactor(**bd["road_disruption"]),
            critical_facility_exposure=RiskFactor(**bd["critical_facility_exposure"]),
        ),
    )
