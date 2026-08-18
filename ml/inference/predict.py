"""
Main Inference Pipeline - ASTRA-SHIELD
Takes satellite image → Outputs complete disaster analysis

This is what Person 2 (Backend) and Person 3 (Frontend) will call!
"""

import torch
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import base64
import cv2

# Import our models
import sys
sys.path.append(str(Path(__file__).parent.parent))

from preprocessing.preprocess import SatelliteImagePreprocessor
from models.classifier.disaster_classifier import DisasterClassifier
from models.segmentation.disaster_segmenter import DisasterSegmenter
from evaluation.metrics import DisasterMetrics, print_results


class DisasterAnalyzer:
    """End-to-end disaster analysis pipeline"""
    
    def __init__(
        self,
        classifier_path=None,
        segmenter_path=None,
        device='cpu',
        img_size=512
    ):
        """
        Initialize the complete analysis pipeline
        
        Args:
            classifier_path: Path to pre-trained classifier
            segmenter_path: Path to pre-trained segmenter
            device: 'cpu' or 'cuda'
            img_size: Input image size (default 512x512)
        """
        self.device = device
        self.img_size = img_size
        
        # Initialize components
        print("🚀 Initializing ASTRA-SHIELD ML Pipeline...")
        
        self.preprocessor = SatelliteImagePreprocessor(img_size=img_size, normalize=True)
        print("  ✅ Preprocessor loaded")
        
        self.classifier = DisasterClassifier(
            model_path=classifier_path,
            device=device,
            pretrained=True
        )
        print("  ✅ Classifier loaded")
        
        self.segmenter = DisasterSegmenter(
            model_path=segmenter_path,
            device=device
        )
        print("  ✅ Segmenter loaded")
        
        print("✅ Pipeline ready!\n")
    
    def analyze(self, image_path, return_visualization=True):
        """
        Complete disaster analysis from satellite image
        
        Args:
            image_path: Path to satellite image
            return_visualization: Whether to return visualization overlay
            
        Returns:
            {
                "success": bool,
                "timestamp": "2026-08-18T10:30:45",
                "image_path": "path/to/image.tif",
                
                "classification": {
                    "disaster_type": "flood",
                    "confidence": 0.94,
                    "predictions": {
                        "normal": 0.02,
                        "flood": 0.94,
                        "wildfire": 0.03,
                        "landslide": 0.01
                    }
                },
                
                "segmentation": {
                    "affected_area_km2": 24.3,
                    "severity_score": 8.5,
                    "confidence": 0.91,
                    "mask": "base64_encoded_mask"
                },
                
                "metrics": {
                    "affected_pixels": 127450,
                    "total_pixels": 262144
                },
                
                "visualization": "base64_encoded_overlay" (optional)
            }
        """
        
        try:
            print(f"📷 Analyzing: {image_path}")
            
            # Step 1: Load and preprocess image
            print("  [1/4] Preprocessing image...")
            image, original = self.preprocessor.preprocess(
                image_path,
                return_original=True
            )
            image_tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0)
            print("       ✅ Image preprocessed")
            
            # Step 2: Classification
            print("  [2/4] Classifying disaster type...")
            classification = self.classifier.predict(image_tensor)
            disaster_type = classification["disaster_type"]
            class_confidence = classification["confidence"]
            print(f"       ✅ Detected: {disaster_type} ({class_confidence:.1%})")
            
            # Step 3: Segmentation
            print("  [3/4] Segmenting affected area...")
            mask, seg_confidence = self.segmenter.predict(image_tensor, threshold=0.5)
            
            # Calculate metrics from mask
            affected_area = self.segmenter.calculate_affected_area(mask)
            severity = self.segmenter.calculate_severity(mask)
            affected_pixels = mask.sum()
            
            print(f"       ✅ Affected area: {affected_area:.2f} km²")
            print(f"       ✅ Severity: {severity:.1f}/10")
            print(f"       ✅ Confidence: {seg_confidence:.1%}")
            
            # Step 4: Encode outputs
            print("  [4/4] Encoding outputs...")
            
            # Convert mask to base64
            mask_uint8 = (mask * 255).astype(np.uint8)
            _, mask_encoded = cv2.imencode('.png', mask_uint8)
            mask_b64 = base64.b64encode(mask_encoded).decode('utf-8')
            
            # Optionally create visualization
            visualization_b64 = None
            if return_visualization:
                viz = self.segmenter.visualize_mask(original, mask, alpha=0.5)
                _, viz_encoded = cv2.imencode('.png', cv2.cvtColor(viz, cv2.COLOR_RGB2BGR))
                visualization_b64 = base64.b64encode(viz_encoded).decode('utf-8')
            
            print("       ✅ Outputs encoded")
            
            # Prepare result
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "image_path": str(image_path),
                
                "classification": {
                    "disaster_type": disaster_type,
                    "confidence": float(class_confidence),
                    "predictions": classification["predictions"]
                },
                
                "segmentation": {
                    "affected_area_km2": float(affected_area),
                    "severity_score": float(severity),
                    "confidence": float(seg_confidence),
                    "mask": mask_b64
                },
                
                "metrics": {
                    "affected_pixels": int(affected_pixels),
                    "total_pixels": int(mask.size),
                    "affected_percentage": float((affected_pixels / mask.size) * 100)
                }
            }
            
            if visualization_b64:
                result["visualization"] = visualization_b64
            
            print("✅ Analysis complete!\n")
            
            return result
        
        except Exception as e:
            print(f"❌ Error during analysis: {e}\n")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_batch(self, image_paths):
        """Analyze multiple images"""
        results = []
        for img_path in image_paths:
            result = self.analyze(img_path)
            results.append(result)
        return results
    
    def save_result(self, result, output_path):
        """Save analysis result to JSON"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a copy without base64 for readability
        result_clean = result.copy()
        if "visualization" in result_clean:
            del result_clean["visualization"]  # Don't save huge base64 in JSON
        
        with open(output_path, 'w') as f:
            json.dump(result_clean, f, indent=2)
        
        print(f"✅ Result saved to {output_path}")
        
        return result_clean


# ============================================================================
# BACKEND API INTEGRATION
# ============================================================================
# Person 2 should call this function from their FastAPI endpoint

def api_analyze_image(image_path: str, classifier_path=None, segmenter_path=None):
    """
    FastAPI-ready analysis function
    
    Usage in backend:
    ```
    from ml.inference.predict import api_analyze_image
    
    @app.post("/api/analyze")
    async def analyze(file: UploadFile):
        result = api_analyze_image(str(file.filename))
        return result
    ```
    """
    analyzer = DisasterAnalyzer(
        classifier_path=classifier_path,
        segmenter_path=segmenter_path,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    return analyzer.analyze(image_path, return_visualization=True)


# ============================================================================
# TESTING & DEMO
# ============================================================================

if __name__ == "__main__":
    print("🛰️  ASTRA-SHIELD ML INFERENCE PIPELINE\n")
    
    # Initialize analyzer
    analyzer = DisasterAnalyzer(device='cpu')
    
    # Example: Analyze a demo image (if it exists)
    demo_image = Path(__file__).parent.parent / "demo" / "flood" / "before.png"
    
    if demo_image.exists():
        result = analyzer.analyze(str(demo_image), return_visualization=True)
        
        # Print summary
        if result["success"]:
            print("="*60)
            print("ANALYSIS RESULT SUMMARY")
            print("="*60)
            print(f"Disaster Type:    {result['classification']['disaster_type'].upper()}")
            print(f"Confidence:       {result['classification']['confidence']:.1%}")
            print(f"Affected Area:    {result['segmentation']['affected_area_km2']:.2f} km²")
            print(f"Severity Score:   {result['segmentation']['severity_score']:.1f}/10")
            print(f"Affected %:       {result['metrics']['affected_percentage']:.1f}%")
            print("="*60 + "\n")
            
            # Save result
            output_file = demo_image.parent / "result.json"
            analyzer.save_result(result, output_file)
    else:
        print(f"⚠️  Demo image not found: {demo_image}")
        print("   To test, place satellite images in ml/demo/ directory")
    
    print("\n✅ Pipeline ready for integration with backend and frontend!")
    print("\nNext steps:")
    print("  1. Person 2: Import api_analyze_image() in backend/app/api/")
    print("  2. Person 3: Call backend endpoint from frontend")
    print("  3. See results in web dashboard!")

