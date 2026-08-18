import os
import rasterio
from rasterio.transform import from_origin
import numpy as np

def create_test_rasters():
    os.makedirs("tests/data", exist_ok=True)
    
    # 1. Valid flood mask
    data = np.zeros((10, 10), dtype=rasterio.uint8)
    data[3:7, 3:7] = 1 # 4x4 block of flood pixels = 16 pixels
    
    # Create transform (e.g. 1 degree per pixel for easy math)
    # Longitude starts at 10.0, Latitude starts at 50.0
    transform = from_origin(10.0, 50.0, 0.01, 0.01)
    crs = 'EPSG:4326'
    
    valid_path = 'tests/data/test_flood_mask.tif'
    with rasterio.open(
        valid_path, 'w', driver='GTiff',
        height=data.shape[0], width=data.shape[1],
        count=1, dtype=data.dtype, crs=crs, transform=transform,
    ) as dest:
        dest.write(data, 1)
        
    # 2. Invalid missing CRS
    invalid_crs_path = 'tests/data/invalid_crs_mask.tif'
    with rasterio.open(
        invalid_crs_path, 'w', driver='GTiff',
        height=10, width=10,
        count=1, dtype=data.dtype, transform=transform
        # no crs
    ) as dest:
        dest.write(np.zeros((10, 10), dtype=rasterio.uint8), 1)

if __name__ == "__main__":
    create_test_rasters()
    print("Test rasters generated successfully.")
