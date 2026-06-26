from pydantic import BaseModel
from typing import Dict, Any, Literal, Optional

class SagaExecutionRequest(BaseModel):
    saga_type: Literal["content_generation", "platform_sync"]
    payload: Dict[str, Any]
    correlation_id: str
    
class SagaStatus(BaseModel):
    status: Literal["running", "completed", "failed", "escalated"]
    step_current: str
    error: Optional[str] = None
    correlation_id: str
    data: dict = {}
