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
    Classifies satellite images into disaster types.
    Current scope: Normal | Flood | Earthquake | Cyclone
    (Architecture is extensible to 7 classes when additional data is available)
    """
    
    CLASSES = {
        0: "normal",
        1: "flood",
        2: "earthquake",
        3: "cyclone"
    }
    
    def __init__(self, model_path=None, device='cpu', pretrained=True):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        # Load ResNet50 backbone
        self.model = models.resnet50(pretrained=pretrained)
        
        # Replace final layer for 4-class classification
        num_ftrs = self.model.fc.in_features
        self.model.fc = nn.Linear(num_ftrs, len(self.CLASSES))
        
        self.model = self.model.to(self.device)
        self.is_trained = False
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            print("⚠️  No pre-trained classifier found. Using untrained weights. Predictions will not be fabricated.")
    
    def load_model(self, model_path):
        """Load pre-trained weights"""
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            self.is_trained = True
            print(f"✅ Classifier loaded from {model_path}")
        except Exception as e:
            print(f"❌ Failed to load classifier: {e}")
    
    def predict(self, image_tensor):
        """
        Classify satellite image
        """
        if not self.is_trained:
            return {
                "disaster_type": "unknown",
                "confidence": None,
                "predictions": None,
                "status": "model_not_available"
            }
            
        self.model.eval()
        
        with torch.no_grad():
            if not isinstance(image_tensor, torch.Tensor):
                image_tensor = torch.from_numpy(image_tensor)
            
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)
            
            image_tensor = image_tensor.to(self.device)
            outputs = self.model(image_tensor)
            probs = torch.softmax(outputs, dim=1)[0].cpu().numpy()
            
            class_idx = np.argmax(probs)
            disaster_type = self.CLASSES[class_idx]
            confidence = probs[class_idx]
        
        return {
            "disaster_type": disaster_type,
            "confidence": float(confidence),
            "predictions": {
                self.CLASSES[i]: float(probs[i])
                for i in range(len(self.CLASSES))
            },
            "status": "success"
        }

if __name__ == "__main__":
    classifier = DisasterClassifier(device='cpu', pretrained=True)
    dummy_image = torch.randn(1, 3, 512, 512)
    result = classifier.predict(dummy_image)
    print(f"Classification test result: {result}")

