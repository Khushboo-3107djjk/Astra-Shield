"""
Tests for end-to-end analysis integration.
"""

import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.analysis import MLAnalysisInput, DisasterType
from app.services.analysis_service import analyze_synthetic_disaster

client = TestClient(app)

# Synthetic test data paths
FLOOD_MASK_PATH = os.path.join("tests", "data", "test_flood_mask.tif")
BUILDINGS_PATH = os.path.join("tests", "data", "test_buildings.geojson")
ROADS_PATH = os.path.join("tests", "data", "test_roads.geojson")
FACILITIES_PATH = os.path.join("tests", "data", "test_critical_facilities.geojson")


# ── Test 1 — End-to-end successful analysis ────────────────────────────────────
def test_end_to_end_successful_analysis():
    """Verify complete analysis succeeds with synthetic data."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_001",
        disaster_type=DisasterType.FLOOD,
        confidence=0.93,
        severity=0.82,
        affected_area_km2=0,  # Will be overridden by calculated value
        mask_path=FLOOD_MASK_PATH,
    )

    result = analyze_synthetic_disaster(analysis_input)

    assert result is not None
    assert result.summary is not None
    assert result.impact is not None
    assert result.risk is not None
    assert result.zones is not None
    assert result.timeline is not None


# ── Test 2 — Real affected area calculation ────────────────────────────────────
def test_real_affected_area():
    """Verify affected_area_km2 comes from geo_service, not client input."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_002",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.75,
        affected_area_km2=999.0,  # Intentionally wrong
        mask_path=FLOOD_MASK_PATH,
    )

    result = analyze_synthetic_disaster(analysis_input)

    # The calculated area should NOT be 999.0
    # Test flood raster should have a specific calculated area (~12.77 sq km)
    assert result.summary.affected_area_km2 != 999.0
    assert result.summary.affected_area_km2 > 0
    assert result.summary.affected_area_km2 < 100.0  # Reasonable synthetic test area


# ── Test 3 — Building impact integration ───────────────────────────────────────
def test_building_impact_integration():
    """Verify actual affected building count appears in response."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_003",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.7,
        affected_area_km2=0,
        mask_path=FLOOD_MASK_PATH,
    )

    result = analyze_synthetic_disaster(analysis_input)

    # Buildings should be analyzed from test dataset
    assert result.impact.affected_buildings >= 0
    # With test data, we expect some buildings to be affected
    assert result.impact.affected_buildings > 0


# ── Test 4 — Road impact integration ───────────────────────────────────────────
def test_road_impact_integration():
    """Verify actual affected road segments appear in response."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_004",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.7,
        affected_area_km2=0,
        mask_path=FLOOD_MASK_PATH,
    )

    result = analyze_synthetic_disaster(analysis_input)

    # Roads should be analyzed from test dataset
    assert result.impact.affected_roads >= 0
    # With test data, we expect some roads to be affected
    assert result.impact.affected_roads > 0


# ── Test 5 — Infrastructure integration ────────────────────────────────────────
def test_infrastructure_integration():
    """Verify actual affected facility count appears in response."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_005",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.7,
        affected_area_km2=0,
        mask_path=FLOOD_MASK_PATH,
    )

    result = analyze_synthetic_disaster(analysis_input)

    # Facilities should be analyzed from test dataset
    assert result.impact.affected_critical_facilities >= 0
    # With test data, we expect some facilities to be affected
    assert result.impact.affected_critical_facilities > 0


# ── Test 6 — Overall risk integration ──────────────────────────────────────────
def test_overall_risk_integration():
    """Verify RiskSummary matches risk_service output."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_006",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.8,
        affected_area_km2=0,
        mask_path=FLOOD_MASK_PATH,
    )

    result = analyze_synthetic_disaster(analysis_input)

    # Risk score should be in valid range
    assert 0 <= result.risk.overall_risk_score <= 10
    # Priority should be one of the valid values
    assert result.risk.overall_priority in [
        "LOW",
        "MODERATE",
        "HIGH",
        "VERY_HIGH",
        "CRITICAL",
    ]


# ── Test 7 — Zone integration ──────────────────────────────────────────────────
def test_zone_integration():
    """Verify zones are present and generated from flood geometry."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_007",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.75,
        affected_area_km2=0,
        mask_path=FLOOD_MASK_PATH,
    )

    result = analyze_synthetic_disaster(analysis_input)

    # Should generate multiple zones
    assert len(result.zones) > 0

    # Each zone should have valid properties
    for zone in result.zones:
        assert zone.zone_id is not None
        assert 0 <= zone.risk_score <= 10
        assert zone.priority is not None
        assert zone.geometry is not None


# ── Test 8 — Highest-risk zone ────────────────────────────────────────────────
def test_highest_risk_zone():
    """Verify highest-risk zone is correctly identified."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_008",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.8,
        affected_area_km2=0,
        mask_path=FLOOD_MASK_PATH,
    )

    result = analyze_synthetic_disaster(analysis_input)

    if len(result.zones) > 1:
        # Zones should be sorted descending by risk_score
        for i in range(len(result.zones) - 1):
            assert result.zones[i].risk_score >= result.zones[i + 1].risk_score


# ── Test 9 — Timeline ──────────────────────────────────────────────────────────
def test_timeline():
    """Verify timeline is present as empty list for Part 6A."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_009",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.75,
        affected_area_km2=0,
        mask_path=FLOOD_MASK_PATH,
    )

    result = analyze_synthetic_disaster(analysis_input)

    # Part 6A: timeline should be empty
    assert isinstance(result.timeline, list)
    assert len(result.timeline) == 0


# ── Test 10 — Client area ignored ─────────────────────────────────────────────
def test_client_area_ignored():
    """Verify geospatial calculation is used, not client-supplied area."""
    # Create two requests with different affected_area_km2 values
    analysis_input_1 = MLAnalysisInput(
        analysis_id="integration_test_010a",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.75,
        affected_area_km2=100.0,  # Wrong value
        mask_path=FLOOD_MASK_PATH,
    )

    analysis_input_2 = MLAnalysisInput(
        analysis_id="integration_test_010b",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.75,
        affected_area_km2=999.0,  # Different wrong value
        mask_path=FLOOD_MASK_PATH,
    )

    result_1 = analyze_synthetic_disaster(analysis_input_1)
    result_2 = analyze_synthetic_disaster(analysis_input_2)

    # Both should produce same calculated area
    assert (
        result_1.summary.affected_area_km2
        == result_2.summary.affected_area_km2
    )

    # Neither should be the client-supplied value
    assert result_1.summary.affected_area_km2 != 100.0
    assert result_1.summary.affected_area_km2 != 999.0


# ── Test 11 — Invalid mask ────────────────────────────────────────────────────
def test_invalid_mask():
    """Verify missing/invalid mask produces clear API error."""
    analysis_input = MLAnalysisInput(
        analysis_id="integration_test_011",
        disaster_type=DisasterType.FLOOD,
        confidence=0.9,
        severity=0.75,
        affected_area_km2=0,
        mask_path="nonexistent/path/mask.tif",
    )

    from app.api.errors import APIError

    with pytest.raises(APIError):
        analyze_synthetic_disaster(analysis_input)


# ── Test 12 — Invalid request ──────────────────────────────────────────────────
def test_invalid_request():
    """Verify Pydantic validation rejects invalid input."""
    from pydantic import ValidationError

    # Invalid confidence > 1
    with pytest.raises(ValidationError):
        MLAnalysisInput(
            analysis_id="test",
            disaster_type=DisasterType.FLOOD,
            confidence=1.5,  # Invalid
            severity=0.75,
            affected_area_km2=0,
            mask_path=FLOOD_MASK_PATH,
        )

    # Invalid severity < 0
    with pytest.raises(ValidationError):
        MLAnalysisInput(
            analysis_id="test",
            disaster_type=DisasterType.FLOOD,
            confidence=0.9,
            severity=-0.1,  # Invalid
            affected_area_km2=0,
            mask_path=FLOOD_MASK_PATH,
        )


# ── Test 13 — API endpoint ────────────────────────────────────────────────────
def test_api_endpoint():
    """Test POST /api/analyze endpoint with synthetic test request."""
    request_data = {
        "analysis_id": "integration_test_013",
        "disaster_type": "flood",
        "confidence": 0.93,
        "severity": 0.82,
        "affected_area_km2": 0,
        "mask_path": FLOOD_MASK_PATH,
    }

    response = client.post("/api/analyze", json=request_data)

    assert response.status_code == 200

    data = response.json()

    # Verify complete response structure
    assert "summary" in data
    assert "impact" in data
    assert "risk" in data
    assert "zones" in data
    assert "timeline" in data

    # Verify summary fields
    summary = data["summary"]
    assert summary["analysis_id"] == "integration_test_013"
    assert summary["disaster_type"] == "flood"
    assert summary["confidence"] == 0.93
    assert summary["severity"] == 0.82
    assert summary["affected_area_km2"] > 0

    # Verify impact fields
    impact = data["impact"]
    assert "affected_buildings" in impact
    assert "affected_roads" in impact
    assert "affected_critical_facilities" in impact

    # Verify risk fields
    risk = data["risk"]
    assert "overall_risk_score" in risk
    assert "overall_priority" in risk
    assert 0 <= risk["overall_risk_score"] <= 10

    # Verify zones
    assert isinstance(data["zones"], list)
    if data["zones"]:
        zone = data["zones"][0]
        assert "zone_id" in zone
        assert "risk_score" in zone
        assert "priority" in zone

    # Verify timeline
    assert isinstance(data["timeline"], list)
