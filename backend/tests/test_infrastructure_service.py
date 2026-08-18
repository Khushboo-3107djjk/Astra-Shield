import pytest
from shapely.geometry import Polygon
from app.services.infrastructure_service import analyze_infrastructure_impact
from app.api.errors import APIError

FACILITIES_PATH = "tests/data/test_critical_facilities.geojson"
EMPTY_PATH = "tests/data/empty_critical_facilities.geojson"
MISMATCH_CRS_PATH = "tests/data/mismatch_crs_critical_facilities.geojson"

# Flood polygon: Lon 10.03 to 10.07, Lat 49.93 to 49.97
FLOOD_POLYGON = Polygon([
    (10.03, 49.93),
    (10.07, 49.93),
    (10.07, 49.97),
    (10.03, 49.97),
    (10.03, 49.93)
])
FLOOD_CRS = "EPSG:4326"


def test_total_facility_count():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, FACILITIES_PATH)
    assert res["total_facilities"] == 6


def test_hospital_inside_flood():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, FACILITIES_PATH)
    assert "H_IN" in res["affected_facility_ids"]


def test_hospital_outside_flood():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, FACILITIES_PATH)
    assert "H_OUT" not in res["affected_facility_ids"]


def test_school_inside_flood():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, FACILITIES_PATH)
    assert "S_IN" in res["affected_facility_ids"]


def test_school_outside_flood():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, FACILITIES_PATH)
    assert "S_OUT" not in res["affected_facility_ids"]


def test_emergency_inside_flood():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, FACILITIES_PATH)
    assert "E_IN" in res["affected_facility_ids"]


def test_facility_percentage():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, FACILITIES_PATH)
    # 3 inside (H_IN, S_IN, E_IN) out of 6 total = 50.0%
    assert res["affected_facilities"] == 3
    assert res["total_facilities"] == 6
    assert abs(res["affected_percentage"] - 50.0) < 0.01


def test_facility_type_breakdown():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, FACILITIES_PATH)
    summary = res["facility_type_summary"]
    assert summary["hospitals"]["total"] == 2
    assert summary["hospitals"]["affected"] == 1
    assert summary["schools"]["total"] == 2
    assert summary["schools"]["affected"] == 1
    assert summary["emergencys"]["total"] == 2
    assert summary["emergencys"]["affected"] == 1


def test_crs_mismatch():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, MISMATCH_CRS_PATH)
    assert res["total_facilities"] == 6
    assert res["affected_facilities"] == 3
    assert "H_IN" in res["affected_facility_ids"]


def test_empty_facility_dataset():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, EMPTY_PATH)
    assert res["total_facilities"] == 0
    assert res["affected_facilities"] == 0
    assert res["affected_percentage"] == 0.0
    assert len(res["affected_facility_ids"]) == 0


def test_output_geometry():
    res = analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, FACILITIES_PATH)
    details = res["affected_facility_details"]
    assert len(details) == 3
    for d in details:
        assert "facility_id" in d
        assert "facility_name" in d
        assert "facility_type" in d
        assert d["geometry"]["type"] == "Point"
        assert len(d["geometry"]["coordinates"]) == 2


def test_invalid_source():
    with pytest.raises(APIError) as exc_info:
        analyze_infrastructure_impact(FLOOD_POLYGON, FLOOD_CRS, "non_existent.geojson")
    assert exc_info.value.status_code == 404
