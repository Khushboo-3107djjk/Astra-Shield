import os
import geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.geometry.base import BaseGeometry
from app.api.errors import APIError
from app.schemas.geometry import GeoJSONGeometry, GeometryType

def analyze_building_impact(flood_geometry: BaseGeometry, flood_crs: str, buildings_source):
    """
    Analyzes which buildings are affected by a flood polygon.
    An affected building is defined as a building whose geometry intersects the flood polygon.
    """
    if isinstance(buildings_source, str):
        if not os.path.exists(buildings_source):
            raise APIError(f"Building data file not found: {buildings_source}", status_code=404)
        try:
            gdf = gpd.read_file(buildings_source)
        except Exception as e:
            raise APIError(f"Failed to read building data: {str(e)}", status_code=400)
    elif isinstance(buildings_source, gpd.GeoDataFrame):
        gdf = buildings_source.copy()
    else:
        raise APIError("Invalid building source format.", status_code=400)

    # Handle zero building case
    if len(gdf) == 0:
        return {
            "total_buildings": 0,
            "affected_buildings": 0,
            "affected_percentage": 0.0,
            "affected_building_ids": [],
            "affected_buildings_geometry": []
        }

    # Verify building dataset has CRS
    if not gdf.crs:
        raise APIError("Building dataset is missing CRS.", status_code=400)

    # Reproject building geometries if they don't match the flood CRS
    if gdf.crs.to_string() != flood_crs and gdf.crs != flood_crs:
        gdf = gdf.to_crs(flood_crs)

    # Drop invalid geometries (or we could attempt to fix them with buffer(0))
    if not gdf.is_valid.all():
        raise APIError("Building dataset contains invalid geometries.", status_code=400)

    # Ensure building_id column exists
    if 'building_id' not in gdf.columns:
        gdf['building_id'] = [f"B_{i}" for i in range(len(gdf))]

    # Spatial intersection: A building is affected if it intersects the flood polygon
    affected_mask = gdf.intersects(flood_geometry)
    affected_gdf = gdf[affected_mask]
    
    total_buildings = len(gdf)
    affected_buildings = len(affected_gdf)
    affected_percentage = round((affected_buildings / total_buildings) * 100, 2)
    
    affected_building_ids = affected_gdf['building_id'].astype(str).tolist()
    
    # Format geometries for output
    affected_buildings_geometry = []
    for _, row in affected_gdf.iterrows():
        geom = row.geometry
        geom_type = geom.geom_type
        
        if geom_type == "Polygon":
            coords = [list(geom.exterior.coords)]
            for interior in geom.interiors:
                coords.append(list(interior.coords))
        elif geom_type == "MultiPolygon":
            coords = []
            for poly in geom.geoms:
                poly_coords = [list(poly.exterior.coords)]
                for interior in poly.interiors:
                    poly_coords.append(list(interior.coords))
                coords.append(poly_coords)
        else:
            continue
            
        affected_buildings_geometry.append({
            "building_id": str(row['building_id']),
            "geometry": GeoJSONGeometry(
                type=GeometryType(geom_type),
                coordinates=coords
            ).model_dump() # Pydantic v2
        })
        
    return {
        "total_buildings": total_buildings,
        "affected_buildings": affected_buildings,
        "affected_percentage": affected_percentage,
        "affected_building_ids": affected_building_ids,
        "affected_buildings_geometry": affected_buildings_geometry
    }
