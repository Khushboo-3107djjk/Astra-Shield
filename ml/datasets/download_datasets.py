"""
ASTRA-SHIELD Dataset Download Script
=====================================
Downloads and extracts the 4 datasets for the Option B pilot.

Requires:
  pip install kaggle
  Place your kaggle.json at C:/Users/<YourName>/.kaggle/kaggle.json

Run:
  python ml/datasets/download_datasets.py
"""

import subprocess
import sys
from pathlib import Path

RAW_DIR = Path(__file__).parent / "raw"


def run(cmd):
    print(f"\n>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ ERROR:\n{result.stderr}")
        return False
    print(result.stdout)
    return True


def download_datasets():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    datasets = [
        {
            "name": "Cyclone/Wildfire/Flood/Earthquake (Mixed, web-scraped)",
            "kaggle_id": "rupakroy/cyclone-wildfire-flood-earthquake-database",
            "dest": RAW_DIR / "rupakroy",
            "domain": "mixed_aerial_web",
            "covers": ["Cyclone", "Wildfire", "Flood", "Earthquake"],
            "is_satellite": False
        },
        {
            "name": "Fire/Flood/Smoke/Landslide/Earthquake (Mixed, web-scraped)",
            "kaggle_id": "igig2020/fire-flood-smoke-landslide-earthquake",
            "dest": RAW_DIR / "igig2020",
            "domain": "mixed_aerial_web",
            "covers": ["Fire", "Flood", "Landslide", "Earthquake"],
            "is_satellite": False
        },
        {
            "name": "Landslide4Sense (Sentinel-2 Satellite ✅)",
            "kaggle_id": "thedevastator/landslide4sense",
            "dest": RAW_DIR / "Landslide4Sense",
            "domain": "satellite",
            "covers": ["landslide"],
            "is_satellite": True
        },
        {
            "name": "EuroSAT (Sentinel-2 Satellite ✅ - for Normal class)",
            "kaggle_id": "apollo2506/eurosat-dataset",
            "dest": RAW_DIR / "EuroSAT",
            "domain": "satellite",
            "covers": ["normal"],
            "is_satellite": True
        }
    ]

    print("=" * 70)
    print("ASTRA-SHIELD: Dataset Download (Option B Pilot)")
    print("=" * 70)
    print("\nDataset Summary:")
    for ds in datasets:
        sat = "✅ Satellite" if ds["is_satellite"] else "⚠️  Mixed/Web"
        print(f"  [{sat}] {ds['name']}")
        print(f"         Kaggle ID : {ds['kaggle_id']}")
        print(f"         Covers    : {ds['covers']}")
        print()

    print("\n⚠️  NOTE: rupakroy & igig2020 contain mixed ground+aerial photos.")
    print("   Their domain will be recorded as 'mixed_aerial_web' in metadata.csv.")
    print("   Model predictions from these classes will be tagged accordingly.")
    print("=" * 70)

    for ds in datasets:
        dest = ds["dest"]
        dest.mkdir(parents=True, exist_ok=True)
        print(f"\n📥 Downloading: {ds['name']}")
        success = run(
            f'kaggle datasets download -d {ds["kaggle_id"]} -p "{dest}" --unzip'
        )
        if success:
            print(f"✅ Downloaded to {dest}")
        else:
            print(f"❌ Failed to download {ds['name']}. Check your kaggle.json credentials.")

    print("\n✅ All downloads complete.")
    print("➡️  Next: Run `python ml/datasets/curate_dataset.py` to inspect and curate.")


if __name__ == "__main__":
    download_datasets()
