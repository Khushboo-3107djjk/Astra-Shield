from pydantic import BaseModel, Field
from app.schemas.zone import ZonePriority

class RiskSummary(BaseModel):
    """
    Summary of the overall risk assessment.
    """
    overall_risk_score: float = Field(..., ge=0, le=10, description="Overall calculated risk score (0-10)")
    overall_priority: ZonePriority = Field(..., description="Overall priority level for emergency response")
