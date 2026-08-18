# Disaster Datasets

Storage for satellite imagery and ground truth masks for training/testing.

## Directory Structure

```
datasets/
├── flood/
│   ├── images/
│   │   ├── before_1.tif
│   │   ├── before_2.tif
│   │   └── ...
│   └── masks/
│       ├── mask_1.tif
│       ├── mask_2.tif
│       └── ...
│
├── wildfire/
│   ├── images/
│   └── masks/
│
├── landslide/
│   ├── images/
│   └── masks/
│
└── README.md (this file)
```

---

## Data Sources

### ✅ Recommended Free Datasets

#### **1. Sentinel-2 Satellite Imagery** (ESA)
- **Source**: [Copernicus Open Access Hub](https://scihub.copernicus.eu/)
- **Resolution**: 10-60m
- **Bands**: 11 multispectral bands
- **Cost**: FREE
- **Good for**: Flood, Wildfire, Landslide detection
- **How to access**:
  1. Register at Copernicus hub
  2. Search for satellite images in your region
  3. Download GeoTIFF files
  4. Process with `rasterio` in preprocessing

#### **2. Landsat 8/9** (USGS)
- **Source**: [USGS Earth Explorer](https://earthexplorer.usgs.gov/)
- **Resolution**: 30m
- **Bands**: 11 bands
- **Cost**: FREE
- **Good for**: Large-area disaster monitoring
- **How to access**: Search by date/location, download Level 2 data

#### **3. Kaggle Datasets** (Pre-processed)
- **Flood segmentation**: Search "flood segmentation" on Kaggle
- **Wildfire detection**: Search "wildfire dataset"
- **Already labeled**: Much faster to get started!

#### **4. NASA WorldView** (High Resolution)
- **Source**: [NASA EarthData](https://earthdata.nasa.gov/)
- **Resolution**: 0.3-1m (highest quality)
- **Cost**: FREE (for research)
- **Good for**: Detailed disaster analysis

---

## Expected Data Format

### Training Images
```
Shape: (Height, Width, Channels)
- Single satellite image (512x512 typical)
- Format: .tif (GeoTIFF), .png, .jpg
- Channels: 3 (RGB) or multispectral (11+ channels for Sentinel-2)
- Values: 0-255 or 0-10000 (depends on format)
```

### Ground Truth Masks
```
Shape: (Height, Width)
- Binary mask: 0 (no disaster) or 255 (disaster)
- Format: .tif or .png
- Values: 0 or 255 (or 0-1 after normalization)
```

### Example File Pair
```
images/flood_case_1.tif      (512x512, 3 channels)
masks/flood_case_1_mask.tif  (512x512, 1 channel, binary)
```

---

## 📥 Quick Dataset Setup

### Option 1: Use Kaggle Datasets (FASTEST)

```bash
# Install Kaggle CLI
pip install kaggle

# Download flood segmentation dataset
kaggle datasets download -d [dataset-name]

# Unzip to datasets/flood/
unzip archive.zip -d ./flood/
```

### Option 2: Use Sentinel-2 (Recommended)

```python
# Example with sentinelsat package
from sentinelsat import SentinelAPI, geojson_to_wkt
from datetime import date

api = SentinelAPI('username', 'password', 
                  'https://scihub.copernicus.eu/dhus')

footprint = geojson_to_wkt(geom)  # Your region
products = api.query(
    footprint,
    date=(date(2023, 1, 1), date(2023, 12, 31)),
    platformname='Sentinel-2',
    cloudcoverpercentage=(0, 20)
)

# Download
api.download_all(products)
```

### Option 3: Use Demo Data

For hackathon, use pre-made demo images:
```bash
# Images already in ml/demo/flood/, ml/demo/wildfire/
# Use these for quick testing!
```

---

## 🔧 Data Preprocessing Steps

Once you have raw data, use `preprocessing/preprocess.py`:

```python
from preprocessing.preprocess import SatelliteImagePreprocessor

preprocessor = SatelliteImagePreprocessor(img_size=512)

# Load and process
image, mask = preprocessor.preprocess(
    "datasets/flood/images/flood_1.tif",
    "datasets/flood/masks/flood_1_mask.tif"
)

# Now ready for model training
```

---

## 📊 Recommended Dataset Sizes

For a 1-day hackathon with pretrained models:

```
Disaster Type  Training  Validation  Test
─────────────────────────────────────────
Flood          50        10         10    (total: 70 images)
Wildfire       50        10         10    (total: 70 images)
Landslide      50        10         10    (total: 70 images)

Total dataset: ~210 image-mask pairs
```

**Note**: With transfer learning + pretrained weights, you don't need huge amounts of data. 50-100 labeled examples per disaster type is sufficient.

---

## ⚠️ Data Quality Checklist

Before training, ensure:

- [ ] Images are 512x512 or resizable
- [ ] Masks are binary (0 or 255)
- [ ] Image-mask pairs are aligned
- [ ] No corrupted files
- [ ] Cloud coverage < 20% (for Sentinel-2)
- [ ] All images in same projection/coordinate system

---

## 🚀 Loading Data in Code

See `preprocessing/preprocess.py` for:
- `SatelliteImagePreprocessor.load_image()` → Load from .tif/.png/.jpg
- `SatelliteImagePreprocessor.load_mask()` → Load ground truth masks
- `DataAugmenter` → Random flips, rotations, brightness adjustments

---

## 📝 Dataset Documentation

If you add your own dataset, document it here:

### Example Entry:
```
DATASET NAME: India Floods 2023
Source: Sentinel-2 via Copernicus Hub
Date collected: July-August 2023
Region: Assam, India
Number of images: 42
Spatial resolution: 10m
File format: GeoTIFF
Status: ✅ Ready for training
Notes: High cloud coverage in some images, preprocessed
```

---

## 🔗 Useful References

- **Sentinel-2 Documentation**: https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi
- **Landsat 8 Bands**: https://www.usgs.gov/faqs/what-are-band-designations-landsat-satellites
- **rasterio Documentation**: https://rasterio.readthedocs.io/
- **OpenCV Image Processing**: https://docs.opencv.org/

---

## ❓ FAQ

**Q: Can I use RGB images from Google Maps?**
A: Yes, but Sentinel-2/Landsat are better for multispectral analysis. RGB works fine for demo.

**Q: What if my images are different sizes?**
A: Preprocessing automatically resizes to 512x512. See `preprocess.py`.

**Q: How do I create masks if I only have images?**
A: Use segmentation tools like QGIS, labelImg, or manual polygon annotation.

**Q: Is the data too large to fit in memory?**
A: Use data loaders and batch processing. See `preprocessing/preprocess.py` for examples.

---

**Next**: Start collecting data, or use Kaggle datasets to get going quickly!
