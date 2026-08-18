# Backend
## FastAPI Server for ASTRA-SHIELD

This is the server-side application handling:
- API endpoints for image analysis
- Geospatial impact calculation
- Risk zone prioritization
- Emergency response recommendations

### Structure
```
app/
├── api/                    # Route handlers
├── models/                 # Database models
├── services/               # Business logic
│   ├── ai_service.py       # ML model integration
│   ├── geo_service.py      # Geospatial analysis
│   ├── impact_service.py   # Infrastructure impact
│   ├── risk_service.py     # Risk assessment
│   └── response_service.py # Response generation
├── schemas/                # Pydantic models
└── utils/                  # Helpers
```

### Setup
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### API Endpoints
- `POST /api/analyze` — Analyze satellite images
- `GET /api/results/{id}` — Get analysis results
- `POST /api/impact` — Calculate impact metrics
- `GET /api/zones/{disaster_type}` — Get risk zones
