"""
ML Integration Service Tests
Tests for the ML/backend adapter that converts ML output to backend analysis input.
"""

import os
import pytest
import numpy as np
from pathlib import Path
import tempfile
import rasterio
from rasterio.transform import from_bounds

from app.services.ml_integration_service import (
    normalize_severity,
    generate_analysis_id,
    map_disaster_type,
    mask_to_geotiff,
    ml_output_to_analysis_input_with_mask,
)
from app.schemas.analysis import DisasterType
from app.api.errors import APIError


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def synthetic_georeferenced_raster(temp_dir):
    """Create a small synthetic georeferenced GeoTIFF for testing."""
    output_path = temp_dir / "test_source.tif"
    
    # Create a small 10x10 raster with CRS and transform
    data = np.ones((10, 10), dtype=np.uint8)
    
    # EPSG:4326 (WGS84)
    crs = "EPSG:4326"
    
    # Bounds: A small area around 10°E, 50°N (Germany)
    west, south = 10.0, 50.0
    east, north = 10.1, 50.1
    
    transform = from_bounds(west, south, east, north, 10, 10)
    
    with rasterio.open(
        str(output_path),
        'w',
        driver='GTiff',
        height=10,
        width=10,
        count=1,
        dtype=rasterio.uint8,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(data, 1)
    
    return str(output_path)


@pytest.fixture
def synthetic_ml_output():
    """Create a synthetic ML pipeline output for testing."""
    return {
        "success": True,
        "timestamp": "2026-08-18T12:00:00",
        "image_path": "/path/to/image.tif",
        "classification": {
            "disaster_type": "flood",
            "confidence": 0.94,
            "predictions": {
                "normal": 0.02,
                "flood": 0.94,
                "wildfire": 0.03,
                "landslide": 0.01,
            }
        },
        "segmentation": {
            "affected_area_km2": 24.3,
            "severity_score": 8.5,
            "confidence": 0.91,
            "mask": "base64_encoded_png_string"
        },
        "metrics": {
            "affected_pixels": 127450,
            "total_pixels": 262144,
            "affected_percentage": 48.6
        }
    }


# ──────────────────────────────────────────────────────────────────────────────
# Test 1 — Severity Normalization
# ──────────────────────────────────────────────────────────────────────────────


def test_severity_normalization_basic():
    """Verify severity is normalized from [0,10] to [0,1]."""
    assert normalize_severity(0.0) == 0.0
    assert normalize_severity(5.0) == 0.5
    assert normalize_severity(10.0) == 1.0


def test_severity_normalization_examples():
    """Test specific ML severity values."""
    assert normalize_severity(8.0) == 0.8
    assert normalize_severity(3.5) == 0.35
    assert abs(normalize_severity(7.2) - 0.72) < 0.001


def test_severity_normalization_clamping():
    """Verify clamping for edge cases."""
    # Slight overshoot is clamped
    assert normalize_severity(10.1) == 1.0
    assert normalize_severity(-0.1) == 0.0


def test_severity_normalization_invalid():
    """Verify invalid severity raises error."""
    with pytest.raises(ValueError):
        normalize_severity(-1.0)
    
    with pytest.raises(ValueError):
        normalize_severity(11.0)
    
    with pytest.raises(ValueError):
        normalize_severity("not_a_number")


# ──────────────────────────────────────────────────────────────────────────────
# Test 2 — Confidence Passthrough
# ──────────────────────────────────────────────────────────────────────────────


def test_confidence_passthrough(synthetic_ml_output):
    """Verify confidence from classification is used directly."""
    assert synthetic_ml_output["classification"]["confidence"] == 0.94
    # No transformation needed; confidence is already [0,1]


# ──────────────────────────────────────────────────────────────────────────────
# Test 3 — Analysis ID Generation
# ──────────────────────────────────────────────────────────────────────────────


def test_analysis_id_generation():
    """Verify analysis IDs are unique."""
    ids = [generate_analysis_id() for _ in range(10)]
    assert len(ids) == len(set(ids)), "Analysis IDs are not unique"


def test_analysis_id_format():
    """Verify analysis ID format."""
    aid = generate_analysis_id()
    assert isinstance(aid, str)
    assert len(aid) == 32  # UUID4 hex is 32 chars
    assert all(c in '0123456789abcdef' for c in aid)


# ──────────────────────────────────────────────────────────────────────────────
# Test 4 — Disaster Type Mapping
# ──────────────────────────────────────────────────────────────────────────────


def test_disaster_type_mapping_valid():
    """Verify correct mapping of ML disaster types."""
    assert map_disaster_type("flood") == DisasterType.FLOOD
    assert map_disaster_type("wildfire") == DisasterType.WILDFIRE
    assert map_disaster_type("landslide") == DisasterType.LANDSLIDE


def test_disaster_type_mapping_case_insensitive():
    """Verify mapping is case-insensitive."""
    assert map_disaster_type("FLOOD") == DisasterType.FLOOD
    assert map_disaster_type("Wildfire") == DisasterType.WILDFIRE
    assert map_disaster_type("LaNdSlIdE") == DisasterType.LANDSLIDE


def test_disaster_type_mapping_normal():
    """Verify 'normal' maps to None (no disaster)."""
    assert map_disaster_type("normal") is None


def test_disaster_type_mapping_invalid():
    """Verify unsupported types raise error."""
    with pytest.raises(ValueError):
        map_disaster_type("tornado")
    
    with pytest.raises(ValueError):
        map_disaster_type("hurricane")
    
    with pytest.raises(ValueError):
        map_disaster_type("unknown_disaster")


# ──────────────────────────────────────────────────────────────────────────────
# Test 5 — Normal Disaster Handling
# ──────────────────────────────────────────────────────────────────────────────


def test_normal_disaster_no_analysis(synthetic_ml_output, synthetic_georeferenced_raster):
    """Verify 'normal' disaster returns None (no analysis)."""
    ml_output = synthetic_ml_output.copy()
    ml_output["classification"]["disaster_type"] = "normal"
    
    binary_mask = np.zeros((512, 512), dtype=np.uint8)
    
    result = ml_output_to_analysis_input_with_mask(
        ml_output, binary_mask, synthetic_georeferenced_raster
    )
    
    assert result is None, "Normal disaster should not produce analysis input"


# ──────────────────────────────────────────────────────────────────────────────
# Test 6 — Binary Mask Conversion (0-1 preservation)
# ──────────────────────────────────────────────────────────────────────────────


def test_binary_mask_values_preserved(temp_dir, synthetic_georeferenced_raster):
    """Verify binary mask values 0 and 1 are preserved in GeoTIFF."""
    # Create a mask with 0s and 1s
    binary_mask = np.zeros((32, 32), dtype=np.uint8)
    binary_mask[10:20, 10:20] = 1  # Create a 10x10 disaster zone
    
    analysis_id = "test_mask_001"
    
    mask_path = mask_to_geotiff(binary_mask, synthetic_georeferenced_raster, analysis_id)
    
    # Read back and verify
    with rasterio.open(mask_path) as src:
        read_mask = src.read(1)
        assert read_mask.dtype == np.uint8
        assert np.all((read_mask == 0) | (read_mask == 1))
        assert read_mask[10:20, 10:20].all()  # Disaster zone
        assert not read_mask[:10, :10].any()  # No disaster outside zone


# ──────────────────────────────────────────────────────────────────────────────
# Test 7 — GeoTIFF Creation and Metadata
# ──────────────────────────────────────────────────────────────────────────────


def test_geotiff_creation_basic(temp_dir, synthetic_georeferenced_raster):
    """Verify GeoTIFF is created with correct metadata."""
    binary_mask = np.zeros((32, 32), dtype=np.uint8)
    binary_mask[10:20, 10:20] = 1
    
    analysis_id = "test_geotiff_001"
    mask_path = mask_to_geotiff(binary_mask, synthetic_georeferenced_raster, analysis_id)
    
    # Verify file exists
    assert os.path.exists(mask_path)
    
    # Verify it's a valid raster
    with rasterio.open(mask_path) as src:
        assert src.width == 32
        assert src.height == 32
        assert src.count == 1
        assert src.crs is not None
        assert not src.transform.is_identity


def test_geotiff_crs_preserved(synthetic_georeferenced_raster):
    """Verify CRS is preserved from source raster."""
    binary_mask = np.zeros((32, 32), dtype=np.uint8)
    
    analysis_id = "test_crs_001"
    mask_path = mask_to_geotiff(binary_mask, synthetic_georeferenced_raster, analysis_id)
    
    # Read source CRS
    with rasterio.open(synthetic_georeferenced_raster) as src_src:
        source_crs = src_src.crs
    
    # Verify generated mask has same CRS
    with rasterio.open(mask_path) as dst_src:
        assert dst_src.crs == source_crs


def test_geotiff_transform_valid(synthetic_georeferenced_raster):
    """Verify affine transform is valid and not identity."""
    binary_mask = np.ones((32, 32), dtype=np.uint8)
    
    analysis_id = "test_transform_001"
    mask_path = mask_to_geotiff(binary_mask, synthetic_georeferenced_raster, analysis_id)
    
    with rasterio.open(mask_path) as src:
        assert not src.transform.is_identity
        # Verify transform elements are reasonable (not all zero)
        assert src.transform.a != 0  # pixel width
        assert src.transform.e != 0  # pixel height


# ──────────────────────────────────────────────────────────────────────────────
# Test 8 — Geographic Extent Preservation
# ──────────────────────────────────────────────────────────────────────────────


def test_geographic_extent_preserved(synthetic_georeferenced_raster):
    """Verify generated mask bounds match source raster bounds."""
    binary_mask = np.ones((64, 64), dtype=np.uint8)
    
    # Get source bounds
    with rasterio.open(synthetic_georeferenced_raster) as src:
        source_bounds = src.bounds
    
    # Create mask and check bounds
    analysis_id = "test_extent_001"
    mask_path = mask_to_geotiff(binary_mask, synthetic_georeferenced_raster, analysis_id)
    
    with rasterio.open(mask_path) as dst:
        dst_bounds = dst.bounds
        
        # Bounds should be approximately equal
        # (allowing for floating point precision)
        assert abs(dst_bounds.left - source_bounds.left) < 0.001
        assert abs(dst_bounds.bottom - source_bounds.bottom) < 0.001
        assert abs(dst_bounds.right - source_bounds.right) < 0.001
        assert abs(dst_bounds.top - source_bounds.top) < 0.001


# ──────────────────────────────────────────────────────────────────────────────
# Test 9 — Rasterio Compatibility
# ──────────────────────────────────────────────────────────────────────────────


def test_geotiff_rasterio_readable(synthetic_georeferenced_raster):
    """Verify generated GeoTIFF can be read back by rasterio."""
    binary_mask = np.random.randint(0, 2, (48, 48), dtype=np.uint8)
    
    analysis_id = "test_rasterio_001"
    mask_path = mask_to_geotiff(binary_mask, synthetic_georeferenced_raster, analysis_id)
    
    # Should not raise
    with rasterio.open(mask_path) as src:
        read_data = src.read(1)
        assert read_data.shape == binary_mask.shape


# ──────────────────────────────────────────────────────────────────────────────
# Test 10 — Invalid CRS Error
# ──────────────────────────────────────────────────────────────────────────────


def test_missing_crs_error(temp_dir):
    """Verify error when source raster lacks CRS."""
    # Create raster without CRS
    bad_raster_path = temp_dir / "no_crs.tif"
    data = np.ones((10, 10), dtype=np.uint8)
    
    with rasterio.open(
        str(bad_raster_path),
        'w',
        driver='GTiff',
        height=10,
        width=10,
        count=1,
        dtype=rasterio.uint8,
        # Note: no CRS specified
    ) as dst:
        dst.write(data, 1)
    
    binary_mask = np.zeros((32, 32), dtype=np.uint8)
    
    with pytest.raises(APIError) as exc_info:
        mask_to_geotiff(binary_mask, str(bad_raster_path), "test_no_crs")
    
    assert "CRS" in str(exc_info.value).upper()


# ──────────────────────────────────────────────────────────────────────────────
# Test 11 — Invalid Transform Error
# ──────────────────────────────────────────────────────────────────────────────


def test_missing_transform_error(temp_dir):
    """Verify error when source raster lacks transform."""
    # Create raster without transform
    bad_raster_path = temp_dir / "no_transform.tif"
    data = np.ones((10, 10), dtype=np.uint8)
    
    with rasterio.open(
        str(bad_raster_path),
        'w',
        driver='GTiff',
        height=10,
        width=10,
        count=1,
        dtype=rasterio.uint8,
        crs="EPSG:4326",
        # Note: no transform specified
    ) as dst:
        dst.write(data, 1)
    
    binary_mask = np.zeros((32, 32), dtype=np.uint8)
    
    with pytest.raises(APIError) as exc_info:
        mask_to_geotiff(binary_mask, str(bad_raster_path), "test_no_transform")
    
    assert "transform" in str(exc_info.value).lower()


# ──────────────────────────────────────────────────────────────────────────────
# Test 12 — ML Output Integration
# ──────────────────────────────────────────────────────────────────────────────


def test_ml_output_integration(synthetic_ml_output, synthetic_georeferenced_raster):
    """Verify complete conversion from ML output to MLAnalysisInput."""
    binary_mask = np.zeros((512, 512), dtype=np.uint8)
    binary_mask[100:200, 100:200] = 1
    
    result = ml_output_to_analysis_input_with_mask(
        synthetic_ml_output,
        binary_mask,
        synthetic_georeferenced_raster
    )
    
    assert result is not None
    analysis_input, mask_path = result
    
    # Verify MLAnalysisInput fields
    assert analysis_input.analysis_id is not None
    assert len(analysis_input.analysis_id) == 32
    assert analysis_input.disaster_type == DisasterType.FLOOD
    assert analysis_input.confidence == 0.94
    assert analysis_input.severity == 0.85
    assert analysis_input.affected_area_km2 == 0.0  # Placeholder
    assert analysis_input.mask_path == mask_path
    
    # Verify mask file exists
    assert os.path.exists(mask_path)


def test_ml_output_confidence_validation(synthetic_ml_output, synthetic_georeferenced_raster):
    """Verify confidence is validated."""
    # Create invalid ML output with confidence > 1
    bad_output = synthetic_ml_output.copy()
    bad_output["classification"]["confidence"] = 1.5
    
    binary_mask = np.zeros((512, 512), dtype=np.uint8)
    
    with pytest.raises(ValueError):
        ml_output_to_analysis_input_with_mask(
            bad_output, binary_mask, synthetic_georeferenced_raster
        )


def test_ml_output_failed_inference(synthetic_georeferenced_raster):
    """Verify error when ML inference failed."""
    bad_output = {"success": False, "error": "ML model error"}
    binary_mask = np.zeros((512, 512), dtype=np.uint8)
    
    with pytest.raises(APIError) as exc_info:
        ml_output_to_analysis_input_with_mask(
            bad_output, binary_mask, synthetic_georeferenced_raster
        )
    
    assert "failed" in str(exc_info.value).lower()


# ──────────────────────────────────────────────────────────────────────────────
# Test 13 — Invalid Mask Type
# ──────────────────────────────────────────────────────────────────────────────


def test_invalid_mask_type(synthetic_ml_output, synthetic_georeferenced_raster):
    """Verify error for non-array mask."""
    with pytest.raises(ValueError):
        ml_output_to_analysis_input_with_mask(
            synthetic_ml_output,
            "not_a_numpy_array",  # Invalid
            synthetic_georeferenced_raster
        )


def test_invalid_mask_dimensions(synthetic_ml_output, synthetic_georeferenced_raster):
    """Verify error for wrong mask dimensions."""
    bad_mask = np.zeros((512, 512, 3))  # 3D instead of 2D
    
    with pytest.raises(ValueError):
        ml_output_to_analysis_input_with_mask(
            synthetic_ml_output,
            bad_mask,
            synthetic_georeferenced_raster
        )


# ──────────────────────────────────────────────────────────────────────────────
# Test 14 — File Naming and Uniqueness
# ──────────────────────────────────────────────────────────────────────────────


def test_generated_mask_file_naming(synthetic_georeferenced_raster):
    """Verify generated mask files use analysis ID and are unique."""
    binary_mask = np.zeros((32, 32), dtype=np.uint8)
    
    analysis_id_1 = "analysis_12345"
    analysis_id_2 = "analysis_67890"
    
    path_1 = mask_to_geotiff(binary_mask, synthetic_georeferenced_raster, analysis_id_1)
    path_2 = mask_to_geotiff(binary_mask, synthetic_georeferenced_raster, analysis_id_2)
    
    # Verify they're different files
    assert path_1 != path_2
    assert "12345" in path_1
    assert "67890" in path_2


# ──────────────────────────────────────────────────────────────────────────────
# Test 15 — Geospatial Data Accuracy
# ──────────────────────────────────────────────────────────────────────────────


def test_geospatial_accuracy_multiple_disasters(synthetic_georeferenced_raster):
    """Verify multiple disaster regions are preserved correctly."""
    binary_mask = np.zeros((64, 64), dtype=np.uint8)
    
    # Create two separate disaster zones
    binary_mask[10:20, 10:20] = 1  # Zone 1
    binary_mask[40:50, 40:50] = 1  # Zone 2
    
    analysis_id = "test_multi_disaster"
    mask_path = mask_to_geotiff(binary_mask, synthetic_georeferenced_raster, analysis_id)
    
    with rasterio.open(mask_path) as src:
        read_mask = src.read(1)
        
        # Verify both zones are preserved
        assert read_mask[10:20, 10:20].all()
        assert read_mask[40:50, 40:50].all()
        
        # Verify no disaster areas are zero
        assert not read_mask[0:5, 0:5].any()
        assert not read_mask[25:35, 25:35].any()
