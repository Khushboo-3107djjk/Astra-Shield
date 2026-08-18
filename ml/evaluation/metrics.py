"""
Evaluation Metrics for Disaster Detection
IoU, Dice, Accuracy, Precision, Recall, F1
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)


class SegmentationMetrics:
    """Metrics for segmentation models"""
    
    @staticmethod
    def iou(pred_mask, true_mask):
        """
        Intersection over Union (Jaccard Index)
        For binary segmentation: IoU = TP / (TP + FP + FN)
        
        Args:
            pred_mask: (H, W) predicted binary mask
            true_mask: (H, W) ground truth binary mask
            
        Returns:
            iou: float [0, 1]
        """
        intersection = np.logical_and(pred_mask, true_mask).sum()
        union = np.logical_or(pred_mask, true_mask).sum()
        
        if union == 0:
            return 1.0 if intersection == 0 else 0.0
        
        return intersection / union
    
    @staticmethod
    def dice(pred_mask, true_mask):
        """
        Dice Coefficient (F1 Score for segmentation)
        Dice = 2 * TP / (2 * TP + FP + FN)
        
        Args:
            pred_mask: (H, W) predicted binary mask
            true_mask: (H, W) ground truth binary mask
            
        Returns:
            dice: float [0, 1]
        """
        intersection = np.logical_and(pred_mask, true_mask).sum()
        total = pred_mask.sum() + true_mask.sum()
        
        if total == 0:
            return 1.0 if intersection == 0 else 0.0
        
        return (2 * intersection) / total
    
    @staticmethod
    def pixel_accuracy(pred_mask, true_mask):
        """Percentage of correctly classified pixels"""
        correct = (pred_mask == true_mask).sum()
        total = true_mask.size
        return correct / total
    
    @staticmethod
    def evaluate(pred_mask, true_mask):
        """
        Complete segmentation evaluation
        
        Returns:
            dict with IoU, Dice, Accuracy
        """
        return {
            "iou": SegmentationMetrics.iou(pred_mask, true_mask),
            "dice": SegmentationMetrics.dice(pred_mask, true_mask),
            "accuracy": SegmentationMetrics.pixel_accuracy(pred_mask, true_mask)
        }


class ClassificationMetrics:
    """Metrics for classification models"""
    
    @staticmethod
    def evaluate(pred_labels, true_labels):
        """
        Complete classification evaluation
        
        Args:
            pred_labels: (N,) predicted class indices
            true_labels: (N,) ground truth class indices
            
        Returns:
            dict with Accuracy, Precision, Recall, F1
        """
        return {
            "accuracy": accuracy_score(true_labels, pred_labels),
            "precision_weighted": precision_score(true_labels, pred_labels, average='weighted', zero_division=0),
            "recall_weighted": recall_score(true_labels, pred_labels, average='weighted', zero_division=0),
            "f1_weighted": f1_score(true_labels, pred_labels, average='weighted', zero_division=0),
            "confusion_matrix": confusion_matrix(true_labels, pred_labels)
        }
    
    @staticmethod
    def report(pred_labels, true_labels, class_names=None):
        """Detailed classification report"""
        return classification_report(
            true_labels, pred_labels,
            target_names=class_names,
            zero_division=0
        )


class DisasterMetrics:
    """
    Complete evaluation for ASTRA-SHIELD
    Combines classification + segmentation metrics
    """
    
    @staticmethod
    def evaluate_disaster_detection(
        pred_class, true_class,
        pred_mask, true_mask,
        class_names=None
    ):
        """
        Comprehensive disaster detection evaluation
        
        Returns:
            {
                "classification": {...},
                "segmentation": {...},
                "summary": "..."
            }
        """
        
        # Classification metrics
        if pred_class is not None and true_class is not None:
            pred_labels = np.array([pred_class])
            true_labels = np.array([true_class])
            class_metrics = ClassificationMetrics.evaluate(pred_labels, true_labels)
        else:
            class_metrics = {}
        
        # Segmentation metrics
        if pred_mask is not None and true_mask is not None:
            seg_metrics = SegmentationMetrics.evaluate(pred_mask, true_mask)
        else:
            seg_metrics = {}
        
        return {
            "classification": class_metrics,
            "segmentation": seg_metrics,
        }


def print_results(results):
    """Pretty print evaluation results"""
    print("\n" + "="*50)
    print("ASTRA-SHIELD EVALUATION RESULTS")
    print("="*50)
    
    if "classification" in results and results["classification"]:
        print("\n📊 CLASSIFICATION METRICS:")
        print(f"  Accuracy:  {results['classification'].get('accuracy', 0):.3f}")
        print(f"  Precision: {results['classification'].get('precision_weighted', 0):.3f}")
        print(f"  Recall:    {results['classification'].get('recall_weighted', 0):.3f}")
        print(f"  F1-Score:  {results['classification'].get('f1_weighted', 0):.3f}")
    
    if "segmentation" in results and results["segmentation"]:
        print("\n🎯 SEGMENTATION METRICS:")
        print(f"  IoU:       {results['segmentation'].get('iou', 0):.3f}")
        print(f"  Dice:      {results['segmentation'].get('dice', 0):.3f}")
        print(f"  Accuracy:  {results['segmentation'].get('accuracy', 0):.3f}")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    # Example usage
    print("✅ Evaluation metrics module ready")
    
    # Test segmentation
    pred_mask = np.random.rand(512, 512) > 0.5
    true_mask = np.random.rand(512, 512) > 0.5
    
    seg_metrics = SegmentationMetrics.evaluate(pred_mask, true_mask)
    print(f"Test IoU: {seg_metrics['iou']:.3f}")
    print(f"Test Dice: {seg_metrics['dice']:.3f}")
