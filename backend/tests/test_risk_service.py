import pytest
from fastapi.testclient import TestClient
from app.services.risk_service import (
    calculate_risk,
    FLOOD_SEVERITY_WEIGHT,
    BUILDING_EXPOSURE_WEIGHT,
    ROAD_DISRUPTION_WEIGHT,
    CRITICAL_FACILITY_WEIGHT,
    LOW_MAX, MODERATE_MAX, HIGH_MAX, VERY_HIGH_MAX,
)
from app.main import app

client = TestClient(app)


# ── 1. Weight sum ──────────────────────────────────────────────────────────────
def test_weight_sum():
    total = (
        FLOOD_SEVERITY_WEIGHT
        + BUILDING_EXPOSURE_WEIGHT
        + ROAD_DISRUPTION_WEIGHT
        + CRITICAL_FACILITY_WEIGHT
    )
    assert total == pytest.approx(1.0, abs=1e-9)


# ── 2. All-zero input ──────────────────────────────────────────────────────────
def test_all_zero():
    r = calculate_risk(0, 0, 0, 0)
    assert r["risk_score"] == pytest.approx(0.0, abs=1e-6)
    assert r["priority"] == "LOW"


# ── 3. All-maximum input ───────────────────────────────────────────────────────
def test_all_maximum():
    r = calculate_risk(1, 1, 1, 1)
    assert r["risk_score"] == pytest.approx(10.0, abs=1e-6)
    assert r["priority"] == "CRITICAL"


# ── 4. Flood-only contribution ─────────────────────────────────────────────────
def test_flood_only():
    r = calculate_risk(1.0, 0.0, 0.0, 0.0)
    assert r["risk_score"] == pytest.approx(FLOOD_SEVERITY_WEIGHT * 10, abs=1e-4)


# ── 5. Building-only contribution ─────────────────────────────────────────────
def test_building_only():
    r = calculate_risk(0.0, 1.0, 0.0, 0.0)
    assert r["risk_score"] == pytest.approx(BUILDING_EXPOSURE_WEIGHT * 10, abs=1e-4)


# ── 6. Road-only contribution ──────────────────────────────────────────────────
def test_road_only():
    r = calculate_risk(0.0, 0.0, 1.0, 0.0)
    assert r["risk_score"] == pytest.approx(ROAD_DISRUPTION_WEIGHT * 10, abs=1e-4)


# ── 7. Critical-facility-only contribution ─────────────────────────────────────
def test_critical_facility_only():
    r = calculate_risk(0.0, 0.0, 0.0, 1.0)
    assert r["risk_score"] == pytest.approx(CRITICAL_FACILITY_WEIGHT * 10, abs=1e-4)


# ── 8. Mixed input ─────────────────────────────────────────────────────────────
def test_mixed_input():
    r = calculate_risk(
        flood_severity=0.82,
        building_exposure=0.60,
        road_disruption=0.35,
        critical_facility_exposure=0.50,
    )
    # Manual calculation:
    # 0.82*0.35 + 0.60*0.25 + 0.35*0.20 + 0.50*0.20
    # = 0.287 + 0.150 + 0.070 + 0.100 = 0.607 → 6.07
    assert r["risk_score"] == pytest.approx(6.07, abs=0.001)
    assert r["priority"] == "HIGH"


# ── 9. Contribution sum ────────────────────────────────────────────────────────
def test_contribution_sum():
    r = calculate_risk(0.82, 0.60, 0.35, 0.50)
    bd = r["breakdown"]
    total_contribution = sum(bd[k]["contribution"] for k in bd)
    assert total_contribution == pytest.approx(r["normalized_risk"], abs=1e-5)


# ── 10. Priority boundaries ────────────────────────────────────────────────────
@pytest.mark.parametrize("score_raw, expected_priority", [
    # Just below LOW boundary
    (0.0, "LOW"),
    (0.29, "LOW"),       # 0.29 * 10 = 2.9 → LOW
    # At LOW/MODERATE boundary
    (0.30, "MODERATE"),  # 3.0 → MODERATE
    (0.499, "MODERATE"), # 4.99 → MODERATE
    # At MODERATE/HIGH boundary
    (0.50, "HIGH"),      # 5.0 → HIGH
    (0.699, "HIGH"),     # 6.99 → HIGH
    # At HIGH/VERY_HIGH boundary
    (0.70, "VERY_HIGH"), # 7.0 → VERY_HIGH
    (0.849, "VERY_HIGH"),# 8.49 → VERY_HIGH
    # At VERY_HIGH/CRITICAL boundary
    (0.85, "CRITICAL"),  # 8.5 → CRITICAL
    (1.0,  "CRITICAL"),  # 10.0 → CRITICAL
])
def test_priority_boundaries(score_raw, expected_priority):
    # Use flood_severity only to drive exactly the right score via single weight
    # Normalize score_raw to flood input: input = score_raw / FLOOD_SEVERITY_WEIGHT
    # But that may exceed 1.0 for high scores. Use all-factors equal approach instead.
    # With equal inputs: score = input * (sum_of_weights) * 10 = input * 10
    r = calculate_risk(score_raw, score_raw, score_raw, score_raw)
    assert r["priority"] == expected_priority


# ── 11. Invalid values ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("kwargs", [
    {"flood_severity": -0.1, "building_exposure": 0.5, "road_disruption": 0.5, "critical_facility_exposure": 0.5},
    {"flood_severity": 1.1,  "building_exposure": 0.5, "road_disruption": 0.5, "critical_facility_exposure": 0.5},
    {"flood_severity": 0.5,  "building_exposure": -0.1,"road_disruption": 0.5, "critical_facility_exposure": 0.5},
    {"flood_severity": 0.5,  "building_exposure": 1.5, "road_disruption": 0.5, "critical_facility_exposure": 0.5},
    {"flood_severity": 0.5,  "building_exposure": 0.5, "road_disruption": -0.5,"critical_facility_exposure": 0.5},
    {"flood_severity": 0.5,  "building_exposure": 0.5, "road_disruption": 1.5, "critical_facility_exposure": 0.5},
    {"flood_severity": 0.5,  "building_exposure": 0.5, "road_disruption": 0.5, "critical_facility_exposure": -0.1},
    {"flood_severity": 0.5,  "building_exposure": 0.5, "road_disruption": 0.5, "critical_facility_exposure": 1.1},
])
def test_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        calculate_risk(**kwargs)


# ── 12. Deterministic output ───────────────────────────────────────────────────
def test_deterministic():
    inputs = dict(flood_severity=0.8, building_exposure=0.5, road_disruption=0.3, critical_facility_exposure=0.7)
    r1 = calculate_risk(**inputs)
    r2 = calculate_risk(**inputs)
    assert r1["risk_score"] == r2["risk_score"]
    assert r1["priority"] == r2["priority"]
    assert r1["breakdown"] == r2["breakdown"]


# ── 13. API endpoint ───────────────────────────────────────────────────────────
def test_api_endpoint():
    resp = client.post("/api/risk/calculate", json={
        "flood_severity": 0.82,
        "building_exposure": 0.60,
        "road_disruption": 0.35,
        "critical_facility_exposure": 0.50,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "risk_score" in data
    assert "priority" in data
    assert "breakdown" in data
    assert data["risk_score"] == pytest.approx(6.07, abs=0.01)


# ── 14. Schema validation ──────────────────────────────────────────────────────
def test_schema_validation_rejects_out_of_range():
    resp = client.post("/api/risk/calculate", json={
        "flood_severity": 1.5,   # invalid
        "building_exposure": 0.5,
        "road_disruption": 0.5,
        "critical_facility_exposure": 0.5,
    })
    assert resp.status_code == 422
