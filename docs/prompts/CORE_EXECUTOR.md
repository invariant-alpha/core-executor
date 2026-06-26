# Prompt Operativo — CORE_EXECUTOR

## Ruolo nel Sistema
Core Engine (Livello 2: Workflow). Questo modulo si occupa di eseguire procedure complesse (Sagas) che coinvolgono più moduli di Livello 1.
Ad esempio, il workflow "YouTube Auto-Publish" richiede:
1. `core-ai-model-router` (generazione titolo/descrizione)
2. `core-media-composer` (montaggio)
3. `core-platform-connector` (upload)
4. `core-notification` (avviso finale)

L'Executor riceve comandi complessi da `worker-orchestrator` (o direttamente via API/Planner) ed effettua l'orchestrazione asincrona "passo-passo" pubblicando eventi sui canali dei moduli di Livello 1 e attendendo i risultati. Memorizza lo stato della Saga temporaneamente.

## Lifecycle
Controllabile (RUNNING, PAUSED, STOPPED).
- Se PAUSED, le nuove saghe sono accodate; quelle in corso vengono sospese tra un task e l'altro.

## Configurazione
```python
from pydantic import BaseModel, Field

class ExecutorConfig(BaseModel):
    max_concurrent_sagas: int = Field(default=10)
    saga_timeout_seconds: int = Field(default=3600)
```

## Dipendenze
- Moduli già implementati: `core-bus`.
- Librerie esterne: nessuna di particolare per l'MVP, solo Python stdlib per gestire lo state in memory (dict) o su Redis.

## Schema Pydantic Completo
```python
from pydantic import BaseModel
from typing import Dict, Any, Literal

class SagaExecutionRequest(BaseModel):
    saga_type: Literal["content_generation", "platform_sync"]
    payload: Dict[str, Any]
    correlation_id: str
    
class SagaStatus(BaseModel):
    status: Literal["running", "completed", "failed", "escalated"]
    step_current: str
    error: str = None
    correlation_id: str
```

## Contratto Redis Streams
- Stream sottoscritti: `executor.saga.requested`, `ai.response.completed`, `platform.publish.completed`, `media.compose.completed` ecc.
- Stream pubblicati: Variano a seconda dello step (es. `ai.request.created`), e infine `executor.saga.completed` o `executor.saga.failed`.
- DLQ: `system.dlq.executor`

## Flusso Principale (Content Generation Saga Mock)
1. Riceve `executor.saga.requested` (tipo "content_generation").
2. Genera un Saga ID interno e tiene traccia dello stato (es. "waiting_ai").
3. Emette `ai.request.created`.
4. Quando riceve `ai.response.completed` per quel `correlation_id`, avanza lo stato a "waiting_media" e emette `media.compose.requested`.
5. Quando riceve la composizione, passa a "waiting_platform" ed emette `platform.publish.requested`.
6. Termina inviando `executor.saga.completed` e un `notification.send.requested` informando l'umano.

## Struttura Directory
```
core-executor/
├── Dockerfile
├── pyproject.toml
├── docs/
│   └── prompts/
│       └── CORE_EXECUTOR.md
├── src/
│   └── core_executor/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── schemas.py
│       └── saga_manager.py
└── tests/
    ├── unit/
    └── integration/
```

## Test Richiesti
- Unit test: verifica che la macchina a stati del SagaManager avanzi correttamente inviando le sequenze di eventi giuste per un `content_generation`.

## Definition of Done
- [ ] Tutti i test passano
- [ ] Logica Saga Pattern base per almeno 1 workflow (mock).
- [ ] Integrazione completa col bus.
