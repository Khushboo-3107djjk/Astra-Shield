# ML / AI
## Machine Learning Models for ASTRA-SHIELD

This directory contains:
- Training & preprocessing pipelines
- Disaster classification models
- Disaster segmentation models
- Inference pipeline
- Model evaluation & metrics

### Person 1's Deliverables

Your job: Take a satellite image → Output JSON with:
```json
{
  "disaster_type": "flood",
  "confidence": 0.94,
  "severity": 8.5,
  "affected_area_km2": 24.3,
  "mask": "base64_encoded_image"
}
```

### Structure

```
ml/
├── datasets/
│   ├── flood/
│   ├── wildfire/
│   └── README.md          # Dataset sources & format
│
├── preprocessing/
│   ├── preprocess.py      # Data loading & normalization
│   └── transforms.py      # Augmentation & splitting
│
├── models/
│   ├── classifier/
│   │   └── disaster_classifier.py   # Classification model
│   └── segmentation/
│       └── disaster_segmenter.py    # Segmentation model
│
├── inference/
│   └── predict.py         # Main inference pipeline
│
├── evaluation/
│   ├── metrics.py         # Accuracy, IoU, etc.
│   └── evaluate.py        # Model evaluation
│
├── outputs/
│   ├── masks/             # Segmentation outputs
│   ├── overlays/          # Visualization
│   └── predictions/       # JSON results
│
├── notebooks/
│   └── experiments.ipynb  # Development & experiments
│
└── requirements.txt
```

### Usage

```bash
# Preprocessing
python preprocessing/preprocess.py

# Training (if needed)
python models/classifier/disaster_classifier.py --train

# Inference on new image
python inference/predict.py --image path/to/image.tif

# Evaluation
python evaluation/evaluate.py
```

### Model Specs

**Disaster Classifier** (Classification)
- Input: Satellite image
- Output: `{disaster_type, confidence}`
- Model: ResNet50 / EfficientNet

**Disaster Segmenter** (Segmentation)
- Input: Satellite image
- Output: `{affected_area_km2, severity, mask}`
- Model: U-Net / DeepLab v3+

### Demo Scenarios

Pre-trained models should work on:
- Flood detection
- Wildfire detection
- Landslide detection

---

**Note**: You can train these models using public datasets (Sentinel-2, Landsat) or use pre-trained weights from similar tasks.
