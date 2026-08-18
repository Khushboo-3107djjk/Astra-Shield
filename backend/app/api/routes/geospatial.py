from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from shapely.geometry import shape
from app.schemas.geometry import GeoJSONGeometry
from app.services.geo_service import process_flood_mask
from app.services.building_service import analyze_building_impact
from app.services.road_service import analyze_road_impact
from app.services.infrastructure_service import analyze_infrastructure_impact

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
    flood_geom = shape(request.flood_geometry)
    result = analyze_building_impact(flood_geom, request.flood_crs, request.buildings_path)
    return BuildingAnalysisResponse(**result)

class RoadAnalysisRequest(BaseModel):
    flood_geometry: dict = Field(..., description="Flood polygon GeoJSON geometry")
    flood_crs: str = Field(..., description="CRS of the flood geometry")
    roads_path: str = Field(..., description="Path to the roads GeoJSON file")

class RoadStats(BaseModel):
    total_segments: int
    affected_segments: int
    affected_length_km: float

class AffectedRoadDetail(BaseModel):
    road_id: str
    road_type: str
    total_length_km: float
    affected_length_km: float
    geometry: GeoJSONGeometry

class RoadAnalysisResponse(BaseModel):
    total_road_segments: int
    affected_road_segments: int
    affected_percentage: float
    total_road_length_km: float
    affected_road_length_km: float
    affected_road_ids: List[str]
    major_roads: RoadStats
    minor_roads: RoadStats
    affected_road_details: List[AffectedRoadDetail]

@router.post(
    "/analyze-roads",
    response_model=RoadAnalysisResponse,
    summary="Development Test Endpoint for Road Impact",
    description="Development endpoint to test computing which roads intersect the flood geometry and their lengths."
)
def analyze_roads(request: RoadAnalysisRequest):
    flood_geom = shape(request.flood_geometry)
    result = analyze_road_impact(flood_geom, request.flood_crs, request.roads_path)
    return RoadAnalysisResponse(**result)


class InfrastructureAnalysisRequest(BaseModel):
    flood_geometry: dict = Field(..., description="Flood polygon GeoJSON geometry")
    flood_crs: str = Field(..., description="CRS of the flood geometry")
    facilities_path: str = Field(..., description="Path to the critical facilities GeoJSON file")


class FacilityTypeStat(BaseModel):
    total: int
    affected: int


class AffectedFacilityDetail(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    geometry: GeoJSONGeometry


class InfrastructureAnalysisResponse(BaseModel):
    total_facilities: int
    affected_facilities: int
    affected_percentage: float
    affected_facility_ids: List[str]
    facility_type_summary: Dict[str, FacilityTypeStat]
    affected_facility_details: List[AffectedFacilityDetail]


@router.post(
    "/analyze-infrastructure",
    response_model=InfrastructureAnalysisResponse,
    summary="Development Test Endpoint for Critical Infrastructure Impact",
    description=(
        "Development endpoint to identify which critical facilities (hospitals, schools, emergency) "
        "are potentially affected by a flood. Spatial overlap does NOT imply structural damage."
    )
)
def analyze_infrastructure(request: InfrastructureAnalysisRequest):
    flood_geom = shape(request.flood_geometry)
    result = analyze_infrastructure_impact(flood_geom, request.flood_crs, request.facilities_path)
    return InfrastructureAnalysisResponse(**result)
