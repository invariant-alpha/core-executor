import pytest
from core_executor.saga_manager import SagaManager

def test_saga_lifecycle():
    manager = SagaManager()
    
    # Init
    saga = manager.create_saga("corr_1", "content_generation", {"target_platform": "youtube"})
    assert saga.status == "running"
    assert saga.step_current == "init"
    
    # Advance
    saga = manager.advance_saga("corr_1", "waiting_ai", {"ai_prompt": "hello"})
    assert saga.step_current == "waiting_ai"
    assert saga.data["ai_prompt"] == "hello"
    
    # Complete
    saga = manager.complete_saga("corr_1", {"result_url": "http://x"})
    assert saga.status == "completed"
    assert saga.data["result_url"] == "http://x"

def test_saga_failure():
    manager = SagaManager()
    manager.create_saga("corr_2", "platform_sync")
    
    saga = manager.fail_saga("corr_2", "Timeout error")
    assert saga.status == "failed"
    assert saga.error == "Timeout error"

def test_saga_escalation():
    manager = SagaManager()
    manager.create_saga("corr_3", "platform_sync")
    
    saga = manager.escalate_saga("corr_3", "Captcha required")
    assert saga.status == "escalated"
    assert saga.error == "Captcha required"
