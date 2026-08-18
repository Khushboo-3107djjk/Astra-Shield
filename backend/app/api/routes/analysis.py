"""
POST /api/analyze — End-to-end disaster analysis endpoint
"""

import os
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File
from app.schemas.analysis import (
    MLAnalysisInput,
    AnalysisResponse,
    AnalysisSummary,
    DisasterType,
)
from app.schemas.impact import ImpactSummary
from app.schemas.risk import RiskSummary
from app.services.analysis_service import analyze_synthetic_disaster, analyze_disaster
from app.services.ml_integration_service import analyze_satellite_image
from app.api.errors import APIError

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Run complete disaster analysis",
    description=(
        "Receives ML analysis input and returns a complete integrated disaster analysis "
        "including flood processing, building/road/facility impact, risk assessment, "
        "and zone-level analysis. "
        "**Part 6A Development:** Uses synthetic test data. "
        "**Real ML Integration:** Will be implemented in Part 6B."
    ),
)
def run_analysis(input_data: MLAnalysisInput) -> AnalysisResponse:
    """
    Executes the complete end-to-end analysis workflow.

    Orchestration flow:
    1. Process flood mask to extract geometry and affected area
    2. Analyze building impact on flood area
    3. Analyze road disruption on flood area
    4. Analyze critical infrastructure exposure
    5. Calculate overall risk using weighted factors
    6. Generate deterministic geographic zones with risk scores
    7. Return complete analysis response

    Args:
        input_data: MLAnalysisInput from Person 1's ML pipeline

    Returns:
        AnalysisResponse with summary, impact, risk, zones, and timeline

    Raises:
        APIError: If any service call fails
    """
    try:
        result = analyze_synthetic_disaster(input_data)
    except APIError:
        raise
    except Exception as e:
        raise APIError(
            f"Analysis workflow failed: {str(e)}", status_code=500
        )

    return result


# ──────────────────────────────────────────────────────────────────────────────
# PART 6B — REAL ML INTEGRATION ENDPOINT
# ──────────────────────────────────────────────────────────────────────────────


@router.post(
    "/analyze/image",
    response_model=AnalysisResponse,
    summary="Real ML satellite image analysis",
    description=(
        "Accepts a satellite image, runs ML inference, converts the mask to GeoTIFF, "
        "and performs complete geospatial disaster analysis. "
        "**Input:** Georeferenced GeoTIFF with CRS and spatial transform. "
        "**Output:** Complete disaster analysis with infrastructure impact and risk assessment. "
        "**Part 6B:** Real ML integration with georeferenced satellite data."
    ),
)
async def analyze_satellite_image_endpoint(file: UploadFile = File(...)) -> AnalysisResponse:
    """
    Executes complete ML → Backend disaster analysis workflow.

    Accepts a satellite image, runs ML inference, and returns integrated analysis.

    Orchestration flow:
    1. Save uploaded satellite image
    2. Run ML inference (classification + segmentation)
    3. Extract binary segmentation mask
    4. Convert mask to georeferenced GeoTIFF
    5. Read geospatial metadata from source image
    6. Process flood mask (geo_service)
    7. Analyze building/road/facility impact
    8. Calculate overall risk
    9. Generate zones
    10. Return complete AnalysisResponse

    Args:
        file: Uploaded satellite image file (GeoTIFF, PNG, or JPG)
             Recommended: Georeferenced GeoTIFF with CRS and spatial transform

    Returns:
        AnalysisResponse with complete analysis including:
        - Analysis summary (disaster type, confidence, severity)
        - Infrastructure impact (buildings, roads, facilities)
        - Risk assessment (overall score and priority)
        - Geographic risk zones

    Raises:
        APIError: If upload validation, ML inference, geospatial processing, or analysis fails

    Note:
        Generated segmentation masks are stored in backend/generated_masks/ for audit trails.
        Infrastructure data is synthetic development/test data.
    """
    
    # ──────────────────────────────────────────────────────────────────────────
    # 1. VALIDATE UPLOAD
    # ──────────────────────────────────────────────────────────────────────────
    
    if not file:
        raise APIError("No file provided", status_code=400)
    
    if not file.filename:
        raise APIError("File has no name", status_code=400)
    
    # Validate file extension
    allowed_extensions = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise APIError(
            f"Unsupported file type: {file_ext}. "
            f"Supported types: {', '.join(allowed_extensions)}",
            status_code=400
        )
    
    # ──────────────────────────────────────────────────────────────────────────
    # 2. SAVE UPLOADED FILE
    # ──────────────────────────────────────────────────────────────────────────
    
    temp_dir = Path(tempfile.gettempdir()) / "astra_shield_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate server-side filename (don't trust user input)
    from uuid import uuid4
    safe_filename = f"satellite_{uuid4().hex}{file_ext}"
    input_path = temp_dir / safe_filename
    
    try:
        with open(input_path, "wb") as f:
            contents = await file.read()
            if not contents:
                raise APIError("Uploaded file is empty", status_code=400)
            f.write(contents)
    except Exception as e:
        raise APIError(
            f"Failed to save uploaded file: {str(e)}",
            status_code=500
        )
    
    # ──────────────────────────────────────────────────────────────────────────
    # 3. VALIDATE GEOSPATIAL METADATA
    # ──────────────────────────────────────────────────────────────────────────
    
    if file_ext in [".tif", ".tiff"]:
        # For GeoTIFF, validate CRS and transform
        try:
            import rasterio
            with rasterio.open(str(input_path)) as src:
                if not src.crs:
                    raise APIError(
                        "Source raster is missing CRS (Coordinate Reference System). "
                        "Geospatial analysis requires georeferenced input.",
                        status_code=400
                    )
                if not src.transform or src.transform.is_identity:
                    raise APIError(
                        "Source raster is missing spatial transform. "
                        "Geospatial analysis requires valid affine transform.",
                        status_code=400
                    )
        except rasterio.errors.RasterioIOError:
            raise APIError(
                "Cannot read raster file. Verify it is a valid GeoTIFF.",
                status_code=400
            )
        except APIError:
            raise
        except Exception as e:
            raise APIError(
                f"Geospatial metadata validation failed: {str(e)}",
                status_code=400
            )
    else:
        # PNG/JPG without embedded geospatial metadata cannot produce geographically valid results
        raise APIError(
            f"File type '{file_ext}' does not support embedded geospatial metadata. "
            "Use georeferenced GeoTIFF (.tif) for geographic flood analysis.",
            status_code=400
        )
    
    # ──────────────────────────────────────────────────────────────────────────
    # 4. RUN ML INFERENCE
    # ──────────────────────────────────────────────────────────────────────────
    
    try:
        ml_result = analyze_satellite_image(str(input_path))
    except APIError:
        raise
    except Exception as e:
        raise APIError(
            f"ML analysis failed: {str(e)}",
            status_code=500
        )
    
    # Handle "no disaster detected"
    if ml_result is None:
        # Return minimal response with no disaster
        from uuid import uuid4
        no_disaster_id = uuid4().hex
        return AnalysisResponse(
            summary=AnalysisSummary(
                analysis_id=no_disaster_id,
                disaster_type=DisasterType.FLOOD,  # Placeholder; use FLOOD for undetected
                location="Analysis Area",
                confidence=0.0,
                severity=0.0,
                affected_area_km2=0.0,
            ),
            impact=ImpactSummary(
                affected_buildings=0,
                affected_roads=0,
                affected_critical_facilities=0,
            ),
            risk=RiskSummary(
                overall_risk_score=0.0,
                overall_priority="LOW",
            ),
            zones=[],
            timeline=[],
        )
    
    analysis_input, mask_path, ml_output = ml_result
    
    # ──────────────────────────────────────────────────────────────────────────
    # 5. RUN BACKEND ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────
    
    try:
        result = analyze_disaster(
            analysis_input=analysis_input,
            location_name=f"Satellite Analysis {analysis_input.disaster_type.value}",
        )
    except APIError:
        raise
    except Exception as e:
        raise APIError(
            f"Backend analysis failed: {str(e)}",
            status_code=500
        )
    
    # ──────────────────────────────────────────────────────────────────────────
    # 6. CLEANUP
    # ──────────────────────────────────────────────────────────────────────────
    
    try:
        input_path.unlink()  # Delete temporary input file
    except Exception:
        pass  # Ignore cleanup errors
    
    return result
