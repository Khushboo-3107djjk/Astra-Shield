"""
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ASTRA-SHIELD API",
    description="AI-Powered Satellite Disaster Intelligence",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# TODO: Add API routes
# from app.api import analysis, impact, response
# app.include_router(analysis.router)
# app.include_router(impact.router)
# app.include_router(response.router)
