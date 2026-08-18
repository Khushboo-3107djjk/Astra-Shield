"""
Main Inference Pipeline - ASTRA-SHIELD
Takes satellite image(s) → Outputs complete modular disaster analysis
"""

import torch
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import base64
import cv2
import sys

sys.path.append(str(Path(__file__).parent.parent))

from preprocessing.preprocess import SatelliteImagePreprocessor
from models.classifier.disaster_classifier import DisasterClassifier

# Import disaster modules
from models.disaster_modules.flood import FloodModule
from models.disaster_modules.wildfire import WildfireModule
from models.disaster_modules.cyclone import CycloneModule
from models.disaster_modules.landslide import LandslideModule
from models.disaster_modules.earthquake import EarthquakeModule
from models.disaster_modules.drought import DroughtModule


class DisasterAnalyzer:
    """End-to-end multi-disaster analysis pipeline"""
    
    def __init__(
        self,
        classifier_path=None,
        device='cpu',
        img_size=512
    ):
        self.device = device
        self.img_size = img_size
        
        print("🚀 Initializing ASTRA-SHIELD Modular ML Pipeline...")
        self.preprocessor = SatelliteImagePreprocessor(img_size=img_size, normalize=True)
        print("  ✅ Preprocessor loaded")
        
        self.classifier = DisasterClassifier(
            model_path=classifier_path,
            device=device,
            pretrained=True
        )
        print("  ✅ 7-Class Classifier loaded")
        
        # Initialize modules
        self.modules = {
            "flood": FloodModule(device=device),
            "wildfire": WildfireModule(device=device),
            "cyclone": CycloneModule(device=device),
            "landslide": LandslideModule(device=device),
            "earthquake": EarthquakeModule(device=device),
            "drought": DroughtModule(device=device)
        }
        print("  ✅ Disaster modules loaded")
        print("✅ Pipeline ready!\n")
    
    def analyze(self, image_path, before_image_path=None, return_visualization=True):
        """
        Complete modular disaster analysis.
        """
        try:
            print(f"📷 Analyzing: {image_path}")
            
            # 1. Preprocess
            print("  [1/4] Preprocessing image(s)...")
            image, _, original = self.preprocessor.preprocess(image_path, return_original=True)
            image_tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0).to(self.device)
            
            before_image_tensor = None
            if before_image_path:
                b_image, _, _ = self.preprocessor.preprocess(before_image_path)
                before_image_tensor = torch.from_numpy(b_image).permute(2, 0, 1).unsqueeze(0).to(self.device)
                
            print("       ✅ Images preprocessed")
            
            # 2. Classification
            print("  [2/4] Classifying disaster type...")
            class_result = self.classifier.predict(image_tensor)
            
            disaster_type = class_result["disaster_type"]
            confidence = class_result["confidence"]
            
            if class_result["status"] == "model_not_available":
                print("       ⚠️ Classifier untrained. Falling back to module_not_available.")
                return self._get_fallback_response("unknown", None)
                
            print(f"       ✅ Detected: {disaster_type} (Confidence: {confidence:.2f})")
            
            # 3. Route to Disaster Module
            print("  [3/4] Routing to disaster-specific analysis...")
            if disaster_type == "normal" or disaster_type not in self.modules:
                return {
                    "disaster_type": disaster_type,
                    "confidence": confidence,
                    "severity": {"level": None, "score": None},
                    "affected_area_km2": None,
                    "change_percent": None,
                    "mask_path": None,
                    "analysis_status": "success",
                    "data_source": "satellite"
                }
                
            module = self.modules[disaster_type]
            analysis_result = module.analyze(image_tensor, before_image_tensor, original, confidence)
            
            # 4. Return standard JSON
            print("  [4/4] Encoding outputs...")
            print("✅ Analysis complete!\n")
            return analysis_result
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}\n")
            return self._get_fallback_response("error", None)
            
    def _get_fallback_response(self, disaster_type, confidence=None):
        return {
            "disaster_type": disaster_type,
            "confidence": confidence,
            "severity": {
                "level": None,
                "score": None
            },
            "affected_area_km2": None,
            "change_percent": None,
            "mask_path": None,
            "analysis_status": "model_not_available",
            "data_source": "demo"
        }
        
    def save_result(self, result, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Result saved to {output_path}")
        return result


def api_analyze_image(image_path: str, before_image_path=None, classifier_path=None):
    analyzer = DisasterAnalyzer(
        classifier_path=classifier_path,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    return analyzer.analyze(image_path, before_image_path=before_image_path)


if __name__ == "__main__":
    print("🛰️  ASTRA-SHIELD ML INFERENCE PIPELINE\n")
    
    analyzer = DisasterAnalyzer(device='cpu')
    demo_image = Path(__file__).parent.parent / "demo" / "flood" / "before.png"
    
    if demo_image.exists():
        result = analyzer.analyze(str(demo_image))
        
        print("="*60)
        print("ANALYSIS RESULT SUMMARY")
        print("="*60)
        print(f"Disaster Type:    {str(result.get('disaster_type')).upper()}")
        
        conf = result.get('confidence')
        print(f"Confidence:       {f'{conf:.1%}' if conf is not None else 'N/A'}")
        
        severity = result.get('severity', {})
        level = severity.get('level')
        score = severity.get('score')
        print(f"Severity:         {level if level else 'N/A'} ({score if score else 'N/A'})")
        
        area = result.get('affected_area_km2')
        print(f"Affected Area:    {f'{area:.2f} km²' if area is not None else 'N/A (Needs Geospatial)'}")
        
        change = result.get('change_percent')
        print(f"Change Percent:   {f'{change:.1f}%' if change is not None else 'N/A'}")
        
        print(f"Status:           {result.get('analysis_status')}")
        print("="*60 + "\n")
        
        output_file = demo_image.parent / "result.json"
        analyzer.save_result(result, output_file)
    else:
        print(f"⚠️  Demo image not found: {demo_image}")
