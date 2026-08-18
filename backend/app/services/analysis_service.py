"""
ASTRA-SHIELD Analysis Orchestration Service
==============================================
Orchestrates the complete end-to-end analysis workflow.

Architecture:
    Analysis Request
            ↓
    analysis_service (orchestration)
            ↓
    geo_service (flood processing)
    building_service (impact analysis)
    road_service (impact analysis)
    infrastructure_service (impact analysis)
    risk_service (risk calculation)
    zone_service (zone generation & aggregation)
            ↓
    Complete AnalysisResponse

Key Principle:
- Services do NOT call each other
- analysis_service coordinates all service calls
- API route delegates to analysis_service
- Each service is independently testable
"""

from typing import Dict, List, Optional
from shapely.geometry import shape
from app.services import (
    geo_service,
    building_service,
    road_service,
    infrastructure_service,
    risk_service,
    zone_service,
)
from app.schemas.analysis import (
    MLAnalysisInput,
    AnalysisResponse,
    AnalysisSummary,
)
from app.schemas.impact import ImpactSummary
from app.schemas.risk import RiskSummary, RiskBreakdown, RiskFactor
from app.schemas.zone import RiskZone
from app.schemas.geometry import GeoJSONGeometry, GeometryType
from app.api.errors import APIError

# ──────────────────────────────────────────────────────────────────────────────
# Development configuration
# ──────────────────────────────────────────────────────────────────────────────

# For Part 6A: Point to synthetic test data
# Real integration will use actual paths from ML pipeline in Part 6B
TEST_BUILDINGS_PATH = "tests/data/test_buildings.geojson"
TEST_ROADS_PATH = "tests/data/test_roads.geojson"
TEST_FACILITIES_PATH = "tests/data/test_critical_facilities.geojson"


def analyze_synthetic_disaster(analysis_input: MLAnalysisInput) -> AnalysisResponse:
    """
    Execute complete end-to-end disaster analysis workflow.

    This is the main orchestration function that coordinates all service calls.

    For Part 6A: Uses synthetic development/test data.
    For Part 6B: Will integrate with real ML pipeline.

    Args:
        analysis_input: MLAnalysisInput with analysis parameters

    Returns:
        Complete AnalysisResponse with all analysis results

    Raises:
        APIError: If any service call fails
    """

    # ──────────────────────────────────────────────────────────────────────────
    # 1. FLOOD PROCESSING
    # ──────────────────────────────────────────────────────────────────────────

    try:
        flood_result = geo_service.process_flood_mask(analysis_input.mask_path)
    except Exception as e:
        raise APIError(f"Flood processing failed: {str(e)}", status_code=400)

    flood_geom_schema = flood_result["geometry"]
    if flood_geom_schema is None:
        raise APIError("Flood geometry is empty or invalid", status_code=400)

    flood_crs = flood_result["crs"]
    affected_area_km2_calculated = flood_result["affected_area_km2"]

    # Convert GeoJSONGeometry back to Shapely for downstream processing
    flood_dict = {
        "type": flood_geom_schema.type,
        "coordinates": flood_geom_schema.coordinates,
    }
    flood_shapely = shape(flood_dict)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. BUILDING IMPACT ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    try:
        building_result = building_service.analyze_building_impact(
            flood_geometry=flood_shapely,
            flood_crs=flood_crs,
            buildings_source=TEST_BUILDINGS_PATH,
        )
    except Exception as e:
        raise APIError(f"Building impact analysis failed: {str(e)}", status_code=500)

    affected_buildings = building_result["affected_buildings"]
    total_buildings = building_result["total_buildings"]
    building_exposure = (
        affected_buildings / total_buildings if total_buildings > 0 else 0.0
    )

    # ──────────────────────────────────────────────────────────────────────────
    # 3. ROAD IMPACT ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    try:
        road_result = road_service.analyze_road_impact(
            flood_geometry=flood_shapely,
            flood_crs=flood_crs,
            roads_source=TEST_ROADS_PATH,
        )
    except Exception as e:
        raise APIError(f"Road impact analysis failed: {str(e)}", status_code=500)

    affected_road_length_km = road_result["affected_road_length_km"]
    total_road_length_km = road_result["total_road_length_km"]
    road_disruption = (
        affected_road_length_km / total_road_length_km
        if total_road_length_km > 0
        else 0.0
    )
    affected_road_segments = road_result["affected_road_segments"]

    # ──────────────────────────────────────────────────────────────────────────
    # 4. CRITICAL INFRASTRUCTURE IMPACT ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    try:
        facility_result = infrastructure_service.analyze_infrastructure_impact(
            flood_geometry=flood_shapely,
            flood_crs=flood_crs,
            facilities_source=TEST_FACILITIES_PATH,
        )
    except Exception as e:
        raise APIError(
            f"Critical infrastructure analysis failed: {str(e)}", status_code=500
        )

    affected_facilities = facility_result["affected_facilities"]
    total_facilities = facility_result["total_facilities"]
    facility_exposure = (
        affected_facilities / total_facilities if total_facilities > 0 else 0.0
    )

    # ──────────────────────────────────────────────────────────────────────────
    # 5. OVERALL RISK CALCULATION
    # ──────────────────────────────────────────────────────────────────────────

    try:
        risk_result = risk_service.calculate_risk(
            flood_severity=analysis_input.severity,  # From ML model
            building_exposure=building_exposure,
            road_disruption=road_disruption,
            critical_facility_exposure=facility_exposure,
        )
    except ValueError as e:
        raise APIError(f"Risk calculation failed: {str(e)}", status_code=422)

    overall_risk_score = risk_result["risk_score"]
    overall_priority = risk_result["priority"]

    # ──────────────────────────────────────────────────────────────────────────
    # 6. ZONE-LEVEL ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    try:
        zones_result = zone_service.calculate_zones_with_risk(
            flood_geometry=flood_shapely,
            flood_crs=flood_crs,
            buildings_source=TEST_BUILDINGS_PATH,
            roads_source=TEST_ROADS_PATH,
            facilities_source=TEST_FACILITIES_PATH,
        )
    except Exception as e:
        raise APIError(f"Zone analysis failed: {str(e)}", status_code=500)

    # ──────────────────────────────────────────────────────────────────────────
    # 7. BUILD RESPONSE OBJECTS
    # ──────────────────────────────────────────────────────────────────────────

    # Summary
    summary = AnalysisSummary(
        analysis_id=analysis_input.analysis_id,
        disaster_type=analysis_input.disaster_type,
        location="Development Test Area (Synthetic Data)",
        confidence=analysis_input.confidence,
        severity=analysis_input.severity,
        affected_area_km2=affected_area_km2_calculated,  # Use calculated, not client-supplied
    )

    # Impact
    impact = ImpactSummary(
        affected_buildings=affected_buildings,
        affected_roads=affected_road_segments,
        affected_critical_facilities=affected_facilities,
    )

    # Risk
    risk_summary = RiskSummary(
        overall_risk_score=overall_risk_score,
        overall_priority=overall_priority,
    )

    # Zones - convert from zone_service format to RiskZone schema
    formatted_zones: List[RiskZone] = []
    for zone_dict in zones_result["zones"]:
        zone_geom = zone_dict["geometry"]

        # Convert Shapely geometry to GeoJSONGeometry
        if zone_geom.geom_type == "Polygon":
            coords = [list(zone_geom.exterior.coords)]
            for interior in zone_geom.interiors:
                coords.append(list(interior.coords))
        else:
            coords = []

        geojson_geom = (
            GeoJSONGeometry(
                type=GeometryType("Polygon"),
                coordinates=coords,
            )
            if coords
            else None
        )

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

    # ──────────────────────────────────────────────────────────────────────────
    # 8. FINAL RESPONSE
    # ──────────────────────────────────────────────────────────────────────────

    response = AnalysisResponse(
        summary=summary,
        impact=impact,
        risk=risk_summary,
        zones=formatted_zones,
        timeline=[],  # Part 6A: No temporal analysis yet
    )

    return response


# ──────────────────────────────────────────────────────────────────────────────
# GENERIC ANALYSIS FUNCTION FOR PART 6B (ML INTEGRATION)
# ──────────────────────────────────────────────────────────────────────────────


def analyze_disaster(
    analysis_input: MLAnalysisInput,
    buildings_source: str = TEST_BUILDINGS_PATH,
    roads_source: str = TEST_ROADS_PATH,
    facilities_source: str = TEST_FACILITIES_PATH,
    location_name: str = "Disaster Area",
) -> AnalysisResponse:
    """
    Execute complete end-to-end disaster analysis workflow with configurable infrastructure data.

    This generic function allows real ML output (Part 6B) to be analyzed using
    any infrastructure data source, not just the Part 6A synthetic test data.

    Args:
        analysis_input: MLAnalysisInput with analysis parameters
        buildings_source: Path to buildings GeoJSON (default: test data)
        roads_source: Path to roads GeoJSON (default: test data)
        facilities_source: Path to facilities GeoJSON (default: test data)
        location_name: Name of the disaster location for display (default: "Disaster Area")

    Returns:
        Complete AnalysisResponse with all analysis results

    Raises:
        APIError: If any service call fails
    """

    # ──────────────────────────────────────────────────────────────────────────
    # 1. FLOOD PROCESSING
    # ──────────────────────────────────────────────────────────────────────────

    try:
        flood_result = geo_service.process_flood_mask(analysis_input.mask_path)
    except Exception as e:
        raise APIError(f"Flood processing failed: {str(e)}", status_code=400)

    flood_geom_schema = flood_result["geometry"]
    if flood_geom_schema is None:
        raise APIError("Flood geometry is empty or invalid", status_code=400)

    flood_crs = flood_result["crs"]
    affected_area_km2_calculated = flood_result["affected_area_km2"]

    # Convert GeoJSONGeometry back to Shapely for downstream processing
    flood_dict = {
        "type": flood_geom_schema.type,
        "coordinates": flood_geom_schema.coordinates,
    }
    flood_shapely = shape(flood_dict)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. BUILDING IMPACT ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    try:
        building_result = building_service.analyze_building_impact(
            flood_geometry=flood_shapely,
            flood_crs=flood_crs,
            buildings_source=buildings_source,
        )
    except Exception as e:
        raise APIError(f"Building impact analysis failed: {str(e)}", status_code=500)

    affected_buildings = building_result["affected_buildings"]
    total_buildings = building_result["total_buildings"]
    building_exposure = (
        affected_buildings / total_buildings if total_buildings > 0 else 0.0
    )

    # ──────────────────────────────────────────────────────────────────────────
    # 3. ROAD IMPACT ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    try:
        road_result = road_service.analyze_road_impact(
            flood_geometry=flood_shapely,
            flood_crs=flood_crs,
            roads_source=roads_source,
        )
    except Exception as e:
        raise APIError(f"Road impact analysis failed: {str(e)}", status_code=500)

    affected_road_length_km = road_result["affected_road_length_km"]
    total_road_length_km = road_result["total_road_length_km"]
    road_disruption = (
        affected_road_length_km / total_road_length_km
        if total_road_length_km > 0
        else 0.0
    )
    affected_road_segments = road_result["affected_road_segments"]

    # ──────────────────────────────────────────────────────────────────────────
    # 4. CRITICAL INFRASTRUCTURE IMPACT ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    try:
        facility_result = infrastructure_service.analyze_infrastructure_impact(
            flood_geometry=flood_shapely,
            flood_crs=flood_crs,
            facilities_source=facilities_source,
        )
    except Exception as e:
        raise APIError(
            f"Critical infrastructure analysis failed: {str(e)}", status_code=500
        )

    affected_facilities = facility_result["affected_facilities"]
    total_facilities = facility_result["total_facilities"]
    facility_exposure = (
        affected_facilities / total_facilities if total_facilities > 0 else 0.0
    )

    # ──────────────────────────────────────────────────────────────────────────
    # 5. OVERALL RISK CALCULATION
    # ──────────────────────────────────────────────────────────────────────────

    try:
        risk_result = risk_service.calculate_risk(
            flood_severity=analysis_input.severity,
            building_exposure=building_exposure,
            road_disruption=road_disruption,
            critical_facility_exposure=facility_exposure,
        )
    except ValueError as e:
        raise APIError(f"Risk calculation failed: {str(e)}", status_code=422)

    overall_risk_score = risk_result["risk_score"]
    overall_priority = risk_result["priority"]

    # ──────────────────────────────────────────────────────────────────────────
    # 6. ZONE-LEVEL ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    try:
        zones_result = zone_service.calculate_zones_with_risk(
            flood_geometry=flood_shapely,
            flood_crs=flood_crs,
            buildings_source=buildings_source,
            roads_source=roads_source,
            facilities_source=facilities_source,
        )
    except Exception as e:
        raise APIError(f"Zone analysis failed: {str(e)}", status_code=500)

    # ──────────────────────────────────────────────────────────────────────────
    # 7. BUILD RESPONSE OBJECTS
    # ──────────────────────────────────────────────────────────────────────────

    # Summary
    summary = AnalysisSummary(
        analysis_id=analysis_input.analysis_id,
        disaster_type=analysis_input.disaster_type,
        location=location_name,
        confidence=analysis_input.confidence,
        severity=analysis_input.severity,
        affected_area_km2=affected_area_km2_calculated,  # Use geo_service calculated area
    )

    # Impact
    impact = ImpactSummary(
        affected_buildings=affected_buildings,
        affected_roads=affected_road_segments,
        affected_critical_facilities=affected_facilities,
    )

    # Risk
    risk_summary = RiskSummary(
        overall_risk_score=overall_risk_score,
        overall_priority=overall_priority,
    )

    # Zones - convert from zone_service format to RiskZone schema
    formatted_zones: List[RiskZone] = []
    for zone_dict in zones_result["zones"]:
        zone_geom = zone_dict["geometry"]

        # Convert Shapely geometry to GeoJSONGeometry
        if zone_geom.geom_type == "Polygon":
            coords = [list(zone_geom.exterior.coords)]
            for interior in zone_geom.interiors:
                coords.append(list(interior.coords))
        else:
            coords = []

        geojson_geom = (
            GeoJSONGeometry(
                type=GeometryType("Polygon"),
                coordinates=coords,
            )
            if coords
            else None
        )

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

    # ──────────────────────────────────────────────────────────────────────────
    # 8. FINAL RESPONSE
    # ──────────────────────────────────────────────────────────────────────────

    response = AnalysisResponse(
        summary=summary,
        impact=impact,
        risk=risk_summary,
        zones=formatted_zones,
        timeline=[],
    )

    return response
