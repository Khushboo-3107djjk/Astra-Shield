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
        "zone_id": "A",
        "risk_score": 8.7,
        "priority": "CRITICAL",
        "affected_area_km2": 12.4,
        "affected_buildings": 540,
        "affected_roads": 9,
        "critical_facilities": 2,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    }
    zone = RiskZone(**data)
    assert zone.zone_id == "A"
    assert zone.priority == "CRITICAL"
    assert zone.geometry.type == "Polygon"
