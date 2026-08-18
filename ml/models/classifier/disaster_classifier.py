"""
Disaster Classification Model - ResNet50
Output: Disaster type classification (Flood, Wildfire, Landslide, Normal)
"""

import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path
import numpy as np


class DisasterClassifier:
    """
    Classifies satellite images into disaster types
    Classes: Flood | Wildfire | Landslide | Normal
    """
    
    CLASSES = {
        0: "normal",
        1: "flood",
        2: "wildfire",
        3: "landslide"
    }
    
    def __init__(self, model_path=None, device='cpu', pretrained=True):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        # Load ResNet50 backbone
        self.model = models.resnet50(pretrained=pretrained)
        
        # Replace final layer for 4-class classification
        num_ftrs = self.model.fc.in_features
        self.model.fc = nn.Linear(num_ftrs, len(self.CLASSES))
        
        self.model = self.model.to(self.device)
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            print("⚠️  No pre-trained classifier found. Using ImageNet weights.")
    
    def load_model(self, model_path):
        """Load pre-trained weights"""
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            print(f"✅ Classifier loaded from {model_path}")
        except Exception as e:
            print(f"❌ Failed to load classifier: {e}")
    
    def predict(self, image_tensor):
        """
        Classify satellite image
        
        Args:
            image_tensor: (1, 3, H, W) normalized image tensor
            
        Returns:
            {
                "disaster_type": "flood",
                "confidence": 0.94,
                "predictions": {
                    "normal": 0.02,
                    "flood": 0.94,
                    "wildfire": 0.03,
                    "landslide": 0.01
                }
            }
        """
        self.model.eval()
        
        with torch.no_grad():
            # Ensure image is on correct device
            if not isinstance(image_tensor, torch.Tensor):
                image_tensor = torch.from_numpy(image_tensor)
            
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)  # Add batch dim
            
            image_tensor = image_tensor.to(self.device)
            
            # Forward pass
            outputs = self.model(image_tensor)  # (1, 4)
            
            # Get probabilities
            probs = torch.softmax(outputs, dim=1)[0].cpu().numpy()
            
            # Get top prediction
            class_idx = np.argmax(probs)
            disaster_type = self.CLASSES[class_idx]
            confidence = probs[class_idx]
        
        return {
            "disaster_type": disaster_type,
            "confidence": float(confidence),
            "predictions": {
                self.CLASSES[i]: float(probs[i])
                for i in range(len(self.CLASSES))
            }
        }


if __name__ == "__main__":
    # Test classifier
    classifier = DisasterClassifier(device='cpu', pretrained=True)
    
    # Create dummy image
    dummy_image = torch.randn(1, 3, 512, 512)
    
    # Predict
    result = classifier.predict(dummy_image)
    
    print(f"✅ Classification test successful")
    print(f"  Disaster type: {result['disaster_type']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  All predictions: {result['predictions']}")

