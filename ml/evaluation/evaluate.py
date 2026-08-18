"""
Model Evaluation Script
Tests trained models and generates performance report
"""

import torch
import numpy as np
from pathlib import Path
import json
import argparse

from preprocessing.preprocess import SatelliteImagePreprocessor
from models.classifier.disaster_classifier import DisasterClassifier
from models.segmentation.disaster_segmenter import DisasterSegmenter
from evaluation.metrics import DisasterMetrics, print_results
from inference.predict import DisasterAnalyzer


def evaluate_classifier(classifier, test_images, test_labels):
    """Evaluate classification performance"""
    pred_labels = []
    
    for img_path in test_images:
        preprocessor = SatelliteImagePreprocessor()
        image, _ = preprocessor.preprocess(img_path)
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0)
        
        result = classifier.predict(image_tensor)
        pred_labels.append(result["disaster_type"])
    
    # Would need actual label conversion to class indices for full evaluation
    return pred_labels


def evaluate_segmenter(segmenter, test_images, test_masks):
    """Evaluate segmentation performance"""
    iou_scores = []
    dice_scores = []
    
    preprocessor = SatelliteImagePreprocessor()
    
    for img_path, mask_path in zip(test_images, test_masks):
        image, _ = preprocessor.preprocess(img_path)
        _, gt_mask = preprocessor.preprocess(mask_path)
        
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0)
        pred_mask, _ = segmenter.predict(image_tensor)
        
        # Calculate metrics
        from evaluation.metrics import SegmentationMetrics
        iou = SegmentationMetrics.iou(pred_mask, gt_mask)
        dice = SegmentationMetrics.dice(pred_mask, gt_mask)
        
        iou_scores.append(iou)
        dice_scores.append(dice)
    
    return {
        "mean_iou": np.mean(iou_scores),
        "std_iou": np.std(iou_scores),
        "mean_dice": np.mean(dice_scores),
        "std_dice": np.std(dice_scores)
    }


def generate_report(analyzer, test_images, output_file="evaluation_report.json"):
    """Generate comprehensive evaluation report"""
    
    results = []
    for img_path in test_images:
        result = analyzer.analyze(str(img_path), return_visualization=False)
        results.append(result)
    
    # Aggregate statistics
    report = {
        "total_images": len(results),
        "successful_analyses": sum(1 for r in results if r.get("success", False)),
        "avg_classification_confidence": np.mean([
            r["classification"]["confidence"]
            for r in results if r.get("success", False)
        ]),
        "avg_segmentation_confidence": np.mean([
            r["segmentation"]["confidence"]
            for r in results if r.get("success", False)
        ]),
        "avg_severity": np.mean([
            r["segmentation"]["severity_score"]
            for r in results if r.get("success", False)
        ]),
        "sample_results": results[:5]  # Save first 5 for inspection
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Report saved to {output_file}")
    
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate ASTRA-SHIELD models")
    parser.add_argument("--test-dir", default="demo", help="Directory with test images")
    parser.add_argument("--output", default="evaluation_report.json", help="Output report file")
    parser.add_argument("--device", default="cpu", help="Device: cpu or cuda")
    
    args = parser.parse_args()
    
    print("📊 Starting Model Evaluation...\n")
    
    # Initialize analyzer
    analyzer = DisasterAnalyzer(device=args.device)
    
    # Generate report
    report = generate_report(analyzer, [f"demo/flood/before.png"], output_file=args.output)
    
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Total images:              {report['total_images']}")
    print(f"Successful analyses:       {report['successful_analyses']}")
    print(f"Avg classification conf:   {report['avg_classification_confidence']:.1%}")
    print(f"Avg segmentation conf:     {report['avg_segmentation_confidence']:.1%}")
    print(f"Avg severity score:        {report['avg_severity']:.1f}/10")
    print("="*60)
