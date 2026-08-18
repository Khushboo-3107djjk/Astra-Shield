import os
import geopandas as gpd
from shapely.geometry import Polygon

def create_buildings():
    os.makedirs('tests/data', exist_ok=True)
    # 1. Completely inside: Lon 10.04 to 10.05, Lat 49.94 to 49.95
    b1 = Polygon([(10.04, 49.94), (10.05, 49.94), (10.05, 49.95), (10.04, 49.95), (10.04, 49.94)])
    # 2. Completely outside: Lon 10.10 to 10.11, Lat 49.90 to 49.91
    b2 = Polygon([(10.10, 49.90), (10.11, 49.90), (10.11, 49.91), (10.10, 49.91), (10.10, 49.90)])
    # 3. Intersecting: Lon 10.02 to 10.04, Lat 49.96 to 49.98
    b3 = Polygon([(10.02, 49.96), (10.04, 49.96), (10.04, 49.98), (10.02, 49.98), (10.02, 49.96)])
    
    gdf = gpd.GeoDataFrame(
        {'building_id': ['B_IN', 'B_OUT', 'B_INTERSECT']},
        geometry=[b1, b2, b3],
        crs='EPSG:4326'
    )
    gdf.to_file('tests/data/test_buildings.geojson', driver='GeoJSON')
    
    # Create empty dataset
    gdf_empty = gpd.GeoDataFrame({'building_id': []}, geometry=[], crs='EPSG:4326')
    gdf_empty.to_file('tests/data/empty_buildings.geojson', driver='GeoJSON')
    
    # Create CRS mismatch dataset (EPSG:3857)
    gdf_3857 = gdf.to_crs('EPSG:3857')
    gdf_3857.to_file('tests/data/mismatch_crs_buildings.geojson', driver='GeoJSON')

if __name__ == '__main__':
    create_buildings()
    print('Test buildings generated successfully.')
