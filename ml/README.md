# 👩‍💻 ML/AI Module - ASTRA-SHIELD
## Person 1's Complete Machine Learning Pipeline

**Your mission**: Take satellite image → Output disaster detection JSON

---

## 📋 What You're Building

Your job is to create a **complete disaster detection pipeline** that outputs:

```json
{
  "disaster_type": "flood",
  "confidence": 0.94,
  "affected_area_km2": 24.3,
  "severity_score": 8.5,
  "mask": "base64_encoded_segmentation_mask",
  "visualization": "base64_encoded_overlay"
}
```

Person 2 will use this to calculate infrastructure impact.
Person 3 will visualize it in the web interface.

---

## 🎯 The 3 Disasters You're Supporting

```
🌊 Flood     → Satellite image → Segmentation mask
🔥 Wildfire  → Satellite image → Segmentation mask
⛰️ Landslide → Satellite image → Segmentation mask
```

---

## 📁 Current Structure

```
ml/
├── preprocessing/
│   ├── preprocess.py          ✅ Complete - Load, resize, normalize
│   └── __init__.py
│
├── models/
│   ├── classifier/
│   │   └── disaster_classifier.py   ✅ Complete - ResNet50 classification
│   └── segmentation/
│       └── disaster_segmenter.py    ✅ Complete - U-Net segmentation
│
├── inference/
│   └── predict.py             ✅ Complete - Main entry point!
│
├── evaluation/
│   ├── metrics.py             ✅ Complete - IoU, Dice, Accuracy
│   └── evaluate.py            ✅ Complete - Evaluation script
│
├── datasets/
│   └── README.md              ← YOU FILL THIS
│
├── outputs/
│   ├── masks/                 ← Saves segmentation masks here
│   ├── overlays/              ← Saves visualization overlays here
│   └── predictions/           ← Saves JSON results here
│
├── notebooks/
│   └── experiments.ipynb      ← YOU CREATE THIS
│
└── README.md                  ← YOU'RE READING THIS!
```

---

## 🚀 Quick Start (Right Now!)

### 1. Install dependencies

```bash
cd ml
pip install -r ../requirements.txt
```

Key packages:
```
torch==2.1.1
torchvision==0.16.1
opencv-python==4.8.1.78
numpy pandas scikit-learn
rasterio geopandas
```

### 2. Test the pipeline

```bash
python inference/predict.py
```

This will:
- Initialize the classifier & segmenter
- Run on demo images (if they exist)
- Generate `evaluation_report.json`

Expected output:
```
🛰️  ASTRA-SHIELD ML INFERENCE PIPELINE

🚀 Initializing ASTRA-SHIELD ML Pipeline...
  ✅ Preprocessor loaded
  ✅ Classifier loaded
  ✅ Segmenter loaded
✅ Pipeline ready!

📷 Analyzing: demo/flood/before.png
  [1/4] Preprocessing image...
  [2/4] Classifying disaster type...
       ✅ Detected: flood (94%)
  [3/4] Segmenting affected area...
       ✅ Affected area: 24.3 km²
  [4/4] Encoding outputs...
✅ Analysis complete!
```

### 3. Evaluate the models

```bash
python evaluation/evaluate.py --test-dir demo --output eval_report.json
```

---

## 🧠 Model Architecture Reference

### DisasterClassifier (ResNet50)
```
Satellite Image (512x512)
    ↓
ResNet50 backbone (pretrained on ImageNet)
    ↓
Classification head (4 classes)
    ↓
Softmax → Probabilities
    ↓
Output: {disaster_type, confidence, predictions}
```

**Classes**: Normal | Flood | Wildfire | Landslide

### DisasterSegmenter (U-Net)
```
Satellite Image (512x512)
    ↓
Encoder (downsampling)
    ↓
Bottleneck
    ↓
Decoder (upsampling with skip connections)
    ↓
Sigmoid
    ↓
Output: Binary mask (H, W, values 0-1)
    ↓
Thresholding (>0.5 → disaster)
```

---

## 📊 Metrics You Should Track

For **Classification**:
```
✅ Accuracy       (overall correct)
✅ Precision      (positive predictions correct)
✅ Recall         (actual positives found)
✅ F1-Score       (balance of precision & recall)
```

For **Segmentation** (MOST IMPORTANT):
```
✅ IoU (Intersection over Union)    [Target: >0.70]
✅ Dice Coefficient                 [Target: >0.75]
✅ Pixel Accuracy                   [Target: >0.90]
```

See `evaluation/metrics.py` for implementation.

---

## 🔄 Your Development Workflow

### Day 1: Get the pipeline working

1. **[DONE] Set up models**
   - ✅ DisasterClassifier (ResNet50 + pretrained weights)
   - ✅ DisasterSegmenter (U-Net architecture)
   - ✅ Both can run on CPU (slow but works)

2. **[TODO] Get datasets**
   ```
   Options:
   - Sentinel-2 satellite images (ESA)
   - Landsat (USGS)
   - Kaggle datasets (search "satellite disaster")
   - NASA datasets
   
   Store in: ml/datasets/flood/, ml/datasets/wildfire/, etc.
   ```

3. **[TODO] Fine-tune models (if time)**
   ```
   If you have labeled data:
   - Run preprocessing.py on your data
   - Train/val/test split
   - Fine-tune classifier on 3 disasters
   - Fine-tune segmenter on disaster masks
   ```
   
   If you DON'T have time:
   - Use transfer learning (ImageNet weights for classifier)
   - Use U-Net pretrained on similar tasks
   - Test on demo images as-is

4. **[TODO] Evaluate performance**
   ```bash
   python evaluation/evaluate.py
   ```
   
   Report metrics in your technical documentation

---

## 💻 How Backend/Frontend Will Call You

### From Backend (Person 2)

```python
from ml.inference.predict import api_analyze_image

@app.post("/api/analyze")
async def analyze(file: UploadFile):
    # Save uploaded file
    img_path = f"temp/{file.filename}"
    with open(img_path, 'wb') as f:
        f.write(file.file.read())
    
    # Call YOUR function
    result = api_analyze_image(img_path)
    
    return result
```

### From Frontend (Person 3)

```javascript
// JavaScript/React
const formData = new FormData();
formData.append('file', satelliteImage);

const response = await fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  body: formData
});

const result = await response.json();
// result.segmentation.mask → display as overlay
// result.classification.disaster_type → show disaster name
// result.segmentation.severity_score → show risk level
```

---

## 🎓 Recommended Learning Path (if starting fresh)

If you haven't used PyTorch before:

1. **Understanding U-Net** (30 min)
   - Read: https://arxiv.org/abs/1505.04597
   - Understand: Encoder-decoder with skip connections

2. **PyTorch basics** (1 hour)
   ```python
   import torch
   x = torch.randn(1, 3, 512, 512)  # batch, channels, height, width
   model = MyModel()
   output = model(x)
   ```

3. **Transfer learning** (1 hour)
   - Use pretrained ResNet50 for classification
   - Use pretrained weights from `torchvision.models`

4. **Segmentation metrics** (30 min)
   - IoU = True Positives / (True Pos + False Pos + False Neg)
   - Dice = 2*TP / (2*TP + FP + FN)
   - See `evaluation/metrics.py` for implementation

---

## 📝 Key Files Reference

| File | Purpose | Status |
|---|---|---|
| `preprocessing/preprocess.py` | Load, resize, normalize images | ✅ Complete |
| `preprocessing/__init__.py` | Data augmentation utilities | ✅ Complete |
| `models/classifier/disaster_classifier.py` | ResNet50 classification | ✅ Complete |
| `models/segmentation/disaster_segmenter.py` | U-Net segmentation | ✅ Complete |
| `inference/predict.py` | Main entry point (calls both models) | ✅ Complete |
| `evaluation/metrics.py` | IoU, Dice, Accuracy calculations | ✅ Complete |
| `evaluation/evaluate.py` | Evaluation script | ✅ Complete |
| `notebooks/experiments.ipynb` | Your experimentation notebook | [CREATE THIS] |
| `datasets/README.md` | Document your dataset sources | [UPDATE THIS] |

---

## 🔗 Integration Checklist

- [ ] **Models working**: Run `python inference/predict.py` successfully
- [ ] **Preprocessing working**: Images load and resize correctly
- [ ] **Classification working**: Classifier returns disaster type + confidence
- [ ] **Segmentation working**: Segmenter returns binary mask
- [ ] **Metrics calculated**: IoU/Dice scores are computed
- [ ] **Backend integration**: Person 2 can import `api_analyze_image()`
- [ ] **Results formatted**: JSON output matches expected schema
- [ ] **Visualization working**: Base64 encoded masks are generated
- [ ] **Performance documented**: Report metrics in technical documentation

---

## 🎯 Your Hackathon Deliverables

1. **Working ML Pipeline**
   - Takes satellite image
   - Returns disaster analysis JSON

2. **Evaluation Report**
   - Metrics on test set (IoU, Dice, Accuracy)
   - Examples of predictions (3+ images)
   - Analysis of strengths/weaknesses

3. **Integration Documentation**
   - How Person 2 calls your code
   - Expected input/output format
   - Example API responses

---

## 🚨 Common Issues & Solutions

| Issue | Solution |
|---|---|
| Model not loading | Check path exists, use relative paths |
| Out of memory | Use device='cpu', reduce batch size |
| Images not preprocessing | Check image format, use rasterio for GeoTIFF |
| Metrics too low | Use pretrained weights, try data augmentation |
| Performance slow | Enable GPU, batch process images |

---

## 📞 Communication with Other Persons

**Person 2 (Backend)**: "Your `api_analyze_image()` function is our gateway. Make sure it returns valid JSON."

**Person 3 (Frontend)**: "Your segmentation mask as base64 will display as an overlay. Make it clear!"

---

## ✅ Success Criteria

✅ **Person 1 SUCCESS = Teammates can use your code without modification**

When Person 2 can call:
```python
from ml.inference.predict import api_analyze_image
result = api_analyze_image("image.tif")
```

And get back:
```json
{
  "disaster_type": "flood",
  "confidence": 0.94,
  "affected_area_km2": 24.3,
  "mask": "base64..."
}
```

**THEN YOU'RE DONE! ✅**

---

Good luck! 🚀🛰️

