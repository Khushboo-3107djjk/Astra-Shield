import os
import shutil
import csv
import random
import hashlib
from pathlib import Path
from PIL import Image

HAS_PHASH = False
print("⚠️ Perceptual deduplication disabled to speed up processing. Using exact SHA-256 only.")

# Configuration
TARGET_CLASSES = ['normal', 'flood', 'earthquake', 'cyclone']
DATASET_DIR = Path(__file__).parent
METADATA_FILE = DATASET_DIR / 'metadata.csv'

# Split ratios
TRAIN_RATIO = 0.6
VAL_RATIO = 0.2
TEST_RATIO = 0.2

# Explicit Mapping: dataset_name -> {original_folder_name: target_class}
# These are the VERIFIED exact folder names inside each raw dataset.
DATASET_MAPPING = {
    # Cyclone/Wildfire/Flood/Earthquake DB by rupakroy
    # Only mapping the 4 active classes. Wildfire is intentionally excluded.
    "rupakroy": {
        "Cyclone":    "cyclone",
        "Flood":      "flood",
        "Earthquake": "earthquake",
    },
    # EuroSAT - Sentinel-2 satellite imagery ✅ - used for "Normal" class
    "EuroSAT": {
        "Forest":               "normal",
        "AnnualCrop":           "normal",
        "PermanentCrop":        "normal",
        "Pasture":              "normal",
        "SeaLake":              "normal",
        "Residential":          "normal",
        "Industrial":           "normal",
        "River":                "normal",
        "HerbaceousVegetation": "normal"
    }
}

# Domain tracking: which source is satellite vs mixed
DOMAIN_MAP = {
    "rupakroy": "mixed_aerial_web",
    "EuroSAT":  "satellite"
}

# NOTE: Wildfire, Landslide, Drought are excluded from this pilot.
# The 7-class architecture remains in place for future extension.

class DatasetCurator:
    def __init__(self, raw_data_paths):
        """
        raw_data_paths: dict mapping Kaggle dataset names to their local downloaded paths
        Example: {'xBD_Dataset': 'raw/xBD/', 'Landslide4Sense': 'raw/landslide/'}
        """
        self.raw_data_paths = raw_data_paths
        self.image_hashes = set()  # For deduplication
        
    def _get_image_hash(self, filepath):
        """Returns (sha256_hash, phash) for deduplication"""
        try:
            # 1. Exact duplicate detection (SHA-256)
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            exact_hash = sha256_hash.hexdigest()
            
            # 2. Perceptual duplicate detection (pHash)
            perc_hash = None
            if HAS_PHASH:
                with Image.open(filepath) as img:
                    perc_hash = str(imagehash.phash(img))
                    
            return (exact_hash, perc_hash)
        except Exception:
            return (None, None)

    def _is_duplicate(self, filepath):
        exact_hash, perc_hash = self._get_image_hash(filepath)
        
        if exact_hash is None:
            return True # If we can't hash it, consider it bad/duplicate
            
        if exact_hash in self.image_hashes:
            return True
            
        if perc_hash and perc_hash in self.image_hashes:
            return True
            
        # Add to seen hashes
        self.image_hashes.add(exact_hash)
        if perc_hash:
            self.image_hashes.add(perc_hash)
            
        return False

    def inspect(self):
        """Phase 1: Inspect available images without copying/structuring"""
        print("🔍 PHASE 1: INSPECTION")
        print("-" * 75)
        print(f"{'Class':<12} | {'Source':<15} | {'Orig Label':<15} | {'Available':<10} | {'Usable':<10}")
        print("-" * 75)
        
        class_counts = {c: 0 for c in TARGET_CLASSES}
        
        for source, path in self.raw_data_paths.items():
            if not Path(path).exists():
                print(f"⚠️ Source {source} not found at {path}. Please download first.")
                continue
                
            mapping = DATASET_MAPPING.get(source, {})
            
            for orig_label, target_class in mapping.items():
                cls_path = Path(path) / orig_label
                if cls_path.exists():
                    images = list(cls_path.glob('*.png')) + list(cls_path.glob('*.jpg')) + list(cls_path.glob('*.tif'))
                    usable = [img for img in images if self._is_valid_image(img)]
                    print(f"{target_class:<12} | {source:<15} | {orig_label:<15} | {len(images):<10} | {len(usable):<10}")
                    class_counts[target_class] += len(usable)
                    
        print("-" * 75)
        
        missing = [c for c, count in class_counts.items() if count == 0]
        if missing:
            print(f"❌ CRITICAL GAPS DETECTED: Missing data for {missing}")
            print("🛑 STOPPING. Please source datasets for missing classes before proceeding.")
            return False
            
        print("✅ All 7 classes have available candidate images.")
        return True

    def _is_valid_image(self, filepath):
        return True

    def curate(self, target_per_class=100):
        """Phase 2: Extract, Deduplicate, Split, and Record"""
        print(f"\n🚀 PHASE 2: CURATING PILOT DATASET ({target_per_class} per class)")
        
        # Initialize CSV with domain column
        with open(METADATA_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['image_path', 'class', 'source_dataset', 'original_label', 'domain', 'split'])
        
        for cls in TARGET_CLASSES:
            candidates = []
            
            for source, path in self.raw_data_paths.items():
                mapping = DATASET_MAPPING.get(source, {})
                for orig_label, target_class in mapping.items():
                    if target_class == cls:
                        cls_path = Path(path) / orig_label
                        if cls_path.exists():
                            images = list(cls_path.glob('*.png')) + list(cls_path.glob('*.jpg')) + list(cls_path.glob('*.tif'))
                            for img in images:
                                if self._is_valid_image(img):
                                    candidates.append((img, source, orig_label))
            
            random.shuffle(candidates)
            
            selected = []
            for img_path, source, orig_label in candidates:
                if len(selected) >= target_per_class:
                    break
                if not self._is_duplicate(img_path):
                    selected.append((img_path, source, orig_label))
            
            if len(selected) == 0:
                print(f"❌ {cls:<12} | No usable images found. This class will be SKIPPED.")
                continue
            if len(selected) < target_per_class:
                print(f"⚠️  {cls:<12} | Only {len(selected)} unique usable images (Target: {target_per_class})")
                
            train_idx = int(len(selected) * TRAIN_RATIO)
            val_idx = train_idx + int(len(selected) * VAL_RATIO)
            
            train_set = selected[:train_idx]
            val_set = selected[train_idx:val_idx]
            test_set = selected[val_idx:]
            
            self._process_split(train_set, cls, 'train')
            self._process_split(val_set, cls, 'val')
            self._process_split(test_set, cls, 'test')
            
            print(f"✅ {cls:<12} | Selected: {len(selected)} (Train: {len(train_set)}, Val: {len(val_set)}, Test: {len(test_set)})")

    def _process_split(self, dataset, cls, split_name):
        split_dir = DATASET_DIR / split_name / cls
        split_dir.mkdir(parents=True, exist_ok=True)
        
        with open(METADATA_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for i, (src_path, source, orig_label) in enumerate(dataset):
                domain = DOMAIN_MAP.get(source, "unknown")
                dest_filename = f"{source}_{orig_label}_{i}{src_path.suffix}"
                dest_path = split_dir / dest_filename
                shutil.copy2(src_path, dest_path)
                relative_path = f"{split_name}/{cls}/{dest_filename}"
                writer.writerow([relative_path, cls, source, orig_label, domain, split_name])


if __name__ == "__main__":
    RAW_DATA = {
        "rupakroy": str(DATASET_DIR / "raw" / "rupakroy" / "Cyclone_Wildfire_Flood_Earthquake_Database" / "Cyclone_Wildfire_Flood_Earthquake_Database"),
        "EuroSAT":  str(DATASET_DIR / "raw" / "EuroSAT" / "EuroSAT"),
    }
    
    curator = DatasetCurator(RAW_DATA)
    
    print("\n" + "=" * 75)
    print("ASTRA-SHIELD — 4-Class Disaster Classifier Pilot")
    print("Classes: normal | flood | earthquake | cyclone")
    print("⚠️  rupakroy source is mixed aerial/web images, NOT purely satellite.")
    print("   Domain is recorded in metadata.csv for transparency.")
    print("=" * 75 + "\n")

    ok = curator.inspect()
    
    if ok:
        curator.curate(target_per_class=100)
        print("\n🎉 Pilot dataset (100/class) curated! Metadata saved to metadata.csv")
        print("➡️  Next: Run `python ml/training/train_classifier.py`")
    else:
        print("\n🛑 Fix the gaps above before curating.")



