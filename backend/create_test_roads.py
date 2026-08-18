import os
import geopandas as gpd
from shapely.geometry import LineString

def create_roads():
    os.makedirs('tests/data', exist_ok=True)
    # Flood poly: 10.03 to 10.07 (Lon), 49.93 to 49.97 (Lat)
    
    # R_IN: completely inside. 10.04 to 10.06 at Lat 49.95
    r1 = LineString([(10.04, 49.95), (10.06, 49.95)])
    
    # R_OUT: completely outside. 10.10 to 10.12 at Lat 49.90
    r2 = LineString([(10.10, 49.90), (10.12, 49.90)])
    
    # R_PARTIAL: partially intersects. 10.01 to 10.05 at Lat 49.96
    # Crosses the boundary 10.03. Affected portion is 10.03 to 10.05
    r3 = LineString([(10.01, 49.96), (10.05, 49.96)])
    
    gdf = gpd.GeoDataFrame({
        'road_id': ['R_IN', 'R_OUT', 'R_PARTIAL'],
        'road_type': ['major', 'minor', 'major']
    }, geometry=[r1, r2, r3], crs='EPSG:4326')
    
    gdf.to_file('tests/data/test_roads.geojson', driver='GeoJSON')
    
    # Empty dataset
    gdf_empty = gpd.GeoDataFrame({'road_id': [], 'road_type': []}, geometry=[], crs='EPSG:4326')
    gdf_empty.to_file('tests/data/empty_roads.geojson', driver='GeoJSON')
    
    # CRS mismatch (EPSG:3857)
    gdf_3857 = gdf.to_crs('EPSG:3857')
    gdf_3857.to_file('tests/data/mismatch_crs_roads.geojson', driver='GeoJSON')

if __name__ == '__main__':
    create_roads()
    print('Test roads generated successfully.')
