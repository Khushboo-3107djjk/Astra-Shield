import os
import geopandas as gpd
from shapely.geometry.base import BaseGeometry
from app.api.errors import APIError
from app.schemas.geometry import GeoJSONGeometry, GeometryType

SUPPORTED_FACILITY_TYPES = {"hospital", "school", "emergency"}


def analyze_infrastructure_impact(flood_geometry: BaseGeometry, flood_crs: str, facilities_source):
    """
    Analyzes which critical facilities are potentially affected by a flood polygon.

    A facility is considered potentially affected when its geometry intersects
    the detected flood polygon. Spatial overlap does NOT imply structural damage
    or destruction — it only establishes potential spatial exposure.
    """
    if isinstance(facilities_source, str):
        if not os.path.exists(facilities_source):
            raise APIError(f"Facility data file not found: {facilities_source}", status_code=404)
        try:
            gdf = gpd.read_file(facilities_source)
        except Exception as e:
            raise APIError(f"Failed to read facility data: {str(e)}", status_code=400)
    elif isinstance(facilities_source, gpd.GeoDataFrame):
        gdf = facilities_source.copy()
    else:
        raise APIError("Invalid facility source format.", status_code=400)

    if len(gdf) == 0:
        return _empty_response()

    if not gdf.crs:
        raise APIError("Facility dataset is missing CRS.", status_code=400)

    # Reproject if CRS does not match flood CRS
    if gdf.crs.to_string() != flood_crs and gdf.crs != flood_crs:
        gdf = gdf.to_crs(flood_crs)

    if not gdf.is_valid.all():
        raise APIError("Facility dataset contains invalid geometries.", status_code=400)

    # Ensure required columns
    if 'facility_id' not in gdf.columns:
        gdf['facility_id'] = [f"F_{i}" for i in range(len(gdf))]
    if 'facility_name' not in gdf.columns:
        gdf['facility_name'] = gdf['facility_id']
    if 'facility_type' not in gdf.columns:
        gdf['facility_type'] = "unknown"

    total_facilities = len(gdf)

    # Spatial intersection: a facility is potentially affected if it intersects the flood polygon
    affected_mask = gdf.intersects(flood_geometry)
    affected_gdf = gdf[affected_mask]

    affected_count = len(affected_gdf)
    affected_percentage = round((affected_count / total_facilities) * 100, 2) if total_facilities > 0 else 0.0

    affected_facility_ids = affected_gdf['facility_id'].astype(str).tolist()

    # Build facility-type summary
    type_summary = {}
    for ftype in SUPPORTED_FACILITY_TYPES:
        ftype_total = len(gdf[gdf['facility_type'] == ftype])
        ftype_affected = len(affected_gdf[affected_gdf['facility_type'] == ftype])
        type_summary[ftype + "s"] = {"total": ftype_total, "affected": ftype_affected}

    # Build detail list for affected facilities
    affected_details = []
    for _, row in affected_gdf.iterrows():
        geom = row.geometry
        if geom.geom_type != "Point":
            raise APIError(
                f"Unsupported geometry type '{geom.geom_type}' for facility {row['facility_id']}. Expected Point.",
                status_code=400
            )
        affected_details.append({
            "facility_id": str(row['facility_id']),
            "facility_name": str(row['facility_name']),
            "facility_type": str(row['facility_type']),
            "geometry": GeoJSONGeometry(
                type=GeometryType("Point"),
                coordinates=list(geom.coords[0])
            ).model_dump()
        })

    return {
        "total_facilities": total_facilities,
        "affected_facilities": affected_count,
        "affected_percentage": affected_percentage,
        "affected_facility_ids": affected_facility_ids,
        "facility_type_summary": type_summary,
        "affected_facility_details": affected_details,
    }


def _empty_response():
    return {
        "total_facilities": 0,
        "affected_facilities": 0,
        "affected_percentage": 0.0,
        "affected_facility_ids": [],
        "facility_type_summary": {
            "hospitals": {"total": 0, "affected": 0},
            "schools": {"total": 0, "affected": 0},
            "emergencys": {"total": 0, "affected": 0},
        },
        "affected_facility_details": [],
    }
