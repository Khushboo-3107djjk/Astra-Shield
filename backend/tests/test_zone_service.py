"""
Tests for zone-level risk analysis service.
"""

import pytest
import os
from shapely.geometry import box, Polygon
from shapely.geometry.base import BaseGeometry
import geopandas as gpd
from app.services import zone_service, geo_service
from app.services.risk_service import calculate_risk
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Paths to test data (relative to backend root)
FLOOD_MASK_PATH = os.path.join("tests", "data", "test_flood_mask.tif")
BUILDINGS_PATH = os.path.join("tests", "data", "test_buildings.geojson")
ROADS_PATH = os.path.join("tests", "data", "test_roads.geojson")
FACILITIES_PATH = os.path.join("tests", "data", "test_critical_facilities.geojson")


@pytest.fixture
def flood_geometry_and_crs():
    """Load flood geometry from test raster."""
    flood_result = geo_service.process_flood_mask(FLOOD_MASK_PATH)
    flood_geom_schema = flood_result["geometry"]

    # Convert GeoJSONGeometry back to Shapely
    from shapely.geometry import shape
    flood_dict = {
        "type": flood_geom_schema.type,
        "coordinates": flood_geom_schema.coordinates,
    }
    flood_shapely = shape(flood_dict)

    return flood_shapely, flood_result["crs"]


# ── Test 1 — Zone generation ──────────────────────────────────────────────────
def test_zone_generation(flood_geometry_and_crs):
    flood_geom, flood_crs = flood_geometry_and_crs

    zones = zone_service.generate_zones(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        grid_rows=4,
        grid_columns=4,
    )

    assert len(zones) > 0, "Should generate at least one zone"
    assert all("zone_id" in z for z in zones), "All zones should have zone_id"
    assert all("geometry" in z for z in zones), "All zones should have geometry"


# ── Test 2 — Deterministic zone IDs ───────────────────────────────────────────
def test_deterministic_zone_ids(flood_geometry_and_crs):
    flood_geom, flood_crs = flood_geometry_and_crs

    zones1 = zone_service.generate_zones(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        grid_rows=4,
        grid_columns=4,
    )

    zones2 = zone_service.generate_zones(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        grid_rows=4,
        grid_columns=4,
    )

    assert len(zones1) == len(zones2), "Should generate same number of zones"
    zone_ids_1 = [z["zone_id"] for z in zones1]
    zone_ids_2 = [z["zone_id"] for z in zones2]
    assert zone_ids_1 == zone_ids_2, "Zone IDs should be identical on re-run"


# ── Test 3 — Outside cells excluded ────────────────────────────────────────────
def test_outside_cells_excluded(flood_geometry_and_crs):
    flood_geom, flood_crs = flood_geometry_and_crs

    zones = zone_service.generate_zones(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        grid_rows=4,
        grid_columns=4,
    )

    # All zones should intersect flood polygon
    for zone in zones:
        zone_geom = zone["geometry"]
        assert zone_geom.intersects(flood_geom), f"Zone {zone['zone_id']} should intersect flood"


# ── Test 4 — Zone geometry ────────────────────────────────────────────────────
def test_zone_geometry(flood_geometry_and_crs):
    flood_geom, flood_crs = flood_geometry_and_crs

    zones = zone_service.generate_zones(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        grid_rows=4,
        grid_columns=4,
    )

    for zone in zones:
        geom = zone["geometry"]
        assert geom.geom_type == "Polygon", f"Zone {zone['zone_id']} should be Polygon"
        assert geom.is_valid, f"Zone {zone['zone_id']} should be valid geometry"


# ── Test 5 — Flood severity ───────────────────────────────────────────────────
def test_flood_severity(flood_geometry_and_crs):
    flood_geom, flood_crs = flood_geometry_and_crs

    zones = zone_service.generate_zones(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        grid_rows=4,
        grid_columns=4,
    )

    for zone in zones:
        severity = zone_service.calculate_zone_flood_severity(
            zone_geometry=zone["geometry"],
            flood_geometry=flood_geom,
            zone_crs=flood_crs,
        )

        assert 0 <= severity <= 1, f"Severity should be [0, 1], got {severity}"


# ── Test 6 — Building exposure ─────────────────────────────────────────────────
def test_building_exposure(flood_geometry_and_crs):
    flood_geom, flood_crs = flood_geometry_and_crs

    zones = zone_service.generate_zones(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        grid_rows=4,
        grid_columns=4,
    )

    for zone in zones:
        exposure = zone_service.calculate_zone_building_exposure(
            zone_geometry=zone["geometry"],
            zone_crs=flood_crs,
            buildings_source=BUILDINGS_PATH,
        )

        assert 0 <= exposure <= 1, f"Building exposure should be [0, 1], got {exposure}"


# ── Test 7 — Road disruption ───────────────────────────────────────────────────
def test_road_disruption(flood_geometry_and_crs):
    flood_geom, flood_crs = flood_geometry_and_crs

    zones = zone_service.generate_zones(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        grid_rows=4,
        grid_columns=4,
    )

    for zone in zones:
        disruption = zone_service.calculate_zone_road_disruption(
            zone_geometry=zone["geometry"],
            zone_crs=flood_crs,
            roads_source=ROADS_PATH,
        )

        assert 0 <= disruption <= 1, f"Road disruption should be [0, 1], got {disruption}"


# ── Test 8 — Facility exposure ─────────────────────────────────────────────────
def test_facility_exposure(flood_geometry_and_crs):
    flood_geom, flood_crs = flood_geometry_and_crs

    zones = zone_service.generate_zones(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        grid_rows=4,
        grid_columns=4,
    )

    for zone in zones:
        exposure = zone_service.calculate_zone_facility_exposure(
            zone_geometry=zone["geometry"],
            zone_crs=flood_crs,
            facilities_source=FACILITIES_PATH,
        )

        assert 0 <= exposure <= 1, f"Facility exposure should be [0, 1], got {exposure}"


# ── Test 9 — Zero-building zone ───────────────────────────────────────────────
def test_zero_building_zone():
    # Create a zone far outside flood area
    isolated_zone = box(-180, -90, -170, -80)

    # Should return 0 exposure when no buildings intersect
    exposure = zone_service.calculate_zone_building_exposure(
        zone_geometry=isolated_zone,
        zone_crs="EPSG:4326",
        buildings_source=BUILDINGS_PATH,
    )

    assert exposure == 0.0, "Should return 0 exposure when no buildings in zone"


# ── Test 10 — Zero-road zone ──────────────────────────────────────────────────
def test_zero_road_zone():
    # Create a zone far outside flood area
    isolated_zone = box(-180, -90, -170, -80)

    disruption = zone_service.calculate_zone_road_disruption(
        zone_geometry=isolated_zone,
        zone_crs="EPSG:4326",
        roads_source=ROADS_PATH,
    )

    assert disruption == 0.0, "Should return 0 disruption when no roads in zone"


# ── Test 11 — Zero-facility zone ──────────────────────────────────────────────
def test_zero_facility_zone():
    # Create a zone far outside flood area
    isolated_zone = box(-180, -90, -170, -80)

    exposure = zone_service.calculate_zone_facility_exposure(
        zone_geometry=isolated_zone,
        zone_crs="EPSG:4326",
        facilities_source=FACILITIES_PATH,
    )

    assert exposure == 0.0, "Should return 0 exposure when no facilities in zone"


# ── Test 12 — Risk engine integration ──────────────────────────────────────────
def test_risk_engine_integration(flood_geometry_and_crs):
    """Verify zone service uses existing risk_service.calculate_risk()."""
    flood_geom, flood_crs = flood_geometry_and_crs

    zones_result = zone_service.calculate_zones_with_risk(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        buildings_source=BUILDINGS_PATH,
        roads_source=ROADS_PATH,
        facilities_source=FACILITIES_PATH,
        grid_rows=4,
        grid_columns=4,
    )

    # All zones should have risk_score in [0, 10]
    for zone in zones_result["zones"]:
        assert 0 <= zone["risk_score"] <= 10
        assert zone["priority"] in ["LOW", "MODERATE", "HIGH", "VERY_HIGH", "CRITICAL"]


# ── Test 13 — Priority ────────────────────────────────────────────────────────
def test_zone_priority(flood_geometry_and_crs):
    """Verify zone priority matches risk engine output."""
    flood_geom, flood_crs = flood_geometry_and_crs

    zones_result = zone_service.calculate_zones_with_risk(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        buildings_source=BUILDINGS_PATH,
        roads_source=ROADS_PATH,
        facilities_source=FACILITIES_PATH,
        grid_rows=2,
        grid_columns=2,
    )

    for zone in zones_result["zones"]:
        # Verify priority is correct from risk_service
        risk_result = calculate_risk(
            flood_severity=zone["flood_severity"],
            building_exposure=zone["building_exposure"],
            road_disruption=zone["road_disruption"],
            critical_facility_exposure=zone["critical_facility_exposure"],
        )

        assert zone["priority"] == risk_result["priority"], \
            f"Zone priority should match risk engine output"


# ── Test 14 — Risk breakdown ──────────────────────────────────────────────────
def test_zone_risk_breakdown(flood_geometry_and_crs):
    """Verify zone output contains risk breakdown."""
    flood_geom, flood_crs = flood_geometry_and_crs

    zones_result = zone_service.calculate_zones_with_risk(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        buildings_source=BUILDINGS_PATH,
        roads_source=ROADS_PATH,
        facilities_source=FACILITIES_PATH,
        grid_rows=2,
        grid_columns=2,
    )

    for zone in zones_result["zones"]:
        bd = zone["risk_breakdown"]
        
        # All factors should be in breakdown
        assert "flood_severity" in bd
        assert "building_exposure" in bd
        assert "road_disruption" in bd
        assert "critical_facility_exposure" in bd

        # Each factor should have value, weight, contribution
        for factor_name, factor_data in bd.items():
            assert "value" in factor_data
            assert "weight" in factor_data
            assert "contribution" in factor_data


# ── Test 15 — Highest-risk ordering ───────────────────────────────────────────
def test_highest_risk_ordering(flood_geometry_and_crs):
    """Verify zones are sorted by risk_score descending."""
    flood_geom, flood_crs = flood_geometry_and_crs

    zones_result = zone_service.calculate_zones_with_risk(
        flood_geometry=flood_geom,
        flood_crs=flood_crs,
        buildings_source=BUILDINGS_PATH,
        roads_source=ROADS_PATH,
        facilities_source=FACILITIES_PATH,
        grid_rows=4,
        grid_columns=4,
    )

    zones = zones_result["zones"]

    if len(zones) > 1:
        # Verify descending order
        for i in range(len(zones) - 1):
            assert zones[i]["risk_score"] >= zones[i + 1]["risk_score"], \
                "Zones should be sorted by risk_score descending"

    # Verify highest_risk_zone_id is correct
    if zones:
        highest_id = zones_result["highest_risk_zone_id"]
        highest_score = zones_result["highest_risk_score"]
        assert highest_id == zones[0]["zone_id"]
        assert highest_score == pytest.approx(zones[0]["risk_score"], abs=0.01)


# ── Test 16 — CRS handling ─────────────────────────────────────────────────────
def test_crs_handling():
    """Verify zone service works with different CRS values."""
    # Create simple test geometry in EPSG:4326
    simple_flood = box(20, 40, 21, 41)

    zones = zone_service.generate_zones(
        flood_geometry=simple_flood,
        flood_crs="EPSG:4326",
        grid_rows=2,
        grid_columns=2,
    )

    assert len(zones) > 0
    for zone in zones:
        severity = zone_service.calculate_zone_flood_severity(
            zone_geometry=zone["geometry"],
            flood_geometry=simple_flood,
            zone_crs="EPSG:4326",
        )
        assert 0 <= severity <= 1


# ── Test 17 — Empty flood geometry ─────────────────────────────────────────────
def test_empty_flood_geometry():
    """Handle empty flood geometry safely."""
    empty_polygon = Polygon()

    zones = zone_service.generate_zones(
        flood_geometry=empty_polygon,
        flood_crs="EPSG:4326",
        grid_rows=2,
        grid_columns=2,
    )

    assert len(zones) == 0, "Should return zero zones for empty flood"

    result = zone_service.calculate_zones_with_risk(
        flood_geometry=empty_polygon,
        flood_crs="EPSG:4326",
        buildings_source=BUILDINGS_PATH,
        roads_source=ROADS_PATH,
        facilities_source=FACILITIES_PATH,
    )

    assert result["total_zones"] == 0
    assert result["highest_risk_zone_id"] is None


# ── Test 18 — API endpoint ─────────────────────────────────────────────────────
def test_api_zones_endpoint():
    """Test POST /api/risk/zones endpoint."""
    resp = client.post("/api/risk/zones")

    assert resp.status_code == 200
    data = resp.json()

    assert "zones" in data
    assert "total_zones" in data
    assert "highest_risk_zone_id" in data
    assert "highest_risk_score" in data

    assert isinstance(data["zones"], list)
    assert isinstance(data["total_zones"], int)

    if data["zones"]:
        zone = data["zones"][0]
        assert "zone_id" in zone
        assert "risk_score" in zone
        assert "priority" in zone
        assert "geometry" in zone
        assert "flood_severity" in zone
        assert "building_exposure" in zone
        assert "road_disruption" in zone
        assert "critical_facility_exposure" in zone
        assert "affected_buildings" in zone
        assert "affected_road_length_km" in zone
        assert "affected_facilities" in zone
        assert "risk_breakdown" in zone
