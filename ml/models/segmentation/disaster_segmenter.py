"""
Disaster Segmentation Model - U-Net Architecture
Outputs: Disaster mask showing affected areas
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
import numpy as np
import cv2


class DoubleConv(nn.Module):
    """Double convolution block"""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x):
        return self.double_conv(x)


class UNet(nn.Module):
    """
    U-Net segmentation model
    Input: (B, 3, H, W) - satellite image
    Output: (B, 1, H, W) - binary disaster mask [0, 1]
    """
    
    def __init__(self, in_channels=3, out_channels=1, features=[64, 128, 256, 512]):
        super().__init__()
        
        self.ups = nn.ModuleList()
        self.downs = nn.ModuleList()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Encoder (downsampling)
        in_ch = in_channels
        for feature in features:
            self.downs.append(DoubleConv(in_ch, feature))
            in_ch = feature
        
        # Bottleneck
        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)
        
        # Decoder (upsampling)
        for feature in reversed(features):
            self.ups.append(nn.ConvTranspose2d(feature * 2, feature, kernel_size=2, stride=2))
            self.ups.append(DoubleConv(feature * 2, feature))
        
        # Final output layer
        self.final_conv = nn.Conv2d(features[0], out_channels, kernel_size=1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        skip_connections = []
        
        # Encoder
        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)
        
        # Bottleneck
        x = self.bottleneck(x)
        
        # Decoder
        skip_connections = skip_connections[::-1]
        
        for idx in range(0, len(self.ups), 2):
            x = self.ups[idx](x)
            
            skip = skip_connections[idx // 2]
            
            # Handle size mismatch
            if x.shape != skip.shape:
                x = F.interpolate(x, size=skip.shape[2:], mode='bilinear', align_corners=False)
            
            x = torch.cat((skip, x), dim=1)
            x = self.ups[idx + 1](x)
        
        # Output
        x = self.final_conv(x)
        x = self.sigmoid(x)  # Binary output [0, 1]
        
        return x


class DisasterSegmenter:
    """
    Wrapper for disaster segmentation model
    Handles loading, inference, and output formatting
    """
    
    def __init__(self, model_path=None, device='cpu'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.model = UNet(in_channels=3, out_channels=1).to(self.device)
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            print("⚠️  No pre-trained model found. Using random weights for demo.")
    
    def load_model(self, model_path):
        """Load pre-trained weights"""
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            print(f"✅ Model loaded from {model_path}")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
    
    def predict(self, image_tensor, threshold=0.5):
        """
        Generate segmentation mask
        
        Args:
            image_tensor: (1, 3, H, W) normalized image
            threshold: confidence threshold for binary mask
            
        Returns:
            mask: (H, W) binary mask
            confidence: float, mean confidence score
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
            output = self.model(image_tensor)  # (1, 1, H, W)
            
            # Get mask and confidence
            confidence = output.mean().item()
            mask = (output[0, 0].cpu().numpy() > threshold).astype(np.uint8)
        
        return mask, confidence
    
    def calculate_affected_area(self, mask, pixel_to_km2=1.0):
        """
        Calculate affected area from mask
        
        Args:
            mask: binary mask
            pixel_to_km2: conversion factor (depends on satellite resolution)
                         e.g., 10m resolution → 100 pixels per km²
        
        Returns:
            area_km2: estimated affected area
        """
        pixel_count = mask.sum()
        area_km2 = (pixel_count * pixel_to_km2) / 100  # Approximate
        return area_km2
    
    def calculate_severity(self, mask):
        """
        Calculate severity score (0-10)
        Based on percentage of image affected
        """
        total_pixels = mask.size
        affected_pixels = mask.sum()
        affected_percent = (affected_pixels / total_pixels) * 100
        
        # Scale to 0-10
        severity = min(10, (affected_percent / 10))
        return severity
    
    def visualize_mask(self, original_image, mask, alpha=0.5):
        """
        Create visualization overlay
        
        Args:
            original_image: (H, W, 3) original image [0, 1]
            mask: (H, W) binary mask
            
        Returns:
            overlay: (H, W, 3) visualization
        """
        # Convert to 0-255
        img_viz = (original_image * 255).astype(np.uint8)
        
        # Create red overlay for disaster area
        overlay = img_viz.copy()
        overlay[mask == 1] = [255, 0, 0]  # Red for disaster
        
        # Blend
        result = cv2.addWeighted(img_viz, 1 - alpha, overlay, alpha, 0)
        
        return result


if __name__ == "__main__":
    # Test segmenter
    import numpy as np
    
    segmenter = DisasterSegmenter(device='cpu')
    
    # Create dummy image
    dummy_image = torch.randn(1, 3, 512, 512)
    
    # Predict
    mask, conf = segmenter.predict(dummy_image)
    
    print(f"✅ Segmentation test successful")
    print(f"  Mask shape: {mask.shape}")
    print(f"  Confidence: {conf:.2%}")
    print(f"  Affected pixels: {mask.sum()}")




