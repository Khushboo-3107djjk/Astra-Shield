from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.geometry import GeoJSONGeometry

class ZonePriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RiskZone(BaseModel):
    """
    Reusable Pydantic model representing a specific risk zone.
    """
    zone_id: str = Field(..., description="Unique identifier for the zone")
    risk_score: float = Field(..., ge=0, le=10, description="Calculated risk score for the zone (0-10)")
    priority: ZonePriority = Field(..., description="Priority level for emergency response")
    affected_area_km2: float = Field(..., ge=0, description="Affected area within this zone in square kilometers")
    affected_buildings: int = Field(..., ge=0, description="Number of buildings affected in this zone")
    affected_roads: int = Field(..., ge=0, description="Number of roads affected in this zone")
    critical_facilities: int = Field(..., ge=0, description="Number of critical facilities affected in this zone")
    geometry: Optional[GeoJSONGeometry] = Field(None, description="Geographic boundaries of the zone")
