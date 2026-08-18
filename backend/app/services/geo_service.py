import rasterio
from rasterio.features import shapes
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from app.api.errors import APIError
from app.schemas.geometry import GeoJSONGeometry, GeometryType

def process_flood_mask(mask_path: str):
    """
    Processes a georeferenced flood segmentation raster mask.
    Converts 1s to polygons, handles CRS, and calculates affected area in sq km.
    """
    try:
        with rasterio.open(mask_path) as src:
            # Validate CRS and transform
            if not src.crs:
                raise APIError("Raster is missing CRS (Coordinate Reference System)", status_code=400)
            if not src.transform or src.transform.is_identity:
                raise APIError("Raster is missing spatial transform", status_code=400)
            
            # Read first band
            band = src.read(1)
            
            # Extract flood pixels (1 = flood)
            flood_mask = (band == 1)
            flood_pixel_count = int(np.sum(flood_mask))
            
            if flood_pixel_count == 0:
                return {
                    "geometry": None,
                    "affected_area_km2": 0.0,
                    "flood_pixel_count": 0,
                    "crs": str(src.crs)
                }
            
            # Polygonize flood regions
            results = (
                {'properties': {'raster_val': v}, 'geometry': s}
                for i, (s, v) 
                in enumerate(shapes(band, mask=flood_mask, transform=src.transform))
            )
            
            geoms = list(results)
            gdf = gpd.GeoDataFrame.from_features(geoms, crs=src.crs)
            
            # Unify all geometries into a single representation (Polygon or MultiPolygon)
            unified_geom = gdf.geometry.unary_union
            
            # Area calculation
            # To calculate area correctly, reproject to an equal-area projection
            # EPSG:6933 (WGS 84 / NSIDC EASE-Grid 2.0 Global) is excellent for global equal-area
            gdf_equal_area = gdf.to_crs("EPSG:6933")
            area_sq_meters = gdf_equal_area.geometry.unary_union.area
            affected_area_km2 = area_sq_meters / 1_000_000.0
            
            # Map geometry to GeoJSON compatible output
            geom_type = unified_geom.geom_type
            if geom_type == "Polygon":
                coords = [list(unified_geom.exterior.coords)]
                for interior in unified_geom.interiors:
                    coords.append(list(interior.coords))
            elif geom_type == "MultiPolygon":
                coords = []
                for poly in unified_geom.geoms:
                    poly_coords = [list(poly.exterior.coords)]
                    for interior in poly.interiors:
                        poly_coords.append(list(interior.coords))
                    coords.append(poly_coords)
            else:
                raise APIError(f"Unexpected geometry type: {geom_type}", status_code=500)
            
            geojson_geom = GeoJSONGeometry(
                type=GeometryType(geom_type),
                coordinates=coords
            )
            
            return {
                "geometry": geojson_geom,
                "affected_area_km2": round(affected_area_km2, 4),
                "flood_pixel_count": flood_pixel_count,
                "crs": str(src.crs)
            }
            
    except rasterio.errors.RasterioIOError:
        raise APIError(f"Cannot read raster file: {mask_path}", status_code=400)
