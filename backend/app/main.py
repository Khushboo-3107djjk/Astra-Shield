"""
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, analysis
from app.api.errors import APIError, api_error_handler

app = FastAPI(
    title="ASTRA-SHIELD API",
    description="AI-Powered Satellite Disaster Intelligence",
    version="1.0.0"
)

# Exception handlers
app.add_exception_handler(APIError, api_error_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "ASTRA-SHIELD API",
        "version": "1.0.0",
        "status": "online"
    }

app.include_router(health.router, prefix="/api")
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
