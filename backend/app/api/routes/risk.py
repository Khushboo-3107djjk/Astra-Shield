"""
Risk calculation and zone-level analysis endpoints.
Development endpoints for the deterministic risk engine and zone-level risk assessment.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.risk import RiskInput, RiskAssessment, RiskBreakdown, RiskFactor
from app.schemas.zone import RiskZone
from app.schemas.geometry import GeoJSONGeometry, GeometryType
from app.services.risk_service import calculate_risk
from app.services import zone_service
from app.services import geo_service
from app.api.errors import APIError
import os

router = APIRouter()


@router.post(
    "/calculate",
    response_model=RiskAssessment,
    summary="Calculate risk score (development endpoint)",
    description=(
        "Accepts four normalized risk factors (0–1) and returns an explainable "
        "risk assessment including risk score (0–10), priority category, and a "
        "per-factor breakdown. "
        "**Disclaimer:** The weighting and priority thresholds are prototype design "
        "choices for this hackathon and are NOT an official disaster-risk standard."
    ),
    tags=["Risk Engine"],
)
def calculate_risk_endpoint(risk_input: RiskInput) -> RiskAssessment:
    try:
        result = calculate_risk(
            flood_severity=risk_input.flood_severity,
            building_exposure=risk_input.building_exposure,
            road_disruption=risk_input.road_disruption,
            critical_facility_exposure=risk_input.critical_facility_exposure,
        )
    except ValueError as e:
        raise APIError(str(e), status_code=422)

    bd = result["breakdown"]
    return RiskAssessment(
        normalized_risk=result["normalized_risk"],
        risk_score=result["risk_score"],
        priority=result["priority"],
        weights=result["weights"],
        breakdown=RiskBreakdown(
            flood_severity=RiskFactor(**bd["flood_severity"]),
            building_exposure=RiskFactor(**bd["building_exposure"]),
            road_disruption=RiskFactor(**bd["road_disruption"]),
            critical_facility_exposure=RiskFactor(**bd["critical_facility_exposure"]),
        ),
    )


class ZoneRiskResponse(BaseModel):
    """Response containing all zones with risk assessment."""
    zones: List[RiskZone] = Field(..., description="List of risk zones sorted by risk_score descending")
    total_zones: int = Field(..., description="Total number of zones generated")
    highest_risk_zone_id: Optional[str] = Field(None, description="Zone ID with highest risk score")
    highest_risk_score: float = Field(..., description="Highest risk score among all zones")


@router.post(
    "/zones",
    response_model=ZoneRiskResponse,
    summary="Calculate zone-level risk (development endpoint)",
    description=(
        "Generates a deterministic regular grid of zones over the flood-affected area, "
        "calculates zone-level risk for each zone, and returns them sorted by risk score. "
        "This is a development endpoint for testing zone-based risk aggregation. "
        "**Development Use Only:** Uses synthetic test data. "
        "**Disclaimer:** The weighting and priority thresholds are prototype design "
        "choices for this hackathon and are NOT an official disaster-risk standard."
    ),
    tags=["Risk Engine - Zone Analysis"],
)
def calculate_zones_endpoint() -> ZoneRiskResponse:
    """
    Calculate zone-level risk for the synthetic flood scenario.

    Uses:
    - tests/data/test_flood_mask.tif
    - tests/data/test_buildings.geojson
    - tests/data/test_roads.geojson
    - tests/data/test_critical_facilities.geojson

    Returns sorted zones with complete risk assessment.
    """
    # Path to test data (relative to backend root)
    flood_mask_path = os.path.join("tests", "data", "test_flood_mask.tif")
    buildings_path = os.path.join("tests", "data", "test_buildings.geojson")
    roads_path = os.path.join("tests", "data", "test_roads.geojson")
    facilities_path = os.path.join("tests", "data", "test_critical_facilities.geojson")

    try:
        # Process flood mask to get geometry
        flood_result = geo_service.process_flood_mask(flood_mask_path)
    except APIError as e:
        raise APIError(f"Failed to process flood mask: {str(e)}", status_code=400)

    flood_geometry = flood_result["geometry"]
    if flood_geometry is None:
        raise APIError("Flood geometry is empty or invalid", status_code=400)

    # Convert GeoJSONGeometry back to Shapely geometry
    flood_crs = flood_result["crs"]

    # Import needed for geometry conversion
    from shapely.geometry import shape

    # Build GeoJSON dict from schema
    flood_geojson_dict = {
        "type": flood_geometry.type,
        "coordinates": flood_geometry.coordinates,
    }
    flood_shapely = shape(flood_geojson_dict)

    try:
        # Calculate zones with risk
        zones_result = zone_service.calculate_zones_with_risk(
            flood_geometry=flood_shapely,
            flood_crs=flood_crs,
            buildings_source=buildings_path,
            roads_source=roads_path,
            facilities_source=facilities_path,
        )
    except Exception as e:
        raise APIError(f"Failed to calculate zones: {str(e)}", status_code=500)

    # Format zones into RiskZone schema
    formatted_zones = []
    for zone_dict in zones_result["zones"]:
        zone_geom = zone_dict["geometry"]

        # Convert Shapely geometry to GeoJSONGeometry
        if zone_geom.geom_type == "Polygon":
            coords = [list(zone_geom.exterior.coords)]
            for interior in zone_geom.interiors:
                coords.append(list(interior.coords))
        else:
            # Should not happen with regular grid, but handle it
            coords = []

        geojson_geom = GeoJSONGeometry(
            type=GeometryType("Polygon"),
            coordinates=coords,
        ) if coords else None

        # Build risk breakdown from zone breakdown
        bd = zone_dict["risk_breakdown"]
        risk_breakdown = RiskBreakdown(
            flood_severity=RiskFactor(**bd["flood_severity"]),
            building_exposure=RiskFactor(**bd["building_exposure"]),
            road_disruption=RiskFactor(**bd["road_disruption"]),
            critical_facility_exposure=RiskFactor(**bd["critical_facility_exposure"]),
        )

        zone_obj = RiskZone(
            zone_id=zone_dict["zone_id"],
            geometry=geojson_geom,
            flood_severity=zone_dict["flood_severity"],
            building_exposure=zone_dict["building_exposure"],
            road_disruption=zone_dict["road_disruption"],
            critical_facility_exposure=zone_dict["critical_facility_exposure"],
            risk_score=zone_dict["risk_score"],
            priority=zone_dict["priority"],
            risk_breakdown=risk_breakdown,
            affected_buildings=zone_dict["affected_buildings"],
            affected_road_length_km=zone_dict["affected_road_length_km"],
            affected_facilities=zone_dict["affected_facilities"],
        )
        formatted_zones.append(zone_obj)

    return ZoneRiskResponse(
        zones=formatted_zones,
        total_zones=zones_result["total_zones"],
        highest_risk_zone_id=zones_result["highest_risk_zone_id"],
        highest_risk_score=zones_result["highest_risk_score"],
    )
