"""
ASTRA-SHIELD Risk Engine
========================
Deterministic, explainable weighted risk scoring.

IMPORTANT DISCLAIMER:
The weights and priority thresholds defined here are prototype design choices
for the ASTRA-SHIELD hackathon demonstration. They are NOT an official
disaster-risk standard or government-approved methodology.

Architecture:
    ML / Geospatial services
            ↓
    Raw impact metrics
            ↓
    Normalization (upstream services: affected/total ratios)
            ↓
    Risk Engine  ← this module
            ↓
    RiskAssessment
"""

# ──────────────────────────────────────────────────────────────────────────────
# Prototype weights (must sum to 1.0)
# ──────────────────────────────────────────────────────────────────────────────
FLOOD_SEVERITY_WEIGHT: float = 0.35
BUILDING_EXPOSURE_WEIGHT: float = 0.25
ROAD_DISRUPTION_WEIGHT: float = 0.20
CRITICAL_FACILITY_WEIGHT: float = 0.20

# ──────────────────────────────────────────────────────────────────────────────
# Prototype priority thresholds (score out of 10)
# ──────────────────────────────────────────────────────────────────────────────
LOW_MAX: float = 3.0
MODERATE_MAX: float = 5.0
HIGH_MAX: float = 7.0
VERY_HIGH_MAX: float = 8.5


def _assign_priority(risk_score: float) -> str:
    """Map a 0-10 risk score to a priority category."""
    if risk_score < LOW_MAX:
        return "LOW"
    elif risk_score < MODERATE_MAX:
        return "MODERATE"
    elif risk_score < HIGH_MAX:
        return "HIGH"
    elif risk_score < VERY_HIGH_MAX:
        return "VERY_HIGH"
    else:
        return "CRITICAL"


def calculate_risk(
    flood_severity: float,
    building_exposure: float,
    road_disruption: float,
    critical_facility_exposure: float,
) -> dict:
    """
    Calculate a deterministic, explainable risk assessment.

    All inputs must be normalized values in [0, 1]:
      - flood_severity:              from ML model (0–1)
      - building_exposure:           affected_buildings / total_buildings
      - road_disruption:             affected_road_length / total_road_length
      - critical_facility_exposure:  affected_facilities / total_facilities

    Returns a dict matching the RiskAssessment schema.
    """
    # Validate inputs
    factors = {
        "flood_severity": flood_severity,
        "building_exposure": building_exposure,
        "road_disruption": road_disruption,
        "critical_facility_exposure": critical_facility_exposure,
    }
    for name, val in factors.items():
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"Risk factor '{name}' must be in [0, 1], got {val}")

    weights = {
        "flood_severity": FLOOD_SEVERITY_WEIGHT,
        "building_exposure": BUILDING_EXPOSURE_WEIGHT,
        "road_disruption": ROAD_DISRUPTION_WEIGHT,
        "critical_facility_exposure": CRITICAL_FACILITY_WEIGHT,
    }

    # Weighted sum → normalized risk (0–1)
    normalized_risk: float = sum(factors[k] * weights[k] for k in factors)

    # Scale to 0–10 and clamp to [0, 10]
    risk_score: float = max(0.0, min(10.0, round(normalized_risk * 10, 4)))

    priority: str = _assign_priority(risk_score)

    # Breakdown
    breakdown = {}
    for k in factors:
        contribution = round(factors[k] * weights[k], 6)
        breakdown[k] = {
            "value": factors[k],
            "weight": weights[k],
            "contribution": contribution,
        }

    return {
        "normalized_risk": round(normalized_risk, 6),
        "risk_score": risk_score,
        "priority": priority,
        "breakdown": breakdown,
        "weights": weights,
    }
