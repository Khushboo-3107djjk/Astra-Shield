import pytest
import os
from app.services.geo_service import process_flood_mask
from app.api.errors import APIError

VALID_MASK_PATH = "tests/data/test_flood_mask.tif"
INVALID_CRS_PATH = "tests/data/invalid_crs_mask.tif"
NONEXISTENT_PATH = "tests/data/does_not_exist.tif"

def test_process_valid_raster():
    assert os.path.exists(VALID_MASK_PATH), "Test raster was not created"
    result = process_flood_mask(VALID_MASK_PATH)
    
    # Check structure
    assert "geometry" in result
    assert "affected_area_km2" in result
    assert "flood_pixel_count" in result
    assert "crs" in result

def test_flood_pixel_count():
    result = process_flood_mask(VALID_MASK_PATH)
    # The script created a 4x4 block of 1s
    assert result["flood_pixel_count"] == 16

def test_polygon_generation():
    result = process_flood_mask(VALID_MASK_PATH)
    geom = result["geometry"]
    assert geom is not None
    assert geom.type in ["Polygon", "MultiPolygon"]
    assert len(geom.coordinates) > 0

def test_crs_preservation():
    result = process_flood_mask(VALID_MASK_PATH)
    # The test raster was EPSG:4326
    assert "EPSG:4326" in result["crs"]

def test_area_calculation():
    result = process_flood_mask(VALID_MASK_PATH)
    area = result["affected_area_km2"]
    
    # 4x4 block of 0.01 degree pixels. Top-left at (10.0, 50.0).
    # The flood block spans:
    # Longitude: 10.03 to 10.07
    # Latitude: 49.93 to 49.97
    # 
    # Independently calculating area of this box on WGS84 ellipsoid using pyproj.Geod
    # yields an expected area of ~12.7726 sq km.
    expected_area = 12.7726
    
    # Verify the calculated area matches the expected area within a tiny tolerance (0.001)
    assert abs(area - expected_area) < 0.001

def test_invalid_raster():
    with pytest.raises(APIError) as exc_info:
        process_flood_mask(INVALID_CRS_PATH)
    assert exc_info.value.status_code == 400
    assert "CRS" in str(exc_info.value)
    
def test_nonexistent_raster():
    with pytest.raises(APIError) as exc_info:
        process_flood_mask(NONEXISTENT_PATH)
    assert exc_info.value.status_code == 400
    assert "Cannot read raster file" in str(exc_info.value)
