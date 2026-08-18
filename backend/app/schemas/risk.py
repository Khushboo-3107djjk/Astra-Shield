from pydantic import BaseModel, Field
from typing import Dict
from app.schemas.zone import ZonePriority


class RiskSummary(BaseModel):
    """Summary of the overall risk assessment."""
    overall_risk_score: float = Field(..., ge=0, le=10, description="Overall calculated risk score (0-10)")
    overall_priority: ZonePriority = Field(..., description="Overall priority level for emergency response")


# ──────────────────────────────────────────────────────────────────────────────
# Part 5A — Risk Engine schemas
# ──────────────────────────────────────────────────────────────────────────────

class RiskInput(BaseModel):
    """
    Normalized input values for the risk engine.

    All values must be in [0, 1].
    Upstream geospatial services are responsible for converting
    raw impact metrics (e.g. affected_buildings / total_buildings)
    into these normalized scores before passing them here.

    Note: The weighting model is a prototype design choice for this hackathon
    and is NOT an official disaster-risk standard.
    """
    flood_severity: float = Field(
        ..., ge=0, le=1,
        description="Normalized flood severity from the ML pipeline (0–1)"
    )
    building_exposure: float = Field(
        ..., ge=0, le=1,
        description="Fraction of buildings affected (affected / total), 0–1"
    )
    road_disruption: float = Field(
        ..., ge=0, le=1,
        description="Fraction of road length disrupted (affected_km / total_km), 0–1"
    )
    critical_facility_exposure: float = Field(
        ..., ge=0, le=1,
        description="Fraction of critical facilities potentially affected (affected / total), 0–1"
    )


class RiskFactor(BaseModel):
    """Contribution of a single factor to the overall risk score."""
    value: float = Field(..., ge=0, le=1, description="Normalized value of this factor")
    weight: float = Field(..., ge=0, le=1, description="Prototype weight assigned to this factor")
    contribution: float = Field(..., description="value × weight (pre-scaled contribution to normalized risk)")


class RiskBreakdown(BaseModel):
    """Explainable breakdown of risk contributions per factor."""
    flood_severity: RiskFactor
    building_exposure: RiskFactor
    road_disruption: RiskFactor
    critical_facility_exposure: RiskFactor


class RiskAssessment(BaseModel):
    """
    Complete explainable risk assessment result.

    DISCLAIMER: The weights and priority thresholds are prototype design
    choices for the ASTRA-SHIELD hackathon and are NOT an official
    disaster-risk standard.
    """
    normalized_risk: float = Field(
        ..., ge=0, le=1,
        description="Weighted sum of factor contributions (0–1)"
    )
    risk_score: float = Field(
        ..., ge=0, le=10,
        description="Scaled risk score (normalized_risk × 10), range 0–10"
    )
    priority: str = Field(
        ...,
        description="Priority category: LOW / MODERATE / HIGH / VERY_HIGH / CRITICAL"
    )
    breakdown: RiskBreakdown = Field(
        ...,
        description="Per-factor contribution explaining how the score was derived"
    )
    weights: Dict[str, float] = Field(
        ...,
        description="Prototype weights used for this calculation"
    )
