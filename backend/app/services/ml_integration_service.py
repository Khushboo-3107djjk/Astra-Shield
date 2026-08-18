"""
ML Integration Service — Adapter between ML pipeline and backend analysis

This service bridges the ML inference output with the backend analysis pipeline.

Responsibilities:
1. Normalize ML severity [0,10] → [0,1]
2. Generate unique analysis IDs
3. Map disaster types
4. Convert binary segmentation masks to georeferenced GeoTIFFs
5. Preserve CRS and spatial transforms
6. Build MLAnalysisInput from ML output
7. Handle "normal" (no disaster) cases
"""

import os
import tempfile
from pathlib import Path
from uuid import uuid4
from typing import Dict, Optional, Tuple
import numpy as np
import rasterio
from rasterio.transform import from_bounds

from app.schemas.analysis import MLAnalysisInput, DisasterType, AnalysisResponse
from app.api.errors import APIError


# ──────────────────────────────────────────────────────────────────────────────
# Generated Mask Storage Configuration
# ──────────────────────────────────────────────────────────────────────────────

GENERATED_MASKS_DIR = Path(__file__).parent.parent.parent / "generated_masks"


def ensure_masks_directory():
    """Ensure the generated masks directory exists."""
    GENERATED_MASKS_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# 1. SEVERITY NORMALIZATION
# ──────────────────────────────────────────────────────────────────────────────


def normalize_severity(ml_severity: float) -> float:
    """
    Normalize ML severity from [0, 10] to [0, 1] range.

    ML produces severity as percentage-based [0, 10] score.
    Backend expects normalized [0, 1] range for MLAnalysisInput.

    Values slightly outside the expected range are clamped to protect against
    floating-point drift or near-boundary model outputs.

    Args:
        ml_severity: Severity score from ML segmentation [0, 10]

    Returns:
        Normalized severity [0, 1]

    Raises:
        ValueError: If severity is outside a safe tolerance band
    """
    if not isinstance(ml_severity, (int, float)):
        raise ValueError(f"Severity must be numeric, got {type(ml_severity)}")

    # Allow small numeric drift around the expected range but reject clearly
    # invalid values such as -1 or 11.
    if ml_severity < -0.1 or ml_severity > 10.1:
        raise ValueError(
            f"ML severity out of expected range [0, 10]: {ml_severity}"
        )

    normalized = max(0.0, min(10.0, ml_severity)) / 10.0
    return normalized


# ──────────────────────────────────────────────────────────────────────────────
# 2. ANALYSIS ID GENERATION
# ──────────────────────────────────────────────────────────────────────────────


def generate_analysis_id() -> str:
    """
    Generate a unique, collision-safe analysis ID.
    
    Uses UUID4 for guaranteed uniqueness.
    
    Returns:
        Unique analysis ID (hex string, 32 chars)
    """
    return uuid4().hex


# ──────────────────────────────────────────────────────────────────────────────
# 3. DISASTER TYPE MAPPING
# ──────────────────────────────────────────────────────────────────────────────


def map_disaster_type(ml_disaster_type: str) -> Optional[DisasterType]:
    """
    Map ML disaster type string to backend DisasterType enum.
    
    ML produces lowercase strings: "flood", "wildfire", "landslide", "normal"
    Backend supports: FLOOD, WILDFIRE, CYCLONE, LANDSLIDE, EARTHQUAKE, DROUGHT
    
    Args:
        ml_disaster_type: Disaster type from ML classifier (lowercase)
    
    Returns:
        DisasterType enum or None if disaster is "normal"
    
    Raises:
        ValueError: If disaster type is unsupported
    """
    ml_type_lower = ml_disaster_type.lower().strip()
    
    # Mapping from ML output to backend enum
    type_mapping = {
        "flood": DisasterType.FLOOD,
        "wildfire": DisasterType.WILDFIRE,
        "landslide": DisasterType.LANDSLIDE,
    }
    
    if ml_type_lower == "normal":
        return None  # No disaster detected
    
    if ml_type_lower not in type_mapping:
        raise ValueError(
            f"Unsupported disaster type: {ml_disaster_type}. "
            f"Supported types: {list(type_mapping.keys())}"
        )
    
    return type_mapping[ml_type_lower]


# ──────────────────────────────────────────────────────────────────────────────
# 4. BINARY MASK TO GEOREFERENCED GEOTIFF CONVERSION
# ──────────────────────────────────────────────────────────────────────────────


def mask_to_geotiff(
    binary_mask: np.ndarray,
    source_raster_path: str,
    analysis_id: str,
) -> str:
    """
    Convert binary segmentation mask to georeferenced GeoTIFF.
    
    The ML pipeline resizes images to 512×512, so the mask is 512×512.
    This function creates a GeoTIFF that maps the mask pixels to the
    original geographic extent.
    
    Args:
        binary_mask: Binary numpy array (H, W), values 0-1
        source_raster_path: Path to original source raster (must be GeoTIFF with CRS)
        analysis_id: Unique analysis ID for file naming
    
    Returns:
        Path to generated GeoTIFF mask
    
    Raises:
        APIError: If source raster is missing CRS/transform or other I/O issues
    """
    ensure_masks_directory()
    
    # Read source raster metadata
    try:
        with rasterio.open(source_raster_path) as src:
            if not src.crs:
                raise APIError(
                    "Source raster is missing CRS (Coordinate Reference System)",
                    status_code=400
                )
            if not src.transform or src.transform.is_identity:
                raise APIError(
                    "Source raster is missing spatial transform",
                    status_code=400
                )
            
            source_crs = src.crs
            source_bounds = src.bounds
            source_width = src.width
            source_height = src.height
    
    except rasterio.errors.RasterioIOError as e:
        raise APIError(
            f"Cannot read source raster: {str(e)}",
            status_code=400
        )
    
    # Create affine transform for the ML mask
    # The mask is 512×512, but must map to the original geographic bounds
    transform = from_bounds(
        source_bounds.left,
        source_bounds.bottom,
        source_bounds.right,
        source_bounds.top,
        binary_mask.shape[1],  # width (columns)
        binary_mask.shape[0]   # height (rows)
    )
    
    # Generate output path
    mask_filename = f"analysis_{analysis_id}_mask.tif"
    output_path = GENERATED_MASKS_DIR / mask_filename
    
    # Write GeoTIFF
    try:
        with rasterio.open(
            str(output_path),
            'w',
            driver='GTiff',
            height=binary_mask.shape[0],
            width=binary_mask.shape[1],
            count=1,
            dtype=binary_mask.dtype,
            crs=source_crs,
            transform=transform,
            compress='lzw',  # Compression for smaller file size
        ) as dst:
            dst.write(binary_mask, 1)
    
    except Exception as e:
        raise APIError(
            f"Failed to create georeferenced mask GeoTIFF: {str(e)}",
            status_code=500
        )
    
    # Verify the GeoTIFF was written correctly
    try:
        with rasterio.open(str(output_path)) as verify_src:
            if verify_src.crs != source_crs:
                raise APIError(
                    "Generated GeoTIFF CRS mismatch",
                    status_code=500
                )
            if verify_src.transform.is_identity:
                raise APIError(
                    "Generated GeoTIFF missing transform",
                    status_code=500
                )
    except Exception as e:
        raise APIError(
            f"GeoTIFF verification failed: {str(e)}",
            status_code=500
        )
    
    return str(output_path)


# ──────────────────────────────────────────────────────────────────────────────
# 5. ML OUTPUT TO MLANALYSISINPUT CONVERSION
# ──────────────────────────────────────────────────────────────────────────────


def ml_output_to_analysis_input(
    ml_output: Dict,
    source_raster_path: str,
) -> Optional[Tuple[MLAnalysisInput, str]]:
    """
    Convert ML pipeline output to backend MLAnalysisInput.
    
    This is the main adapter function that bridges ML and backend.
    
    Args:
        ml_output: Complete output from ml.inference.predict.DisasterAnalyzer.analyze()
        source_raster_path: Path to source satellite image (must be GeoTIFF)
    
    Returns:
        Tuple of (MLAnalysisInput, generated_mask_path) or None if no disaster
    
    Raises:
        APIError: If conversion fails or data is invalid
    """
    # Validate ML output structure
    if not ml_output.get("success"):
        raise APIError(
            f"ML inference failed: {ml_output.get('error', 'Unknown error')}",
            status_code=500
        )
    
    try:
        classification = ml_output["classification"]
        segmentation = ml_output["segmentation"]
        metrics = ml_output["metrics"]
    except KeyError as e:
        raise APIError(
            f"Malformed ML output: missing {e}",
            status_code=500
        )
    
    # 1. Map disaster type
    disaster_type = map_disaster_type(classification["disaster_type"])
    
    # If no disaster detected, return None
    if disaster_type is None:
        return None
    
    # 2. Extract and validate confidence
    confidence = float(classification["confidence"])
    if not (0 <= confidence <= 1):
        raise ValueError(f"Invalid confidence: {confidence}")
    
    # 3. Extract severity and normalize
    ml_severity = float(segmentation["severity_score"])
    severity = normalize_severity(ml_severity)
    
    # 4. Generate analysis ID
    analysis_id = generate_analysis_id()
    
    # 5. Get binary mask from metrics (affected pixels vs total)
    #    or extract from segmentation if available
    #    For now, we'll reconstruct from the ML output
    affected_pixels = int(metrics["affected_pixels"])
    total_pixels = int(metrics["total_pixels"])
    mask_shape = (int(np.sqrt(total_pixels)), int(np.sqrt(total_pixels)))
    
    # Create binary mask based on affected pixel count
    # Note: This is a simplified reconstruction. In production, we'd want
    # direct access to the binary mask from the ML inference.
    binary_mask = np.zeros(mask_shape, dtype=np.uint8)
    if affected_pixels > 0:
        # For this adapter, we trust the ML severity/affected_pixels
        # The mask itself needs to come from the ML segmentation
        # TODO: Modify predict.py to return the binary mask directly
        # For now, we'll create a placeholder and raise an error
        # because we cannot reliably reconstruct the mask from pixel counts alone
        raise APIError(
            "Binary mask reconstruction not available; "
            "ML pipeline must return the binary mask directly",
            status_code=500
        )
    
    # Convert mask to georeferenced GeoTIFF
    mask_path = mask_to_geotiff(binary_mask, source_raster_path, analysis_id)
    
    # 6. Build MLAnalysisInput
    analysis_input = MLAnalysisInput(
        analysis_id=analysis_id,
        disaster_type=disaster_type,
        confidence=confidence,
        severity=severity,
        affected_area_km2=0.0,  # Will be calculated by geo_service
        mask_path=mask_path,
    )
    
    return (analysis_input, mask_path)


# ──────────────────────────────────────────────────────────────────────────────
# 6. CONVERSION USING DIRECT BINARY MASK
# ──────────────────────────────────────────────────────────────────────────────


def ml_output_to_analysis_input_with_mask(
    ml_output: Dict,
    binary_mask: np.ndarray,
    source_raster_path: str,
) -> Optional[Tuple[MLAnalysisInput, str]]:
    """
    Convert ML pipeline output to backend MLAnalysisInput with explicit binary mask.
    
    This version requires the binary mask to be provided directly,
    avoiding reconstruction from pixel counts.
    
    Args:
        ml_output: Complete output from ml.inference.predict.DisasterAnalyzer.analyze()
        binary_mask: Binary numpy array (H, W) with values 0 (no disaster) and 1 (disaster)
        source_raster_path: Path to source satellite image (must be GeoTIFF)
    
    Returns:
        Tuple of (MLAnalysisInput, generated_mask_path) or None if no disaster
    
    Raises:
        APIError: If conversion fails or data is invalid
    """
    # Validate ML output structure
    if not ml_output.get("success"):
        raise APIError(
            f"ML inference failed: {ml_output.get('error', 'Unknown error')}",
            status_code=500
        )
    
    try:
        classification = ml_output["classification"]
        segmentation = ml_output["segmentation"]
    except KeyError as e:
        raise APIError(
            f"Malformed ML output: missing {e}",
            status_code=500
        )
    
    # Validate binary mask
    if not isinstance(binary_mask, np.ndarray):
        raise ValueError("Binary mask must be a numpy array")
    if binary_mask.ndim != 2:
        raise ValueError("Binary mask must be 2D (H, W)")
    if binary_mask.dtype != np.uint8:
        binary_mask = binary_mask.astype(np.uint8)
    
    # 1. Map disaster type
    disaster_type = map_disaster_type(classification["disaster_type"])
    
    # If no disaster detected, return None
    if disaster_type is None:
        return None
    
    # 2. Extract and validate confidence
    confidence = float(classification["confidence"])
    if not (0 <= confidence <= 1):
        raise ValueError(f"Invalid confidence: {confidence}")
    
    # 3. Extract severity and normalize
    ml_severity = float(segmentation["severity_score"])
    severity = normalize_severity(ml_severity)
    
    # 4. Generate analysis ID
    analysis_id = generate_analysis_id()
    
    # 5. Convert mask to georeferenced GeoTIFF
    mask_path = mask_to_geotiff(binary_mask, source_raster_path, analysis_id)
    
    # 6. Build MLAnalysisInput
    analysis_input = MLAnalysisInput(
        analysis_id=analysis_id,
        disaster_type=disaster_type,
        confidence=confidence,
        severity=severity,
        affected_area_km2=0.0,  # Will be calculated by geo_service
        mask_path=mask_path,
    )
    
    return (analysis_input, mask_path)


# ──────────────────────────────────────────────────────────────────────────────
# 7. END-TO-END ML INFERENCE INTEGRATION
# ──────────────────────────────────────────────────────────────────────────────


def analyze_satellite_image(
    source_image_path: str,
) -> Optional[Tuple[MLAnalysisInput, str, Dict]]:
    """
    Complete ML-to-backend workflow for satellite image analysis.
    
    This function:
    1. Calls the ML inference pipeline
    2. Extracts the binary mask and metadata
    3. Converts to georeferenced GeoTIFF
    4. Builds MLAnalysisInput
    5. Returns result for backend analysis
    
    Args:
        source_image_path: Path to source satellite image (must be GeoTIFF)
    
    Returns:
        Tuple of (MLAnalysisInput, generated_mask_path, ml_output_dict) or None if no disaster
    
    Raises:
        APIError: If ML inference or conversion fails
    """
    # Import ML pipeline
    try:
        from ml.inference.predict import DisasterAnalyzer
    except ImportError as e:
        raise APIError(
            f"ML pipeline not available: {str(e)}",
            status_code=500
        )
    
    # Run ML inference
    try:
        analyzer = DisasterAnalyzer(device='cpu')  # Use CPU for compatibility
        ml_output = analyzer.analyze(source_image_path, return_visualization=False)
    except Exception as e:
        raise APIError(
            f"ML inference failed: {str(e)}",
            status_code=500
        )
    
    if not ml_output.get("success"):
        raise APIError(
            f"ML analysis failed: {ml_output.get('error', 'Unknown error')}",
            status_code=500
        )
    
    # Extract binary mask from analyzer
    # The analyzer's predict method returns a binary mask before base64 encoding
    try:
        # Re-run to get the binary mask (this is inefficient but necessary
        # because the ML pipeline encodes the mask as base64)
        import torch
        from ml.preprocessing.preprocess import SatelliteImagePreprocessor
        
        preprocessor = SatelliteImagePreprocessor(img_size=512, normalize=True)
        image, _ = preprocessor.preprocess(source_image_path)
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0)
        
        segmenter = analyzer.segmenter
        binary_mask, seg_confidence = segmenter.predict(image_tensor, threshold=0.5)
        
    except Exception as e:
        raise APIError(
            f"Failed to extract segmentation mask: {str(e)}",
            status_code=500
        )
    
    # Convert to MLAnalysisInput
    result = ml_output_to_analysis_input_with_mask(
        ml_output,
        binary_mask,
        source_image_path
    )
    
    if result is None:
        # No disaster detected
        return None
    
    analysis_input, mask_path = result
    return (analysis_input, mask_path, ml_output)
