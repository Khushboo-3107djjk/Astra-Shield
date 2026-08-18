import os
import geopandas as gpd
from shapely.geometry import Point

def create_facilities():
    os.makedirs('tests/data', exist_ok=True)
    # Flood polygon: Lon 10.03 to 10.07, Lat 49.93 to 49.97

    facilities = {
        'facility_id':   ['H_IN', 'H_OUT', 'S_IN', 'S_OUT', 'E_IN', 'E_OUT'],
        'facility_name': [
            'City General Hospital', 'Riverside Hospital',
            'Central Primary School', 'North Valley School',
            'Fire Station Alpha', 'Police Post West'
        ],
        'facility_type': ['hospital', 'hospital', 'school', 'school', 'emergency', 'emergency'],
    }
    geometries = [
        Point(10.05, 49.95),  # H_IN:  inside
        Point(10.10, 49.90),  # H_OUT: outside
        Point(10.04, 49.94),  # S_IN:  inside
        Point(10.12, 49.88),  # S_OUT: outside
        Point(10.06, 49.96),  # E_IN:  inside
        Point(10.08, 49.91),  # E_OUT: outside
    ]

    gdf = gpd.GeoDataFrame(facilities, geometry=geometries, crs='EPSG:4326')
    gdf.to_file('tests/data/test_critical_facilities.geojson', driver='GeoJSON')

    gdf_empty = gpd.GeoDataFrame(
        {'facility_id': [], 'facility_name': [], 'facility_type': []},
        geometry=[], crs='EPSG:4326'
    )
    gdf_empty.to_file('tests/data/empty_critical_facilities.geojson', driver='GeoJSON')

    gdf_3857 = gdf.to_crs('EPSG:3857')
    gdf_3857.to_file('tests/data/mismatch_crs_critical_facilities.geojson', driver='GeoJSON')

if __name__ == '__main__':
    create_facilities()
    print('Test critical facility datasets generated successfully.')
