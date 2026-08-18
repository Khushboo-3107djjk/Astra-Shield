from pydantic import BaseModel, Field

class ImpactSummary(BaseModel):
    """
    Summary of infrastructure impact caused by the disaster.
    """
    affected_buildings: int = Field(..., ge=0, description="Total number of buildings affected")
    affected_roads: int = Field(..., ge=0, description="Total number of roads affected")
    affected_critical_facilities: int = Field(..., ge=0, description="Total number of critical facilities affected")
