"""
Create sample satellite images for testing
"""
import cv2
import numpy as np
from pathlib import Path

# Create directories
Path("ml/demo/flood").mkdir(parents=True, exist_ok=True)
Path("ml/demo/wildfire").mkdir(parents=True, exist_ok=True)
Path("ml/demo/landslide").mkdir(parents=True, exist_ok=True)

print("Creating sample satellite images...")

# Create sample images
for disaster_type in ["flood", "wildfire", "landslide"]:
    # Create realistic-looking satellite image (512x512)
    image = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
    
    # Add some patterns to make them look like real satellite data
    if disaster_type == "flood":
        # Blue tones for water
        image[:, :, 2] = np.clip(image[:, :, 2] * 1.5, 0, 255)  # More red
        image[:, :, 0] = np.clip(image[:, :, 0] * 0.7, 0, 255)  # Less blue
        cv2.rectangle(image, (100, 100), (400, 400), (200, 100, 50), -1)
        
    elif disaster_type == "wildfire":
        # Orange/red tones for fire
        image[:, :, 2] = np.clip(image[:, :, 2] * 1.8, 0, 255)  # More red
        image[:, :, 1] = np.clip(image[:, :, 1] * 1.2, 0, 255)  # More green
        cv2.rectangle(image, (150, 150), (350, 350), (100, 50, 180), -1)
        
    elif disaster_type == "landslide":
        # Brown/gray tones for land
        image[:, :, 1] = np.clip(image[:, :, 1] * 0.8, 0, 255)  # Less green
        cv2.rectangle(image, (50, 50), (450, 450), (100, 140, 180), -1)
    
    # Save
    filepath = f"ml/demo/{disaster_type}/before.png"
    cv2.imwrite(filepath, image)
    print(f"✅ Created: {filepath}")

print("\n🎉 Sample images created!")
print("Now test with: python ml/inference/predict.py")
