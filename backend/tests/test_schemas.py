import pytest
from pydantic import ValidationError
from app.schemas.analysis import MLAnalysisInput
from app.schemas.zone import RiskZone

def test_valid_analysis_input():
    data = {
        "analysis_id": "demo_001",
        "disaster_type": "flood",
        "confidence": 0.93,
        "severity": 0.82,
        "affected_area_km2": 42.8,
        "mask_path": "/path/to/mask.png"
    }
    input_model = MLAnalysisInput(**data)
    assert input_model.analysis_id == "demo_001"
    assert input_model.disaster_type == "flood"
    assert input_model.confidence == 0.93

def test_invalid_confidence():
    data = {
        "analysis_id": "demo_002",
        "disaster_type": "flood",
        "confidence": 1.5,  # Invalid
        "severity": 0.82,
        "affected_area_km2": 42.8
    }
    with pytest.raises(ValidationError):
        MLAnalysisInput(**data)

def test_invalid_severity():
    data = {
        "analysis_id": "demo_003",
        "disaster_type": "flood",
        "confidence": 0.9,
        "severity": -0.2,  # Invalid
        "affected_area_km2": 42.8
    }
    with pytest.raises(ValidationError):
        MLAnalysisInput(**data)

def test_invalid_affected_area():
    data = {
        "analysis_id": "demo_004",
        "disaster_type": "flood",
        "confidence": 0.9,
        "severity": 0.8,
        "affected_area_km2": -10  # Invalid
    }
    with pytest.raises(ValidationError):
        MLAnalysisInput(**data)

def test_valid_zone():
    data = {
        "zone_id": "Z001",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        },
        "flood_severity": 0.85,
        "building_exposure": 0.70,
        "road_disruption": 0.40,
        "critical_facility_exposure": 0.50,
        "risk_score": 7.1,
        "priority": "VERY_HIGH",
        "affected_buildings": 12,
        "affected_road_length_km": 3.5,
        "affected_facilities": 2,
    }
    zone = RiskZone(**data)
    assert zone.zone_id == "Z001"
    assert zone.priority == "VERY_HIGH"
    assert zone.geometry.type == "Polygon"
    assert zone.flood_severity == 0.85
    assert zone.risk_score == 7.1
