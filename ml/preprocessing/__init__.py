"""
ML/AI Module - ASTRA-SHIELD
Person 1's complete machine learning pipeline
"""

from preprocessing.preprocess import SatelliteImagePreprocessor, DataAugmenter
from models.classifier.disaster_classifier import DisasterClassifier
from models.segmentation.disaster_segmenter import DisasterSegmenter
from inference.predict import DisasterAnalyzer, api_analyze_image
from evaluation.metrics import DisasterMetrics, SegmentationMetrics, ClassificationMetrics

__version__ = "1.0.0"
__author__ = "Person 1 - ML/AI Engineer"

__all__ = [
    'SatelliteImagePreprocessor',
    'DataAugmenter',
    'DisasterClassifier',
    'DisasterSegmenter',
    'DisasterAnalyzer',
    'api_analyze_image',
    'DisasterMetrics',
    'SegmentationMetrics',
    'ClassificationMetrics'
]
