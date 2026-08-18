from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.geometry import GeoJSONGeometry
from app.services.geo_service import process_flood_mask

router = APIRouter()

class MaskAnalysisRequest(BaseModel):
    mask_path: str = Field(..., description="Path to the raster mask file")

class MaskAnalysisResponse(BaseModel):
    affected_area_km2: float = Field(..., description="Calculated area of the flood mask in square kilometers")
    flood_pixel_count: int = Field(..., description="Number of flood pixels detected in the mask")
    geometry: Optional[GeoJSONGeometry] = Field(None, description="Extracted geographic polygons")
    crs: str = Field(..., description="Coordinate Reference System of the input mask")

@router.post(
    "/analyze-mask", 
    response_model=MaskAnalysisResponse,
    summary="Development Test Endpoint for Mask Processing",
    description="Development endpoint to test turning a flood mask into vector geometries and area."
)
def analyze_mask(request: MaskAnalysisRequest):
    result = process_flood_mask(request.mask_path)
    return MaskAnalysisResponse(**result)
