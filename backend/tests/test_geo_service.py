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
    # 4x4 block of 0.01 degree pixels at latitude 50
    # A 0.01 deg x 0.01 deg pixel at equator is roughly 1.11km x 1.11km = ~1.23 sq km.
    # At 50 N, longitude degree is shorter (cos(50) ~ 0.642). Area per pixel is smaller.
    # The calculation EPSG:6933 should give a reasonable strictly positive physical area.
    assert area > 0.0
    assert area < 100.0 # Just a reasonable bound

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
