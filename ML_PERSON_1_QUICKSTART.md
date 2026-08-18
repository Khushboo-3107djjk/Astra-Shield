# 🚀 ASTRA-SHIELD ML Pipeline - Person 1 Quick Start

**Status**: ✅ ML pipeline complete and committed to branch K

---

## 📊 What You Just Got

Your complete machine learning pipeline for disaster detection:

```
ml/
├── ✅ preprocessing/preprocess.py    → Load & normalize satellite images
├── ✅ models/classifier/             → ResNet50 disaster type classifier
├── ✅ models/segmentation/           → U-Net disaster area segmenter
├── ✅ inference/predict.py           → Main entry point (call this!)
├── ✅ evaluation/metrics.py          → IoU, Dice, Accuracy calculations
├── ✅ evaluation/evaluate.py         → Evaluation script
├── ✅ datasets/README.md             → Dataset guidelines
├── ✅ notebooks/experiments.ipynb    → Your development notebook
└── ✅ README.md                      → Comprehensive documentation
```

---

## 🎯 Your Core Mission (In Order of Priority)

### **Priority 1: Test the Pipeline (15 minutes)**
```bash
cd ml
pip install -r ../requirements.txt
python inference/predict.py
```

Expected output:
```
🛰️  ASTRA-SHIELD ML INFERENCE PIPELINE
🚀 Initializing...
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

✅ **If this works, you're good to go!**

---

### **Priority 2: Get Real Satellite Data (30-60 minutes)**

**Option A: Quick Kaggle Dataset** (Fastest)
```bash
pip install kaggle
kaggle datasets download -d dataset-name
# Extract to ml/datasets/flood/, ml/datasets/wildfire/, etc.
```

**Option B: Sentinel-2 Free Data** (Better for space tech)
1. Register at [Copernicus Hub](https://scihub.copernicus.eu/)
2. Search for images in your region
3. Download GeoTIFF files
4. Put in `ml/datasets/`

**Option C: Use Demo Data** (For testing)
- Already in `ml/demo/flood/`, `ml/demo/wildfire/`, `ml/demo/landslide/`
- Use these while you get real data

---

### **Priority 3: Fine-Tune Models (If Time)**

**If you have labeled data:**
```python
# Create training script
import torch
from preprocessing.preprocess import SatelliteImagePreprocessor
from models.classifier import DisasterClassifier

# Load your data
preprocessor = SatelliteImagePreprocessor()
image, mask = preprocessor.preprocess("path/to/image.tif", "path/to/mask.tif")

# Fine-tune classifier on your disaster types
classifier = DisasterClassifier(device='cuda')
# ... training loop ...
classifier.load_model("trained_model.pth")
```

**If you DON'T have time:**
- Use transfer learning with ImageNet weights (already loaded)
- Test on public datasets
- Document baseline performance

---

### **Priority 4: Evaluate & Report Metrics (30 minutes)**

```bash
python ml/evaluation/evaluate.py --test-dir demo --output eval_report.json
```

You'll get:
```
EVALUATION SUMMARY
✅ Classification confidence: 94%
✅ Segmentation confidence: 91%
✅ Average severity: 8.5/10
```

**Include this in your technical report!**

---

## 🔗 How It Integrates

```
YOU (Person 1)                  PERSON 2 (Backend)              PERSON 3 (Frontend)
      │                              │                                 │
      └─ predict.py                  │                                 │
         │                           │                                 │
         └─ Returns JSON ────────────┼─────────────────────────────────┘
              {                      │
                disaster_type: ...,  └─ /api/analyze endpoint
                mask: base64(...),
                severity: ...
              }
```

---

## 📝 Files You'll Use Most

| File | What to do |
|---|---|
| `inference/predict.py` | **THIS IS YOUR MAIN FILE** - Call `api_analyze_image()` from here |
| `models/classifier/disaster_classifier.py` | Disaster type → Flood/Wildfire/Landslide |
| `models/segmentation/disaster_segmenter.py` | Affected area mask + severity score |
| `preprocessing/preprocess.py` | Load and normalize satellite images |
| `evaluation/metrics.py` | Calculate IoU, Dice, Accuracy |
| `notebooks/experiments.ipynb` | Your development & experimentation |

---

## 🧪 Quick Test Code

**Test 1: Classification Only**
```python
from models.classifier.disaster_classifier import DisasterClassifier
import torch

classifier = DisasterClassifier(device='cpu', pretrained=True)
dummy_image = torch.randn(1, 3, 512, 512)
result = classifier.predict(dummy_image)

print(f"Disaster: {result['disaster_type']}")
print(f"Confidence: {result['confidence']:.1%}")
```

**Test 2: Segmentation Only**
```python
from models.segmentation.disaster_segmenter import DisasterSegmenter

segmenter = DisasterSegmenter(device='cpu')
mask, confidence = segmenter.predict(dummy_image)

print(f"Affected pixels: {mask.sum()}")
print(f"Severity: {segmenter.calculate_severity(mask):.1f}/10")
```

**Test 3: Complete Pipeline**
```python
from inference.predict import DisasterAnalyzer

analyzer = DisasterAnalyzer(device='cpu')
result = analyzer.analyze("path/to/image.tif", return_visualization=True)

print(f"✅ Analysis successful!")
print(result)
```

---

## ✅ Deliverables Checklist

Before moving to integration, ensure:

- [ ] Pipeline runs without errors
- [ ] `inference/predict.py` produces valid JSON
- [ ] Classification returns disaster type + confidence
- [ ] Segmentation returns binary mask
- [ ] Metrics calculated (IoU, Dice, Accuracy)
- [ ] Results saved to `ml/outputs/`
- [ ] Code committed to branch K
- [ ] README documented with your decisions

---

## 🚨 Common Issues

| Problem | Solution |
|---|---|
| **ImportError: No module named 'torch'** | `pip install torch torchvision` |
| **CUDA out of memory** | Use `device='cpu'` in initialization |
| **Image loading fails** | Ensure image is 512x512, RGB, or use rasterio for .tif |
| **Models too slow** | Enable GPU, or reduce batch size |
| **Metrics don't calculate** | Ensure masks are binary (0 or 255) |

---

## 📞 Integration with Other Teams

**To Person 2 (Backend):**
```
"I've created ml/inference/predict.py with api_analyze_image() function.
Import it in your FastAPI endpoints. Here's the output format: ..."
```

**To Person 3 (Frontend):**
```
"Your segmentation mask comes as base64-encoded PNG.
Display it as an overlay on top of the original image.
Severity score ranges from 0-10, use it for risk coloring."
```

---

## 🎓 Learning Resources

If you need to understand the models better:

- **U-Net Architecture**: https://arxiv.org/abs/1505.04597
- **ResNet50**: https://arxiv.org/abs/1512.03385
- **IoU Metric**: https://en.wikipedia.org/wiki/Jaccard_index
- **Dice Coefficient**: https://en.wikipedia.org/wiki/Sørensen–Dice_coefficient
- **PyTorch Docs**: https://pytorch.org/docs/stable/index.html

---

## 🎯 Success Criteria

✅ **You're Done When:**

1. `python inference/predict.py` runs successfully
2. Person 2 can import and call your code
3. Person 3 gets valid JSON with mask data
4. Metrics are documented (IoU, Dice, Accuracy)
5. Code is committed to branch K
6. README explains your implementation choices

---

## 📊 Team Structure

```
You (Person 1)  →  Branch K
  ML Pipeline

Person 2        →  Backend branches
  (API Endpoints)
  
Person 3        →  Frontend branches
  (Web Dashboard)
```

**When ready to integrate:**
1. Create Pull Request from K → main
2. Person 2 & 3 review and test
3. Merge to main
4. Final demo!

---

## 🚀 Next Steps

1. **Right now**: Run `python inference/predict.py`
2. **Next 30 min**: Get satellite data (Kaggle or Sentinel-2)
3. **Next 1-2 hours**: Fine-tune models if you have time
4. **Final 30 min**: Run evaluation, document metrics
5. **Before meeting**: Create pull request to main

---

## 💡 Pro Tips

- ✅ Test early and often
- ✅ Use pretrained weights (don't start from scratch)
- ✅ Document your choices in comments
- ✅ Keep `predict.py` clean for easy integration
- ✅ Save evaluation metrics for technical report

---

**🚀 Your ML pipeline is ready. Go build something amazing!**

Questions? Check `ml/README.md` or `ml/notebooks/experiments.ipynb`

Good luck! 🛰️🤖
