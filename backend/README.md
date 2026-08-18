# ASTRA-SHIELD Backend

This is the FastAPI backend foundation for the ASTRA-SHIELD satellite disaster monitoring system.
Currently, this is a clean foundation focusing on the core structure before adding ML/Geospatial services.

## Development Setup

### 1. Create a virtual environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install requirements
```bash
pip install -r requirements.txt
```

### 3. Start the FastAPI server
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. API Documentation
Swagger UI documentation is available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Available Endpoints
- `GET /` — API Status
- `GET /api/health` — Health check endpoint

### Testing
To run the tests:
```bash
pytest
```
