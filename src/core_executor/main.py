import asyncio
import logging
import uuid
from datetime import datetime

try:
    from core_bus.client import RedisBusClient
    from core_bus.schemas import EventEnvelope
except ImportError:
    RedisBusClient = None
    EventEnvelope = None

from .config import ExecutorConfig
from .schemas import SagaExecutionRequest
from .saga_manager import SagaManager

logger = logging.getLogger(__name__)

async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting core-executor...")

    config = ExecutorConfig()
    manager = SagaManager()
    
    if not RedisBusClient:
        logger.error("core-bus missing. Running without Bus.")
        return

    bus_client = RedisBusClient()
    await bus_client.connect()

    async def emit_event(event_type: str, payload: dict, corr_id: str):
        env = EventEnvelope(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source_module="core-executor",
            timestamp=datetime.utcnow(),
            correlation_id=corr_id,
            payload=payload
        )
        await bus_client.publish(event_type, env)

    async def on_saga_requested(envelope: EventEnvelope):
        req = SagaExecutionRequest.model_validate(envelope.payload)
        logger.info(f"Starting saga {req.saga_type} ({req.correlation_id})")
        
        manager.create_saga(req.correlation_id, req.saga_type, initial_data=req.payload)
        
        if req.saga_type == "content_generation":
            manager.advance_saga(req.correlation_id, "waiting_ai")
            await emit_event("ai.request.created", {
                "modality": "text",
                "prompt": req.payload.get("topic", "Generate content"),
                "correlation_id": req.correlation_id
            }, req.correlation_id)
        else:
            manager.fail_saga(req.correlation_id, f"Unknown saga type {req.saga_type}")

    async def on_ai_completed(envelope: EventEnvelope):
        saga = manager.get_saga(envelope.correlation_id)
        if not saga or saga.status != "running" or saga.step_current != "waiting_ai":
            return
            
        logger.info(f"Saga {saga.correlation_id}: AI finished, starting Media")
        manager.advance_saga(saga.correlation_id, "waiting_media", {"ai_content": envelope.payload.get("content")})
        
        await emit_event("media.compose.requested", {
            "assets": [{"type": "text", "content": envelope.payload.get("content")}],
            "composition_spec": {},
            "correlation_id": saga.correlation_id
        }, saga.correlation_id)

    async def on_media_completed(envelope: EventEnvelope):
        saga = manager.get_saga(envelope.correlation_id)
        if not saga or saga.status != "running" or saga.step_current != "waiting_media":
            return
            
        logger.info(f"Saga {saga.correlation_id}: Media finished, starting Platform Publish")
        manager.advance_saga(saga.correlation_id, "waiting_platform", {"media_url": envelope.payload.get("storage_url")})
        
        await emit_event("platform.publish.requested", {
            "platform": saga.data.get("target_platform", "youtube"),
            "operation": "publish",
            "payload": {"url": envelope.payload.get("storage_url"), "title": "Auto Gen"},
            "correlation_id": saga.correlation_id
        }, saga.correlation_id)

    async def on_platform_completed(envelope: EventEnvelope):
        saga = manager.get_saga(envelope.correlation_id)
        if not saga or saga.status != "running" or saga.step_current != "waiting_platform":
            return
            
        logger.info(f"Saga {saga.correlation_id}: Publish finished! Saga Completed.")
        manager.complete_saga(saga.correlation_id)
        
        await emit_event("executor.saga.completed", {
            "status": "completed",
            "correlation_id": saga.correlation_id
        }, saga.correlation_id)
        
        # Invia notifica all'umano
        await emit_event("notification.send.requested", {
            "message": f"Saga {saga.correlation_id} completata con successo!",
            "level": "info",
            "source_module": "core-executor",
            "correlation_id": saga.correlation_id
        }, saga.correlation_id)

    async def on_failure(envelope: EventEnvelope):
        saga = manager.get_saga(envelope.correlation_id)
        if not saga or saga.status != "running":
            return
            
        logger.error(f"Saga {saga.correlation_id}: Failed at {saga.step_current}")
        manager.fail_saga(saga.correlation_id, envelope.payload.get("error", "Unknown error"))
        
        await emit_event("executor.saga.failed", {
            "status": "failed",
            "error": envelope.payload.get("error", "Unknown error"),
            "correlation_id": saga.correlation_id
        }, saga.correlation_id)
        
        await emit_event("notification.send.requested", {
            "message": f"Saga {saga.correlation_id} FALLITA allo step {saga.step_current}. Errore: {envelope.payload.get('error')}",
            "level": "critical",
            "source_module": "core-executor",
            "correlation_id": saga.correlation_id
        }, saga.correlation_id)

    await bus_client.subscribe("executor.saga.requested", "executor_group", on_saga_requested)
    await bus_client.subscribe("ai.response.completed", "executor_group", on_ai_completed)
    await bus_client.subscribe("media.compose.completed", "executor_group", on_media_completed)
    await bus_client.subscribe("platform.publish.completed", "executor_group", on_platform_completed)
    
    # Catch all failures
    await bus_client.subscribe("ai.response.failed", "executor_group", on_failure)
    await bus_client.subscribe("media.compose.failed", "executor_group", on_failure)
    await bus_client.subscribe("platform.action.failed", "executor_group", on_failure)
    await bus_client.subscribe("platform.escalation.required", "executor_group", on_failure) # We map escalation to failure for now

    logger.info("core-executor is listening for events...")
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Shutting down core-executor...")
    finally:
        await bus_client.close()

if __name__ == "__main__":
    asyncio.run(main())
