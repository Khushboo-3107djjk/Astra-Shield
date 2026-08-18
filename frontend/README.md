# Frontend
## React Web Application for ASTRA-SHIELD

This is the client-side interface displaying:
- Mission overview & satellite image upload
- Real-time AI detection results
- Before/After disaster comparison (wow factor!)
- Geospatial impact visualization
- Risk zone prioritization
- Emergency response recommendations

### Structure
```
src/
├── pages/
│   ├── MissionControl.jsx      # Home/overview
│   ├── Analyze.jsx             # Image upload & analysis
│   ├── Detection.jsx           # AI detection results
│   ├── BeforeAfter.jsx         # Disaster evolution (main feature!)
│   ├── Impact.jsx              # Infrastructure impact
│   ├── Risk.jsx                # Risk zones
│   └── Response.jsx            # Emergency actions
├── components/
│   ├── SatelliteUploader.jsx
│   ├── DisasterSelector.jsx
│   ├── ImpactMap.jsx
│   ├── RiskVisualization.jsx
│   └── ...
├── services/
│   └── api.js                  # Backend API calls
└── utils/
    └── helpers.js
```

### Setup
```bash
npm install
npm start
```

### Build
```bash
npm run build
```

### Key Features
- 🛰️ Satellite image upload
- 🤖 AI detection overlay
- ⭐ Before/After slider comparison
- 🗺️ Interactive geospatial map
- 🚨 Risk zone highlighting
- 📊 Statistics dashboard
- 🆘 Emergency alert generation
