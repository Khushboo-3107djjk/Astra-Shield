import pytest
import geopandas as gpd
from shapely.geometry import Polygon
from app.services.road_service import analyze_road_impact
from app.api.errors import APIError

ROADS_PATH = "tests/data/test_roads.geojson"
EMPTY_PATH = "tests/data/empty_roads.geojson"
MISMATCH_CRS_PATH = "tests/data/mismatch_crs_roads.geojson"

# Flood polygon covering Lon: 10.03 to 10.07, Lat: 49.93 to 49.97
FLOOD_POLYGON = Polygon([
    (10.03, 49.93), 
    (10.07, 49.93), 
    (10.07, 49.97), 
    (10.03, 49.97), 
    (10.03, 49.93)
])
FLOOD_CRS = "EPSG:4326"

def test_total_road_count():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, ROADS_PATH)
    assert res["total_road_segments"] == 3

def test_completely_outside_road():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, ROADS_PATH)
    assert "R_OUT" not in res["affected_road_ids"]

def test_completely_inside_road():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, ROADS_PATH)
    assert "R_IN" in res["affected_road_ids"]

def test_partially_intersecting_road():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, ROADS_PATH)
    assert "R_PARTIAL" in res["affected_road_ids"]

def test_affected_length():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, ROADS_PATH)
    
    # Independent Geod calculation on WGS84 ellipsoid:
    # R_IN intersection (10.04 to 10.06 at 49.95 N) -> ~1.4354 km
    # R_PARTIAL intersection (10.03 to 10.05 at 49.96 N) -> ~1.4351 km
    # Expected total affected length -> ~2.8705 km
    # The service uses UTM reprojection, which introduces slight <0.05% difference.
    expected_total_affected = 2.8705
    
    # We use a numerical tolerance of 0.005 km (5 meters) to account for UTM projection difference.
    assert abs(res["affected_road_length_km"] - expected_total_affected) < 0.005

def test_total_length():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, ROADS_PATH)
    
    # Independent Geod calculation on WGS84 ellipsoid:
    # R_IN total (10.04 to 10.06 at 49.95 N) -> ~1.4354 km
    # R_OUT total (10.10 to 10.12 at 49.90 N) -> ~1.4369 km
    # R_PARTIAL total (10.01 to 10.05 at 49.96 N) -> ~2.8702 km
    # Expected overall total length -> ~5.7425 km
    expected_overall_total = 5.7425
    
    # We use a numerical tolerance of 0.005 km (5 meters) to account for UTM projection difference.
    assert abs(res["total_road_length_km"] - expected_overall_total) < 0.005

def test_major_minor_classification():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, ROADS_PATH)
    assert res["major_roads"]["total_segments"] == 2
    assert res["major_roads"]["affected_segments"] == 2
    assert res["minor_roads"]["total_segments"] == 1
    assert res["minor_roads"]["affected_segments"] == 0

def test_crs_mismatch():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, MISMATCH_CRS_PATH)
    assert res["total_road_segments"] == 3
    assert res["affected_road_segments"] == 2
    assert "R_IN" in res["affected_road_ids"]

def test_empty_road_dataset():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, EMPTY_PATH)
    assert res["total_road_segments"] == 0
    assert res["affected_road_segments"] == 0
    assert res["affected_percentage"] == 0.0
    assert res["affected_road_length_km"] == 0.0
    assert len(res["affected_road_ids"]) == 0

def test_output_geometry():
    res = analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, ROADS_PATH)
    geom_list = res["affected_road_details"]
    assert len(geom_list) == 2
    for r in geom_list:
        assert "road_id" in r
        assert "geometry" in r
        assert r["geometry"]["type"] in ["LineString", "MultiLineString"]
        assert len(r["geometry"]["coordinates"]) > 0

def test_invalid_source():
    with pytest.raises(APIError) as exc_info:
        analyze_road_impact(FLOOD_POLYGON, FLOOD_CRS, "non_existent.geojson")
    assert exc_info.value.status_code == 404
