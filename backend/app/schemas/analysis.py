from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.zone import RiskZone
from app.schemas.impact import ImpactSummary
from app.schemas.risk import RiskSummary

class DisasterType(str, Enum):
    FLOOD = "flood"
    WILDFIRE = "wildfire"
    CYCLONE = "cyclone"
    LANDSLIDE = "landslide"
    EARTHQUAKE = "earthquake"
    DROUGHT = "drought"

class MLAnalysisInput(BaseModel):
    """
    Schema representing the input from Person 1's ML pipeline.
    """
    analysis_id: str = Field(..., description="Unique identifier for this analysis run")
    disaster_type: DisasterType = Field(..., description="Type of disaster detected (e.g., flood)")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence score (0 to 1)")
    severity: float = Field(..., ge=0, le=1, description="Normalized severity score (0 to 1)")
    affected_area_km2: float = Field(..., ge=0, description="Affected area in square kilometers")
    mask_path: Optional[str] = Field(None, description="Path or reference to the generated mask image/data")

class TimelineObservation(BaseModel):
    """
    Observation for a specific point in time to track disaster evolution.
    """
    timestamp: datetime = Field(..., description="Date and time of the observation")
    affected_area_km2: float = Field(..., ge=0, description="Affected area at this point in time (sq km)")
    severity: float = Field(..., ge=0, le=1, description="Severity at this point in time (0 to 1)")

class AnalysisSummary(BaseModel):
    """
    High-level summary of the analysis results.
    """
    analysis_id: str = Field(..., description="Unique identifier for the analysis")
    disaster_type: DisasterType = Field(..., description="Type of disaster")
    location: str = Field(..., description="General location description")
    confidence: float = Field(..., ge=0, le=1, description="Overall AI confidence (0 to 1)")
    severity: float = Field(..., ge=0, le=1, description="Overall severity (0 to 1)")
    affected_area_km2: float = Field(..., ge=0, description="Total affected area in sq km")

class AnalysisResponse(BaseModel):
    """
    Schema representing the final analysis result that Person 3's frontend consumes.
    """
    summary: AnalysisSummary = Field(..., description="High-level summary of the analysis")
    impact: ImpactSummary = Field(..., description="Infrastructure impact details")
    risk: RiskSummary = Field(..., description="Risk assessment details")
    zones: List[RiskZone] = Field(..., description="Breakdown by specific risk zones")
    timeline: List[TimelineObservation] = Field(default_factory=list, description="Historical timeline observations")
