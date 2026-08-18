"""
Data Preprocessing Pipeline
Handles satellite image loading, normalization, and augmentation
"""

import cv2
import numpy as np
from pathlib import Path
import json


class SatelliteImagePreprocessor:
    """Preprocess satellite images for model training"""
    
    def __init__(self, img_size=512, normalize=True):
        self.img_size = img_size
        self.normalize = normalize
    
    def load_image(self, image_path):
        """
        Load satellite image (GeoTIFF, PNG, JPG)
        
        Args:
            image_path: Path to image file
            
        Returns:
            numpy array (H, W, 3) or (H, W, C)
        """
        image_path = Path(image_path)
        
        if image_path.suffix in ['.tif', '.tiff']:
            # For GeoTIFF (multi-band satellite)
            import rasterio
            with rasterio.open(image_path) as src:
                # Read first 3 bands (RGB or NIR-R-G)
                data = src.read([1, 2, 3])  # (C, H, W)
                image = np.transpose(data, (1, 2, 0))  # (H, W, C)
        else:
            # For standard image formats
            image = cv2.imread(str(image_path))  # BGR
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return image.astype(np.float32)
    
    def load_mask(self, mask_path):
        """
        Load segmentation mask (single channel)
        
        Args:
            mask_path: Path to mask file
            
        Returns:
            numpy array (H, W) with values 0-255 or binary
        """
        mask_path = Path(mask_path)
        
        if mask_path.suffix in ['.tif', '.tiff']:
            import rasterio
            with rasterio.open(mask_path) as src:
                mask = src.read(1)  # Read first band
        else:
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if mask is None:
                raise ValueError(f"Could not load mask: {mask_path}")
        
        return mask.astype(np.uint8)
    
    def resize(self, image, size=None):
        """Resize image to target size"""
        if size is None:
            size = self.img_size
        return cv2.resize(image, (size, size), interpolation=cv2.INTER_LINEAR)
    
    def normalize_image(self, image):
        """Normalize image to [0, 1] range"""
        if image.max() > 1.0:
            image = image / 255.0
        
        # Optional: Standardize (mean=0, std=1)
        # Using ImageNet stats as baseline
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        image = (image - mean) / std
        
        return image.astype(np.float32)
    
    def binarize_mask(self, mask, threshold=128):
        """Convert mask to binary (0 or 1)"""
        return (mask > threshold).astype(np.uint8)
    
    def preprocess(self, image_path, mask_path=None, return_original=False):
        """
        Complete preprocessing pipeline
        
        Returns:
            image: preprocessed image (H, W, 3) in [0, 1] or normalized
            mask: (optional) binary mask (H, W)
            original: (optional) original image for visualization
        """
        # Load
        image = self.load_image(image_path)
        original = image.copy() if return_original else None
        
        # Resize
        image = self.resize(image)
        
        # Normalize
        if self.normalize:
            image = self.normalize_image(image)
        else:
            image = image / 255.0
        
        # Load mask if provided
        mask = None
        if mask_path:
            mask = self.load_mask(mask_path)
            mask = self.resize(mask)
            mask = self.binarize_mask(mask)
        
        if return_original and original is not None:
            original = self.resize(original) / 255.0
            return image, mask, original
        
        return image, mask


# Data augmentation for training
class DataAugmenter:
    """Augment satellite images for training"""
    
    @staticmethod
    def horizontal_flip(image, mask=None, p=0.5):
        """Randomly flip horizontally"""
        if np.random.rand() < p:
            image = cv2.flip(image, 1)  # 1 = horizontal
            if mask is not None:
                mask = cv2.flip(mask, 1)
        return image, mask
    
    @staticmethod
    def vertical_flip(image, mask=None, p=0.5):
        """Randomly flip vertically"""
        if np.random.rand() < p:
            image = cv2.flip(image, 0)  # 0 = vertical
            if mask is not None:
                mask = cv2.flip(mask, 0)
        return image, mask
    
    @staticmethod
    def rotate(image, mask=None, angle_range=15):
        """Random rotation"""
        angle = np.random.uniform(-angle_range, angle_range)
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        image = cv2.warpAffine(image, M, (w, h))
        if mask is not None:
            mask = cv2.warpAffine(mask, M, (w, h))
        
        return image, mask
    
    @staticmethod
    def brightness_contrast(image, brightness_range=0.2, contrast_range=0.2):
        """Adjust brightness and contrast"""
        brightness = np.random.uniform(-brightness_range, brightness_range)
        contrast = np.random.uniform(1 - contrast_range, 1 + contrast_range)
        
        image = np.clip(image * contrast + brightness, 0, 1)
        return image
    
    @staticmethod
    def augment(image, mask=None, p_aug=0.7):
        """Apply random augmentations"""
        if np.random.rand() < p_aug:
            image, mask = DataAugmenter.horizontal_flip(image, mask)
            image, mask = DataAugmenter.vertical_flip(image, mask)
            image, mask = DataAugmenter.rotate(image, mask)
            image = DataAugmenter.brightness_contrast(image)
        
        return image, mask


if __name__ == "__main__":
    # Example usage
    preprocessor = SatelliteImagePreprocessor(img_size=512)
    
    # Load a sample image
    # image, mask = preprocessor.preprocess(
    #     "path/to/image.tif",
    #     "path/to/mask.tif"
    # )
    
    print("✅ Preprocessing pipeline ready")
