import pytest
import geopandas as gpd
from shapely.geometry import Polygon
from app.services.building_service import analyze_building_impact
from app.api.errors import APIError

BUILDINGS_PATH = "tests/data/test_buildings.geojson"
EMPTY_PATH = "tests/data/empty_buildings.geojson"
MISMATCH_CRS_PATH = "tests/data/mismatch_crs_buildings.geojson"

# Flood polygon covering Lon: 10.03 to 10.07, Lat: 49.93 to 49.97
FLOOD_POLYGON = Polygon([
    (10.03, 49.93), 
    (10.07, 49.93), 
    (10.07, 49.97), 
    (10.03, 49.97), 
    (10.03, 49.93)
])
FLOOD_CRS = "EPSG:4326"

def test_total_building_count():
    res = analyze_building_impact(FLOOD_POLYGON, FLOOD_CRS, BUILDINGS_PATH)
    assert res["total_buildings"] == 3

def test_completely_outside_building():
    res = analyze_building_impact(FLOOD_POLYGON, FLOOD_CRS, BUILDINGS_PATH)
    assert "B_OUT" not in res["affected_building_ids"]

def test_completely_inside_building():
    res = analyze_building_impact(FLOOD_POLYGON, FLOOD_CRS, BUILDINGS_PATH)
    assert "B_IN" in res["affected_building_ids"]

def test_partially_intersecting_building():
    res = analyze_building_impact(FLOOD_POLYGON, FLOOD_CRS, BUILDINGS_PATH)
    assert "B_INTERSECT" in res["affected_building_ids"]

def test_affected_percentage():
    res = analyze_building_impact(FLOOD_POLYGON, FLOOD_CRS, BUILDINGS_PATH)
    assert res["affected_buildings"] == 2
    assert res["total_buildings"] == 3
    # 2 / 3 = 66.67
    assert abs(res["affected_percentage"] - 66.67) < 0.01

def test_crs_mismatch():
    # Provide flood poly in 4326, but buildings in 3857
    res = analyze_building_impact(FLOOD_POLYGON, FLOOD_CRS, MISMATCH_CRS_PATH)
    # The reprojection should align them and give the same result
    assert res["total_buildings"] == 3
    assert res["affected_buildings"] == 2
    assert "B_IN" in res["affected_building_ids"]

def test_empty_building_dataset():
    res = analyze_building_impact(FLOOD_POLYGON, FLOOD_CRS, EMPTY_PATH)
    assert res["total_buildings"] == 0
    assert res["affected_buildings"] == 0
    assert res["affected_percentage"] == 0.0
    assert len(res["affected_building_ids"]) == 0

def test_output_geometry():
    res = analyze_building_impact(FLOOD_POLYGON, FLOOD_CRS, BUILDINGS_PATH)
    geom_list = res["affected_buildings_geometry"]
    assert len(geom_list) == 2
    for b in geom_list:
        assert "building_id" in b
        assert "geometry" in b
        # Verify valid GeoJSON-compatible type
        assert b["geometry"]["type"] in ["Polygon", "MultiPolygon"]
        assert len(b["geometry"]["coordinates"]) > 0

def test_invalid_source():
    with pytest.raises(APIError) as exc_info:
        analyze_building_impact(FLOOD_POLYGON, FLOOD_CRS, "non_existent.geojson")
    assert exc_info.value.status_code == 404
