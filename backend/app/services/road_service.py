import os
import geopandas as gpd
from shapely.geometry.base import BaseGeometry
from app.api.errors import APIError
from app.schemas.geometry import GeoJSONGeometry, GeometryType

def analyze_road_impact(flood_geometry: BaseGeometry, flood_crs: str, roads_source):
    """
    Analyzes which road segments are affected by a flood polygon.
    An affected road is one whose geometry intersects the flood polygon.
    Calculates affected lengths correctly in kilometers using metric projections.
    """
    if isinstance(roads_source, str):
        if not os.path.exists(roads_source):
            raise APIError(f"Road data file not found: {roads_source}", status_code=404)
        try:
            gdf = gpd.read_file(roads_source)
        except Exception as e:
            raise APIError(f"Failed to read road data: {str(e)}", status_code=400)
    elif isinstance(roads_source, gpd.GeoDataFrame):
        gdf = roads_source.copy()
    else:
        raise APIError("Invalid road source format.", status_code=400)

    if len(gdf) == 0:
        return _empty_road_response()

    if not gdf.crs:
        raise APIError("Road dataset is missing CRS.", status_code=400)

    # Transform roads to flood CRS before intersection
    if gdf.crs.to_string() != flood_crs and gdf.crs != flood_crs:
        gdf = gdf.to_crs(flood_crs)

    if not gdf.is_valid.all():
        raise APIError("Road dataset contains invalid geometries.", status_code=400)

    # Ensure required columns
    if 'road_id' not in gdf.columns:
        gdf['road_id'] = [f"R_{i}" for i in range(len(gdf))]
    if 'road_type' not in gdf.columns:
        gdf['road_type'] = "minor"

    # Compute total length for all roads using an estimated UTM CRS for metric accuracy
    utm_crs = gdf.estimate_utm_crs()
    gdf_utm = gdf.to_crs(utm_crs)
    gdf['total_length_km'] = gdf_utm.geometry.length / 1000.0
    
    total_road_length_km = gdf['total_length_km'].sum()
    total_road_segments = len(gdf)

    # Intersection mask
    affected_mask = gdf.intersects(flood_geometry)
    affected_gdf = gdf[affected_mask].copy()

    affected_road_segments = len(affected_gdf)
    affected_percentage = round((affected_road_segments / total_road_segments) * 100, 2) if total_road_segments > 0 else 0.0
    
    affected_road_details = []
    affected_road_ids = []
    affected_length_sum = 0.0
    
    stats = {
        "major": {"total_segments": len(gdf[gdf['road_type'] == 'major']), "affected_segments": 0, "affected_length_km": 0.0},
        "minor": {"total_segments": len(gdf[gdf['road_type'] == 'minor']), "affected_segments": 0, "affected_length_km": 0.0}
    }
    
    for _, row in affected_gdf.iterrows():
        geom = row.geometry
        r_type = row['road_type'] if row['road_type'] in stats else 'minor'
        r_id = str(row['road_id'])
        
        # Calculate strictly the intersected portion geometry
        intersected_geom = geom.intersection(flood_geometry)
        
        # Calculate metric length of the intersected portion
        gdf_single = gpd.GeoDataFrame({'geometry': [intersected_geom]}, crs=flood_crs)
        gdf_single_utm = gdf_single.to_crs(utm_crs)
        aff_length = gdf_single_utm.geometry.length.iloc[0] / 1000.0
        
        affected_length_sum += aff_length
        stats[r_type]["affected_segments"] += 1
        stats[r_type]["affected_length_km"] += aff_length
        affected_road_ids.append(r_id)
        
        # Build GeoJSON geometry output for the intersected portion
        g_type = intersected_geom.geom_type
        if g_type == "LineString":
            coords = list(intersected_geom.coords)
        elif g_type == "MultiLineString":
            coords = [list(line.coords) for line in intersected_geom.geoms]
        elif g_type == "GeometryCollection":
            # Extract LineStrings from collection if point/line mix occurs
            coords = []
            g_type = "MultiLineString"
            for g in intersected_geom.geoms:
                if g.geom_type == "LineString":
                    coords.append(list(g.coords))
        else:
            continue # Non-line intersection (e.g. just a Point touching edge)

        affected_road_details.append({
            "road_id": r_id,
            "road_type": r_type,
            "total_length_km": round(row['total_length_km'], 4),
            "affected_length_km": round(aff_length, 4),
            "geometry": GeoJSONGeometry(
                type=GeometryType(g_type),
                coordinates=coords
            ).model_dump()
        })

    stats["major"]["affected_length_km"] = round(stats["major"]["affected_length_km"], 4)
    stats["minor"]["affected_length_km"] = round(stats["minor"]["affected_length_km"], 4)
    
    return {
        "total_road_segments": total_road_segments,
        "affected_road_segments": affected_road_segments,
        "affected_percentage": affected_percentage,
        "total_road_length_km": round(total_road_length_km, 4),
        "affected_road_length_km": round(affected_length_sum, 4),
        "affected_road_ids": affected_road_ids,
        "major_roads": stats["major"],
        "minor_roads": stats["minor"],
        "affected_road_details": affected_road_details
    }

def _empty_road_response():
    return {
        "total_road_segments": 0,
        "affected_road_segments": 0,
        "affected_percentage": 0.0,
        "total_road_length_km": 0.0,
        "affected_road_length_km": 0.0,
        "affected_road_ids": [],
        "major_roads": {"total_segments": 0, "affected_segments": 0, "affected_length_km": 0.0},
        "minor_roads": {"total_segments": 0, "affected_segments": 0, "affected_length_km": 0.0},
        "affected_road_details": []
    }
