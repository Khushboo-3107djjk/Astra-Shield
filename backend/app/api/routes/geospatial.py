from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from shapely.geometry import shape
from app.schemas.geometry import GeoJSONGeometry
from app.services.geo_service import process_flood_mask
from app.services.building_service import analyze_building_impact

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

class BuildingAnalysisRequest(BaseModel):
    flood_geometry: dict = Field(..., description="Flood polygon GeoJSON geometry")
    flood_crs: str = Field(..., description="CRS of the flood geometry")
    buildings_path: str = Field(..., description="Path to the buildings GeoJSON file")

class AffectedBuilding(BaseModel):
    building_id: str
    geometry: GeoJSONGeometry

class BuildingAnalysisResponse(BaseModel):
    total_buildings: int
    affected_buildings: int
    affected_percentage: float
    affected_building_ids: List[str]
    affected_buildings_geometry: List[AffectedBuilding]

@router.post(
    "/analyze-buildings",
    response_model=BuildingAnalysisResponse,
    summary="Development Test Endpoint for Building Impact",
    description="Development endpoint to test computing which buildings intersect the flood geometry."
)
def analyze_buildings(request: BuildingAnalysisRequest):
    # Convert GeoJSON dict to shapely geometry
    flood_geom = shape(request.flood_geometry)
    
    result = analyze_building_impact(flood_geom, request.flood_crs, request.buildings_path)
    return BuildingAnalysisResponse(**result)
