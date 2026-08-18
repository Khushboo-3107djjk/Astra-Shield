"""
ASTRA-SHIELD Zone Service
=========================
Deterministic geographic zone generation and zone-level risk aggregation.

Strategy:
    1. Generate regular deterministic grid over flood bounding box
    2. Keep only cells that intersect flood polygon
    3. Calculate zone-level factors (flood severity, building exposure, etc.)
    4. Reuse existing risk_service for consistent risk calculation
    5. Return ranked zones by risk score

Architecture:
    Flood geometry + Infrastructure data
            ↓
    Regular grid zone generation
            ↓
    Spatial intersection filtering
            ↓
    Zone-level factor aggregation
            ↓
    Existing risk_service (deterministic weights)
            ↓
    ZoneRiskAssessment collection
"""

from typing import List, Dict, Optional, Tuple
import geopandas as gpd
import numpy as np
from shapely.geometry import box, Polygon
from shapely.geometry.base import BaseGeometry
from app.api.errors import APIError
from app.services import risk_service
from app.services import building_service
from app.services import road_service
from app.services import infrastructure_service
from app.schemas.geometry import GeoJSONGeometry, GeometryType

# ──────────────────────────────────────────────────────────────────────────────
# Zone generation configuration
# ──────────────────────────────────────────────────────────────────────────────
GRID_ROWS: int = 4
GRID_COLUMNS: int = 4


def generate_zones(
    flood_geometry: BaseGeometry,
    flood_crs: str,
    grid_rows: int = GRID_ROWS,
    grid_columns: int = GRID_COLUMNS,
) -> List[Dict]:
    """
    Generate a deterministic regular grid of zones that intersect the flood polygon.

    Args:
        flood_geometry: Shapely geometry of flood polygon
        flood_crs: CRS of flood geometry
        grid_rows: Number of rows in grid (default 4)
        grid_columns: Number of columns in grid (default 4)

    Returns:
        List of zone dicts with zone_id, geometry, and intersects flag
    """
    if flood_geometry.is_empty:
        return []

    # Get bounding box
    minx, miny, maxx, maxy = flood_geometry.bounds

    # Calculate cell dimensions
    cell_width = (maxx - minx) / grid_columns
    cell_height = (maxy - miny) / grid_rows

    # Generate grid cells
    zones = []
    zone_counter = 1

    for row in range(grid_rows):
        for col in range(grid_columns):
            # Calculate cell bounds
            x_min = minx + col * cell_width
            x_max = x_min + cell_width
            y_min = miny + row * cell_height
            y_max = y_min + cell_height

            # Create cell polygon
            cell_geometry = box(x_min, y_min, x_max, y_max)

            # Check intersection with flood polygon
            if cell_geometry.intersects(flood_geometry):
                zone_id = f"Z{zone_counter:03d}"
                zones.append({
                    "zone_id": zone_id,
                    "geometry": cell_geometry,
                    "row": row,
                    "col": col,
                    "cell_width": cell_width,
                    "cell_height": cell_height,
                })
                zone_counter += 1

    return zones


def calculate_zone_flood_severity(
    zone_geometry: BaseGeometry,
    flood_geometry: BaseGeometry,
    zone_crs: str,
) -> float:
    """
    Calculate normalized flood severity for a zone.

    Severity = (zone ∩ flood area) / zone area

    Uses projected CRS to calculate areas correctly (not in degrees).

    Args:
        zone_geometry: Grid cell geometry
        flood_geometry: Flood polygon geometry
        zone_crs: CRS string of both geometries

    Returns:
        Normalized severity [0, 1]
    """
    if zone_geometry.is_empty:
        return 0.0

    # Create GeoDataFrame to leverage projected CRS
    gdf = gpd.GeoDataFrame({"geometry": [zone_geometry]}, crs=zone_crs)

    # Project to equal-area projection for accurate calculation
    gdf_equal_area = gdf.to_crs("EPSG:6933")
    zone_area_m2 = gdf_equal_area.geometry.iloc[0].area

    if zone_area_m2 <= 0:
        return 0.0

    # Calculate intersection area
    intersection = zone_geometry.intersection(flood_geometry)

    if intersection.is_empty:
        return 0.0

    # Project intersection to equal-area CRS
    gdf_inter = gpd.GeoDataFrame({"geometry": [intersection]}, crs=zone_crs)
    gdf_inter_equal = gdf_inter.to_crs("EPSG:6933")
    intersection_area_m2 = gdf_inter_equal.geometry.iloc[0].area

    # Calculate normalized severity
    severity = min(1.0, intersection_area_m2 / zone_area_m2)
    return round(severity, 6)


def calculate_zone_building_exposure(
    zone_geometry: BaseGeometry,
    zone_crs: str,
    buildings_source,
) -> float:
    """
    Calculate building exposure for a zone.

    Exposure = affected_buildings_in_zone / total_buildings_in_zone

    Args:
        zone_geometry: Grid cell geometry
        zone_crs: CRS string
        buildings_source: Path or GeoDataFrame

    Returns:
        Normalized exposure [0, 1]
    """
    try:
        result = building_service.analyze_building_impact(
            flood_geometry=zone_geometry,
            flood_crs=zone_crs,
            buildings_source=buildings_source,
        )
    except APIError:
        return 0.0

    total = result["total_buildings"]
    affected = result["affected_buildings"]

    if total == 0:
        return 0.0

    exposure = affected / total
    return round(min(1.0, exposure), 6)


def calculate_zone_road_disruption(
    zone_geometry: BaseGeometry,
    zone_crs: str,
    roads_source,
) -> float:
    """
    Calculate road disruption for a zone.

    Disruption = affected_road_length / total_road_length_in_zone

    Args:
        zone_geometry: Grid cell geometry
        zone_crs: CRS string
        roads_source: Path or GeoDataFrame

    Returns:
        Normalized disruption [0, 1]
    """
    try:
        result = road_service.analyze_road_impact(
            flood_geometry=zone_geometry,
            flood_crs=zone_crs,
            roads_source=roads_source,
        )
    except APIError:
        return 0.0

    total_length = result["total_road_length_km"]
    affected_length = result["affected_road_length_km"]

    if total_length == 0:
        return 0.0

    disruption = affected_length / total_length
    return round(min(1.0, disruption), 6)


def calculate_zone_facility_exposure(
    zone_geometry: BaseGeometry,
    zone_crs: str,
    facilities_source,
) -> float:
    """
    Calculate critical facility exposure for a zone.

    Exposure = affected_facilities / total_facilities_in_zone

    Args:
        zone_geometry: Grid cell geometry
        zone_crs: CRS string
        facilities_source: Path or GeoDataFrame

    Returns:
        Normalized exposure [0, 1]
    """
    try:
        result = infrastructure_service.analyze_infrastructure_impact(
            flood_geometry=zone_geometry,
            flood_crs=zone_crs,
            facilities_source=facilities_source,
        )
    except APIError:
        return 0.0

    total = result["total_facilities"]
    affected = result["affected_facilities"]

    if total == 0:
        return 0.0

    exposure = affected / total
    return round(min(1.0, exposure), 6)


def calculate_zone_impacts(
    zone_geometry: BaseGeometry,
    zone_crs: str,
    buildings_source,
    roads_source,
    facilities_source,
) -> Dict:
    """
    Calculate impact counts for a zone.

    Returns:
        Dict with affected_buildings, affected_road_length_km, affected_facilities
    """
    impacts = {
        "affected_buildings": 0,
        "affected_road_length_km": 0.0,
        "affected_facilities": 0,
    }

    try:
        b_result = building_service.analyze_building_impact(
            flood_geometry=zone_geometry,
            flood_crs=zone_crs,
            buildings_source=buildings_source,
        )
        impacts["affected_buildings"] = b_result["affected_buildings"]
    except APIError:
        pass

    try:
        r_result = road_service.analyze_road_impact(
            flood_geometry=zone_geometry,
            flood_crs=zone_crs,
            roads_source=roads_source,
        )
        impacts["affected_road_length_km"] = round(r_result["affected_road_length_km"], 4)
    except APIError:
        pass

    try:
        f_result = infrastructure_service.analyze_infrastructure_impact(
            flood_geometry=zone_geometry,
            flood_crs=zone_crs,
            facilities_source=facilities_source,
        )
        impacts["affected_facilities"] = f_result["affected_facilities"]
    except APIError:
        pass

    return impacts


def calculate_zones_with_risk(
    flood_geometry: BaseGeometry,
    flood_crs: str,
    buildings_source,
    roads_source,
    facilities_source,
    grid_rows: int = GRID_ROWS,
    grid_columns: int = GRID_COLUMNS,
) -> Dict:
    """
    Generate zones and calculate risk for each zone.

    This is the main entry point for zone-level analysis.

    Args:
        flood_geometry: Shapely geometry of flood
        flood_crs: CRS string
        buildings_source: Path or GeoDataFrame
        roads_source: Path or GeoDataFrame
        facilities_source: Path or GeoDataFrame
        grid_rows: Number of grid rows
        grid_columns: Number of grid columns

    Returns:
        Dict containing:
            - zones: List of zone risk assessments (sorted by risk_score desc)
            - total_zones: Count of zones
            - highest_risk_zone_id: Zone with highest risk
            - highest_risk_score: Highest risk score
    """
    # Generate zones
    zones_list = generate_zones(
        flood_geometry=flood_geometry,
        flood_crs=flood_crs,
        grid_rows=grid_rows,
        grid_columns=grid_columns,
    )

    if not zones_list:
        return {
            "zones": [],
            "total_zones": 0,
            "highest_risk_zone_id": None,
            "highest_risk_score": 0.0,
        }

    # Calculate risk for each zone
    zone_assessments = []

    for zone_dict in zones_list:
        zone_id = zone_dict["zone_id"]
        zone_geometry = zone_dict["geometry"]

        # Calculate factors
        flood_severity = calculate_zone_flood_severity(
            zone_geometry=zone_geometry,
            flood_geometry=flood_geometry,
            zone_crs=flood_crs,
        )

        building_exposure = calculate_zone_building_exposure(
            zone_geometry=zone_geometry,
            zone_crs=flood_crs,
            buildings_source=buildings_source,
        )

        road_disruption = calculate_zone_road_disruption(
            zone_geometry=zone_geometry,
            zone_crs=flood_crs,
            roads_source=roads_source,
        )

        facility_exposure = calculate_zone_facility_exposure(
            zone_geometry=zone_geometry,
            zone_crs=flood_crs,
            facilities_source=facilities_source,
        )

        # Calculate risk using existing risk service
        risk_result = risk_service.calculate_risk(
            flood_severity=flood_severity,
            building_exposure=building_exposure,
            road_disruption=road_disruption,
            critical_facility_exposure=facility_exposure,
        )

        # Get impact counts
        impacts = calculate_zone_impacts(
            zone_geometry=zone_geometry,
            zone_crs=flood_crs,
            buildings_source=buildings_source,
            roads_source=roads_source,
            facilities_source=facilities_source,
        )

        # Build zone assessment
        zone_assessment = {
            "zone_id": zone_id,
            "geometry": zone_geometry,
            "flood_severity": flood_severity,
            "building_exposure": building_exposure,
            "road_disruption": road_disruption,
            "critical_facility_exposure": facility_exposure,
            "risk_score": risk_result["risk_score"],
            "priority": risk_result["priority"],
            "risk_breakdown": risk_result["breakdown"],
            "weights": risk_result["weights"],
            "affected_buildings": impacts["affected_buildings"],
            "affected_road_length_km": impacts["affected_road_length_km"],
            "affected_facilities": impacts["affected_facilities"],
        }

        zone_assessments.append(zone_assessment)

    # Sort by risk_score descending, then zone_id ascending (deterministic tie-breaker)
    zone_assessments.sort(
        key=lambda z: (-z["risk_score"], z["zone_id"])
    )

    # Identify highest-risk zone
    highest_risk_zone_id = zone_assessments[0]["zone_id"] if zone_assessments else None
    highest_risk_score = zone_assessments[0]["risk_score"] if zone_assessments else 0.0

    return {
        "zones": zone_assessments,
        "total_zones": len(zone_assessments),
        "highest_risk_zone_id": highest_risk_zone_id,
        "highest_risk_score": round(highest_risk_score, 2),
    }
