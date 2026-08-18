from enum import Enum
from typing import Optional, Dict
from pydantic import BaseModel, Field
from app.schemas.geometry import GeoJSONGeometry
from app.schemas.risk import RiskBreakdown

class ZonePriority(str, Enum):
    CRITICAL = "CRITICAL"
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"

class RiskZone(BaseModel):
    """
    Reusable Pydantic model representing a specific risk zone with zone-level risk assessment.
    """
    zone_id: str = Field(..., description="Unique identifier for the zone (e.g. Z001, Z002)")
    geometry: Optional[GeoJSONGeometry] = Field(None, description="Geographic boundaries of the zone (Polygon)")
    
    # Zone-level risk factors (normalized 0–1)
    flood_severity: float = Field(..., ge=0, le=1, description="Normalized flood severity in this zone")
    building_exposure: float = Field(..., ge=0, le=1, description="Fraction of buildings affected in this zone")
    road_disruption: float = Field(..., ge=0, le=1, description="Fraction of road length affected in this zone")
    critical_facility_exposure: float = Field(..., ge=0, le=1, description="Fraction of facilities affected in this zone")
    
    # Risk score and priority
    risk_score: float = Field(..., ge=0, le=10, description="Calculated risk score for the zone (0-10)")
    priority: str = Field(..., description="Priority category (LOW/MODERATE/HIGH/VERY_HIGH/CRITICAL)")
    
    # Explainable breakdown
    risk_breakdown: Optional[RiskBreakdown] = Field(None, description="Per-factor contribution breakdown")
    
    # Impact counts
    affected_buildings: int = Field(..., ge=0, description="Number of buildings affected in this zone")
    affected_road_length_km: float = Field(..., ge=0, description="Total affected road length in kilometers")
    affected_facilities: int = Field(..., ge=0, description="Number of critical facilities affected in this zone")
