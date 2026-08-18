# Demo Data

Pre-loaded satellite imagery for hackathon demo & testing.

## Folder Structure

### /flood
- `before.png` — Satellite image before flooding
- `after.png` — Satellite image after flooding  
- `result.json` — Expected analysis output

### /wildfire
- `before.png` — Pre-fire satellite image
- `after.png` — Post-fire satellite image
- `result.json` — Expected analysis output

### /landslide
- `before.png` — Before landslide event
- `after.png` — After landslide event
- `result.json` — Expected analysis output

---

## Usage

Place actual satellite images here (PNG/TIF format, ~512x512 or larger).

These images will be preloaded in the UI for quick demo testing without requiring manual uploads.

### Example result.json format:
```json
{
  "disaster_type": "flood",
  "confidence": 0.94,
  "severity": 8.5,
  "affected_area_km2": 24.3,
  "before_area_km2": 12.1,
  "after_area_km2": 36.4,
  "expansion_percent": 201.0,
  "buildings_affected": 847,
  "roads_affected": 23,
  "hospitals_affected": 2,
  "priority": "CRITICAL"
}
```

---

**Tip**: For Flood before/after images, search publicly available satellite imagery from recent flood events (e.g., India floods 2023, Pakistan floods 2022, etc. through Sentinel-2 or USGS archives).
