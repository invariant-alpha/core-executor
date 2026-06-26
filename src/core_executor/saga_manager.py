import logging
from typing import Dict, Any, List, Optional
from .schemas import SagaStatus

logger = logging.getLogger(__name__)

class SagaManager:
    """
    Gestisce lo stato in memoria delle Saghe. 
    In produzione, questo stato andrebbe su Redis (core-db).
    """
    def __init__(self):
        self._sagas: Dict[str, SagaStatus] = {}

    def create_saga(self, correlation_id: str, saga_type: str, initial_data: dict = None) -> SagaStatus:
        status = SagaStatus(
            status="running",
            step_current="init",
            correlation_id=correlation_id,
            data=initial_data or {}
        )
        self._sagas[correlation_id] = status
        return status

    def get_saga(self, correlation_id: str) -> Optional[SagaStatus]:
        return self._sagas.get(correlation_id)

    def advance_saga(self, correlation_id: str, next_step: str, update_data: dict = None) -> Optional[SagaStatus]:
        saga = self.get_saga(correlation_id)
        if not saga:
            return None
        
        saga.step_current = next_step
        if update_data:
            saga.data.update(update_data)
            
        return saga
        
    def complete_saga(self, correlation_id: str, final_data: dict = None) -> Optional[SagaStatus]:
        saga = self.get_saga(correlation_id)
        if not saga:
            return None
            
        saga.status = "completed"
        if final_data:
            saga.data.update(final_data)
        return saga
        
    def fail_saga(self, correlation_id: str, error: str) -> Optional[SagaStatus]:
        saga = self.get_saga(correlation_id)
        if not saga:
            return None
            
        saga.status = "failed"
        saga.error = error
        return saga
        
    def escalate_saga(self, correlation_id: str, reason: str) -> Optional[SagaStatus]:
        saga = self.get_saga(correlation_id)
        if not saga:
            return None
            
        saga.status = "escalated"
        saga.error = reason
        return saga
