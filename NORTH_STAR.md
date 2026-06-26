# NORTH STAR — Venture Studio Automatizzato
## Documento Architetturale Fondante v1.3

---

## [SEZIONE 0 — ISTRUZIONI META PER CLAUDE CODE]

Questo documento è il tuo riferimento immutabile. Prima di scrivere una sola riga di codice, devi:

1. **Leggere integralmente** questo documento
2. **Generare autonomamente** il Prompt Operativo per il modulo che stai per implementare, seguendo il template nella Sezione 6
3. **Salvare** il Prompt Operativo generato in `docs/prompts/[NOME_MODULO].md` prima di iniziare l'implementazione
4. **Rileggere** il Prompt Operativo generato e verificare che non violi nessuno dei Dogmi Architetturali della Sezione 2
5. Solo allora: **implementare**

Ogni decisione tecnologica ambigua (non esplicitamente risolta da questo documento) deve essere:
- Presa autonomamente, privilegiando sempre semplicità e disaccoppiamento
- Documentata in `docs/decisions/ADR_[NNN]_[descrizione].md` seguendo il formato Architecture Decision Record

Non chiedere conferma per decisioni di dettaglio. Chiedi conferma solo se una scelta viola un Dogma Architetturale.

---

## [SEZIONE 1 — VISIONE E SCOPO]

### Cos'è il sistema
Un Venture Studio automatizzato basato su architettura a Microservizi Event-Driven (EDA). Funge da holding tecnologica centrale che fornisce infrastruttura, intelligenza, memoria e capacità operativa a tre flussi di business distinti, orchestrati centralmente.

### Obiettivo operativo
Testare, iterare e massimizzare il profitto netto attraverso automazione scalabile e A/B testing continuo, mantenendo i costi fissi vicini allo zero (OpEx vs CapEx).

### I tre flussi di business
Questi non sono moduli software. Sono **configurazioni di orchestrazione** che solo l'Orchestratore conosce e gestisce. Tutti gli altri moduli sono completamente ignari della loro esistenza.

- **Freelance Automation**: monitora piattaforme freelance, valuta opportunità, genera proposte, esegue lavori di sviluppo software in sandbox isolate, consegna il prodotto
- **SFW Content Automation**: analizza trend, genera script, produce e monta contenuti audio/video, pubblica su piattaforme social per monetizzazione
- **NSFW Content Automation**: analogo al precedente, su piattaforme adulti che consentono esplicitamente contenuti AI-labeled; include gestione automatizzata dell'interazione con gli utenti

### Principio fondamentale
**Solo l'Orchestratore conosce i tre flussi di business.** Ogni altro modulo esegue funzioni tecniche pure senza sapere per quale flusso sta operando. Il contesto di business viaggia nel `correlation_id` e nella configurazione dell'Orchestratore, non nella logica dei moduli.

---

## [SEZIONE 2 — DOGMI ARCHITETTURALI]

Questi principi sono **inviolabili**. Nessuna eccezione, nessuna deroga.

### D1 — Disaccoppiamento Totale
Nessun modulo chiama mai direttamente API esterne né accede direttamente ai database. Ogni comunicazione avviene esclusivamente tramite eventi pubblicati sull'Event Bus. I Core Modules (Livello 1) sono gli unici autorizzati a parlare con il mondo esterno.

### D2 — Validazione Rigorosa
Nessun payload viaggia sull'Event Bus senza validazione Pydantic. Ogni evento in ingresso e in uscita da qualsiasi modulo deve aderire a uno schema definito nello Schema Registry. I payload AI devono usare Structured Outputs o post-validazione Pydantic.

### D3 — Moduli Stateless
Nessun modulo ha stato persistente locale. Nessuno scrive su file locali né mantiene variabili globali tra esecuzioni. Letture e scritture avvengono esclusivamente tramite eventi Bus tradotti in operazioni su PostgreSQL.

### D4 — OpEx vs CapEx
Nessun server dedicato 24/7. Si privilegiano servizi serverless, pay-per-use e API a consumo. Il costo fisso mensile deve tendere a zero.

### D5 — Asincronia Totale
Nessuna chiamata sincrona bloccante tra moduli. Tutto è `async/await`. I timeout sono sempre espliciti. Le code sono sempre bounded.

### D6 — Sicurezza per Default
Le credenziali non esistono nel codice sorgente. Mai. Ogni segreto vive nel Vault e viene iniettato a runtime. Il codice è pubblicabile su GitHub pubblico senza esporre nulla.

### D7 — Agnosticismo dei Moduli
Nessun modulo al di fuori dell'Orchestratore contiene riferimenti, nomi, costanti o logiche condizionali legate ai flussi di business. Un modulo non sa — e non deve sapere — quale flusso ha originato la richiesta che sta processando.

### D8 — Configurabilità Universale
Ogni modulo espone il proprio schema di configurazione tramite Pydantic. I parametri operativi (soglie, timeout, limiti, flag) non sono mai hardcoded. La configurazione è modificabile a runtime dal Command Center senza restart del modulo.

### D9 — Lifecycle Controllabile
Ogni modulo non-fondamentale supporta tre stati: `RUNNING`, `PAUSED`, `STOPPED`. I moduli `CORE_IMMUTABLE` (Bus, DB Manager, Vault) non hanno lifecycle controllabile — sono prerequisiti del sistema. I tre flussi di business supportano lifecycle indipendente con graceful pause (i task in esecuzione vengono completati prima della sospensione).

### D10 — Eccezione Bootstrap
L'Auto-Updater Module è l'unica eccezione esplicita a D1. Opera in isolamento totale dagli altri moduli — non usa il Bus, non dipende dal DB Manager, non dipende dal Vault — perché deve poter funzionare anche quando il resto del sistema è parzialmente o totalmente down. È il modulo che garantisce che il sistema stesso possa essere aggiornato e riavviato. Questa eccezione è architetturalmente giustificata e non estendibile ad altri moduli.

---

## [SEZIONE 3 — TOPOLOGIA DEI LIVELLI]

```
┌──────────────────────────────────────────────────────────────────┐
│  LIVELLO 3 — Controllo, Osservabilità, FinOps                    │
│  [Command Center UI]   [AI SRE Module]   [FinOps Module]         │
├──────────────────────────────────────────────────────────────────┤
│  LIVELLO 1 — Core Engine                                         │
│  [Orchestrator]      [AI Model Router]   [Platform Connector]    │
│  [Media Composer]    [Executor]          [Intelligence Module]   │
│  [Notification Module]                  [Mock Module]            │
├──────────────────────────────────────────────────────────────────┤
│  LIVELLO 0 — Infrastruttura e Dati          [CORE_IMMUTABLE]     │
│  [Redis Bus ⚙]   [DB Manager ⚙]   [Vault ⚙]   [Storage Module] │
└──────────────────────────────────────────────────────────────────┘

         ↕ (isolato da tutto — eccezione D10)
   [Auto-Updater Module] ←→ GitHub (Invariant Labs org)

⚙ = CORE_IMMUTABLE: nessun lifecycle controllabile
```

### Struttura multi-repo (Invariant Labs)

Ogni modulo vive in un repository GitHub separato sotto l'organizzazione `invariant-labs`. Il repository `invariant-labs/venture-studio` è il **meta-repo**: contiene solo `NORTH_STAR.md`, `docker-compose.yml`, il file di bootstrap e i riferimenti ai sotto-repo. Ogni modulo può essere aperto e sviluppato indipendentemente in VSCode o PyCharm.

```
GitHub org: invariant-labs/
├── venture-studio          # meta-repo: NORTH_STAR, docker-compose, bootstrap
├── core-bus
├── core-db
├── core-vault
├── core-storage
├── core-mock
├── core-ai-model-router
├── core-platform-connector
├── core-media-composer
├── core-executor
├── core-notification
├── core-intelligence
├── core-orchestrator
├── core-auto-updater
├── control-ui
├── control-sre
└── control-finops
```

---

## [SEZIONE 4 — STACK TECNOLOGICO DEFINITIVO]

| Componente | Tecnologia | Motivazione |
|---|---|---|
| Event Bus | **Redis Streams** | Persistenza nativa, consumer groups, semplicità |
| Database Relazionale | **PostgreSQL 16** | Affidabilità, ecosistema maturo |
| Memoria Vettoriale | **pgvector** (estensione PG) | Zero infrastruttura extra, stesso DB |
| Asset Storage | **Cloudflare R2** | Zero costi egress, compatibile S3, retention policy nativa |
| Vault | **python-dotenv** in dev / **Infisical** in prod | Separazione netta segreti/codice |
| AI Models (testo) | **OpenRouter.ai** | Aggregatore multi-provider, unica API per centinaia di modelli |
| AI Models (media) | **Novita.ai** / **Prodia** (SD-based) | Pay-per-use, modelli uncensored disponibili |
| Platform Interaction | **Playwright** (async) + proxy residenziali rotanti | Stealth, fallback quando mancano API ufficiali |
| Sandbox Esecuzione | **Docker** effimero con seccomp/apparmor | Isolamento totale, creato e distrutto per task |
| Notifiche | **Telegram Bot API** + **IFTTT Webhooks** | Push outbound leggero, HTTP puro |
| Linguaggio | **Python 3.12** | Ecosistema AI/ML, async maturo |
| Validazione | **Pydantic v2** | Standard de facto, performance |
| Testing | **pytest** + **pytest-asyncio** | Compatibilità async nativa |
| Containerizzazione | **Docker** + **Docker Compose** | Riproducibilità ambiente |
| Osservabilità | **Prometheus** + **Grafana** | Metriche + log strutturati |
| Source Control | **GitHub** (org: invariant-labs) | Un repo per modulo, Auto-Updater per sync locale |

---

## [SEZIONE 5 — SISTEMA DI CONFIGURAZIONE E LIFECYCLE]

### 5.1 — Schema di configurazione per modulo

Ogni modulo non-fondamentale definisce una classe `ModuleConfig(BaseModel)` con tutti i propri parametri operativi. Questa configurazione:
- Ha valori default ragionevoli dichiarati nel codice
- Viene persistita su PostgreSQL alla prima esecuzione
- È modificabile a runtime tramite Command Center UI (pubblica su `config.update.requested`)
- È modificabile offline tramite file YAML in `config/[nome_modulo].yaml` (letto al boot)
- La modifica runtime ha effetto immediato: il modulo sottoscrive `config.updated` e ricarica i propri parametri senza restart

```python
# Esempio struttura — ogni modulo ha la propria versione
class ModuleConfig(BaseModel):
    # parametri specifici del modulo, es:
    max_retries: int = 3
    timeout_seconds: int = 30
    enabled_channels: list[str] = []
    # ... altri parametri specifici

class ModuleConfigUpdate(BaseModel):
    module_name: str
    config: dict          # partial update supportato
    updated_by: str       # "ui" | "yaml" | "system"
```

### 5.2 — Lifecycle dei moduli

```python
class ModuleState(str, Enum):
    RUNNING = "running"
    PAUSED  = "paused"   # eventi restano in coda, non vengono consumati
    STOPPED = "stopped"  # come PAUSED + rilascio risorse (connessioni, browser)

class LifecycleRequest(BaseModel):
    target: str                    # nome modulo o nome flusso di business
    target_type: Literal["module", "flow"]
    action: Literal["pause", "stop", "resume"]
    graceful: bool = True          # attendi completamento task in corso
```

**Moduli CORE_IMMUTABLE** (non accettano LifecycleRequest): `redis_bus`, `db_manager`, `vault`

### 5.3 — Lifecycle dei flussi di business

I tre flussi (freelance, sfw_content, nsfw_content) supportano lifecycle indipendente. Quando un flusso riceve `pause` o `stop`:
- L'Orchestratore smette di accettare nuovi task per quel flusso
- I task già in esecuzione vengono completati (graceful)
- Lo stato del flusso viene persistito su PostgreSQL
- Il Command Center mostra lo stato aggiornato in tempo reale

---

## [SEZIONE 6 — CATALOGO MODULI E CONTRATTI]

**Convenzione naming topic Redis:** `[dominio].[entità].[stato]`
Esempi: `ai.request.created`, `media.asset.generated`, `platform.content.published`
I topic non contengono mai riferimenti ai flussi di business.

---

### [L0-BUS] Redis Stream Manager — `CORE_IMMUTABLE`
**Livello:** 0 | **Tipo:** Infrastruttura | **Lifecycle:** non controllabile

**Responsabilità:** Libreria interna condivisa. Wrapper asincrono attorno a Redis Streams. Gestisce publish, subscribe, consumer groups, dead letter queue, retry con backoff esponenziale.

**Non ha topic propri** — è importata da tutti gli altri moduli.

```python
class EventEnvelope(BaseModel):
    event_id: str           # UUID v4
    event_type: str         # es. "ai.request.created"
    source_module: str      # es. "orchestrator" | "ai_model_router"
    timestamp: datetime
    correlation_id: str     # traccia l'intera catena causale di un task
    payload: dict           # validato dal modulo ricevente
    retry_count: int = 0
```

---

### [L0-DB] Database Manager — `CORE_IMMUTABLE`
**Livello:** 0 | **Tipo:** Infrastruttura | **Lifecycle:** non controllabile

**Responsabilità:** Pool di connessioni async a PostgreSQL (asyncpg). Migrations con Alembic. Metodi CRUD tipizzati. Operazioni pgvector per RAG (upsert embedding, similarity search). Persistenza configurazioni moduli e stati lifecycle.

**Topic in:** `db.write.requested` | `db.read.requested` | `db.vector.upsert` | `db.vector.query`
**Topic out:** `db.write.completed` | `db.read.completed` | `db.vector.results`

---

### [L0-VAULT] Vault Module — `CORE_IMMUTABLE`
**Livello:** 0 | **Tipo:** Infrastruttura | **Lifecycle:** non controllabile

**Responsabilità:** Unico punto di accesso a tutti i segreti. In development: `.env`. In production: Infisical. Espone segreti solo in memoria, mai su disco o nei log.

**Non usa il Bus** — importato direttamente dai Core Modules che ne hanno bisogno.

---

### [L0-STORAGE] Storage Module
**Livello:** 0 | **Tipo:** Infrastruttura | **Lifecycle:** controllabile

**Responsabilità:** Interfaccia async a Cloudflare R2. Upload, download, URL pre-firmati. Gestisce retention policy: ogni asset viene taggato con `expires_at` calcolato dalla configurazione del modulo. Un job periodico interno elimina gli asset scaduti non contrassegnati come `permanent`.

**Topic in:** `storage.upload.requested` | `storage.download.requested` | `storage.delete.requested`
**Topic out:** `storage.upload.completed` | `storage.download.completed`

```python
class StorageModuleConfig(BaseModel):
    default_retention_days: int = 30
    cleanup_interval_hours: int = 24

class StorageUploadRequest(BaseModel):
    asset_id: str
    bucket: str
    content_type: str
    data_base64: str
    permanent: bool = False        # se True, non soggetto ad autopulizia
    correlation_id: str

class StorageUploadCompleted(BaseModel):
    asset_id: str
    url: str
    expires_at: Optional[datetime]
    correlation_id: str
```

---

### [L1-MOCK] Mock Module ⭐
**Livello:** 1 | **Tipo:** Core Engine | **Lifecycle:** controllabile
**Priorità:** Prima implementazione dopo il Bus

**Responsabilità:** Abilita il testing di qualsiasi modulo in isolamento completo. Tre sottocomponenti:

- **Schema Registry:** catalogo di tutti gli schemi Pydantic del sistema, fonte di verità per il testing
- **Fixture Generator:** genera payload validi e realistici per ogni schema, inclusi edge case
- **Bus Injector:** pubblica fixture sul Redis Bus esattamente come farebbe il modulo reale

**Topic in:** `mock.inject.requested`
**Topic out:** pubblica sul `target_topic` specificato nella richiesta

```python
class MockInjectRequest(BaseModel):
    target_topic: str
    schema_name: str
    override_fields: dict = {}
    delay_ms: int = 0
    repeat: int = 1
    sequence: list[dict] = []
```

---

### [L1-AI-ROUTER] AI Model Router
**Livello:** 1 | **Tipo:** Core Engine | **Lifecycle:** controllabile

**Responsabilità:** Gateway unificato per **qualsiasi** chiamata a modelli AI — testo, immagini, audio, video. Non distingue per tipo di contenuto: riceve una richiesta, seleziona il provider/modello appropriato, restituisce il risultato grezzo. Per i modelli testuali usa OpenRouter.ai come aggregatore (unica API per centinaia di modelli). Per i modelli generativi media usa le API dirette (Novita.ai, Prodia). Applica retry, fallback tra provider, validazione Pydantic della risposta. Emette evento di costo per il FinOps Module ad ogni chiamata completata.

**Topic in:** `ai.request.created`
**Topic out:** `ai.response.completed` | `ai.response.failed`

```python
class AIModelRouterConfig(BaseModel):
    default_text_model: str = "anthropic/claude-sonnet-4-5"
    default_image_model: str = "stable-diffusion-xl"
    max_retries: int = 3
    timeout_seconds: int = 60
    fallback_enabled: bool = True

class AIRequest(BaseModel):
    modality: Literal["text", "image", "audio", "video"]
    model_preference: Literal["fast", "smart", "cheap"] = "smart"
    model_override: Optional[str] = None   # forza un modello specifico
    prompt: str
    negative_prompt: Optional[str] = None
    system_prompt: Optional[str] = None    # solo per testo
    output_schema: Optional[str] = None   # nome schema Pydantic per structured output
    parameters: dict = {}
    correlation_id: str

class AIResponse(BaseModel):
    modality: str
    content: Optional[str] = None          # per testo
    asset_base64: Optional[str] = None     # per immagini/audio/video
    parsed_output: Optional[dict] = None   # se output_schema era specificato
    model_used: str
    provider_used: str
    cost_usd: float
    correlation_id: str
```

---

### [L1-PLATFORM] Platform Connector
**Livello:** 1 | **Tipo:** Core Engine | **Lifecycle:** controllabile

**Responsabilità:** Unico modulo autorizzato a interagire con piattaforme esterne. Gestisce tre operazioni principali: **pubblicazione** di contenuti o proposte di lavoro, **estrazione** di dati e analytics, **interazione** (messaggi, risposte). Strategia di accesso per ogni piattaforma configurata: usa l'API ufficiale (dev API) se disponibile e configurata; cade su Playwright+stealth solo come fallback. Se rileva blocchi non superabili (KYC biometrico, verifica identità legale), emette evento di escalation e si ferma — non tenta bypass.

**Topic in:** `platform.publish.requested` | `platform.extract.requested` | `platform.interact.requested`
**Topic out:** `platform.publish.completed` | `platform.extract.completed` | `platform.interact.completed` | `platform.action.failed` | `platform.escalation.required`

```python
class PlatformConnectorConfig(BaseModel):
    max_concurrent_sessions: int = 5
    default_timeout_seconds: int = 30
    stealth_delay_ms_min: int = 500
    stealth_delay_ms_max: int = 2000
    proxy_enabled: bool = True

class PlatformRequest(BaseModel):
    platform: str                          # es. "upwork" | "youtube" | "fansly"
    operation: Literal["publish", "extract", "interact"]
    payload: dict                          # specifico per operazione e piattaforma
    prefer_api: bool = True               # tenta API ufficiale prima di Playwright
    correlation_id: str

class PlatformEscalation(BaseModel):
    platform: str
    operation: str
    reason: str
    requires_human: bool = True
    correlation_id: str
```

---

### [L1-COMPOSER] Media Composer
**Livello:** 1 | **Tipo:** Core Engine | **Lifecycle:** controllabile

**Responsabilità:** Post-produzione e montaggio. Riceve asset grezzi già generati dall'AI Model Router (immagini, clip audio, segmenti video) e li compone in un prodotto finale coerente: sincronizzazione audio/video, compositing di immagini, tagli, titoli, transizioni. Non chiama mai modelli AI direttamente. Salva il prodotto finale su Storage Module.

**Topic in:** `media.compose.requested`
**Topic out:** `media.compose.completed` | `media.compose.failed`

```python
class MediaComposerConfig(BaseModel):
    max_concurrent_jobs: int = 3
    default_output_format: str = "mp4"
    default_resolution: str = "1080p"

class ComposeRequest(BaseModel):
    assets: list[dict]                     # lista asset con url e tipo
    composition_spec: dict                 # istruzioni di montaggio
    output_format: str = "mp4"
    correlation_id: str

class ComposeCompleted(BaseModel):
    asset_id: str
    storage_url: str
    duration_seconds: float
    format: str
    cost_usd: float
    correlation_id: str
```

---

### [L1-EXECUTOR] Executor Module
**Livello:** 1 | **Tipo:** Core Engine | **Lifecycle:** controllabile

**Responsabilità:** Esegue task di sviluppo software in sandbox Docker effimere e isolate. Riceve specifiche dal task, coordina con AI Model Router per generazione codice, esegue il codice nella sandbox, cattura output ed errori, itera fino a un massimo di tentativi configurabile. Se supera il limite senza successo, emette evento di escalation verso il Notification Module. I deliverable completati vengono salvati su Storage Module con retention configurabile; la consegna sulla piattaforma avviene in parallelo tramite Platform Connector, indipendentemente dallo storage.

Gestisce la concorrenza tramite semaforo interno: il numero massimo di sandbox attive simultaneamente è configurabile. I task in eccesso restano in coda sul Bus fino a che uno slot si libera.

**Topic in:** `executor.task.requested`
**Topic out:** `executor.task.completed` | `executor.task.failed` | `executor.escalation.required`

```python
class ExecutorConfig(BaseModel):
    max_concurrent_jobs: int = 3
    max_retries_per_task: int = 5
    sandbox_timeout_minutes: int = 30
    deliverable_retention_days: int = 7
    notify_on_failure: bool = True

class ExecutorTaskRequest(BaseModel):
    task_id: str
    specifications: str                    # requisiti del lavoro
    context: dict = {}                     # contesto aggiuntivo (RAG, storico)
    delivery_platform: Optional[str]       # piattaforma su cui consegnare
    delivery_payload: Optional[dict]       # payload per Platform Connector
    correlation_id: str

class ExecutorEscalation(BaseModel):
    task_id: str
    attempts_made: int
    last_error: str
    requires_human: bool = True
    correlation_id: str
```

---

### [L1-NOTIFY] Notification Module
**Livello:** 1 | **Tipo:** Core Engine | **Lifecycle:** controllabile

**Responsabilità:** Unico punto di uscita per le notifiche verso l'operatore umano. Riceve eventi di notifica da qualsiasi modulo del sistema (Executor per fallimenti, Orchestratore per approvazioni richieste, SRE per alert, FinOps per soglie superate) e li instrada verso i canali configurati: Telegram Bot API e/o IFTTT Webhooks. Non usa Playwright — sono chiamate HTTP pure.

**Topic in:** `notification.send.requested`
**Topic out:** `notification.send.completed` | `notification.send.failed`

```python
class NotificationModuleConfig(BaseModel):
    telegram_enabled: bool = True
    telegram_bot_token: str = ""           # iniettato dal Vault
    telegram_chat_id: str = ""
    ifttt_enabled: bool = False
    ifttt_webhook_key: str = ""            # iniettato dal Vault
    notify_on_escalation: bool = True
    notify_on_flow_state_change: bool = True
    notify_on_finops_alert: bool = True

class NotificationRequest(BaseModel):
    message: str
    level: Literal["info", "warning", "critical"] = "info"
    source_module: str
    action_required: bool = False
    correlation_id: str
```

---

### [L1-INTELLIGENCE] Intelligence Module
**Livello:** 1 | **Tipo:** Core Engine | **Lifecycle:** controllabile

**Responsabilità:** Analisi dati trasversale. Monitora trend su piattaforme target tramite Platform Connector. Gestisce campagne di A/B testing. Calcola ROI per flusso incrociando costi operativi (da FinOps) con ricavi. Segnala canali in perdita oltre soglia configurabile.

**Topic in:** `intelligence.trend_scan.requested` | `intelligence.ab_test.evaluate`
**Topic out:** `intelligence.trend.discovered` | `intelligence.ab_test.result` | `intelligence.roi.computed`

```python
class IntelligenceConfig(BaseModel):
    scan_interval_minutes: int = 60
    roi_loss_threshold_pct: float = -20.0  # soglia perdita per alert
    ab_test_min_sample_size: int = 100

class TrendDiscovered(BaseModel):
    platform: str
    topic: str
    score: float
    raw_data: dict
    correlation_id: str
```

---

### [L1-ORCHESTRATOR] Agent Orchestrator
**Livello:** 1 | **Tipo:** Core Engine | **Lifecycle:** controllabile (solo nuovi task; task in esecuzione completati prima dello stop)

**Responsabilità:** Cervello del sistema. **Unico modulo** che conosce i tre flussi di business e le loro logiche operative. Traduce gli obiettivi di business in sequenze di eventi tecnici. Gestisce il lifecycle completo di ogni task. Implementa il pattern Saga per consistenza nelle operazioni distribuite. Gestisce il lifecycle dei flussi di business (pausa/stop/resume con graceful completion).

I tre flussi sono definiti come file di configurazione YAML in `orchestrator/flows/` — non come codice hardcoded. Aggiungere o modificare un flusso non richiede modifiche al codice del modulo.

**Topic in:** `orchestrator.task.requested` | `module.lifecycle.requested` | `config.update.requested`
**Topic out:** `orchestrator.task.completed` | `orchestrator.task.failed` | `orchestrator.task.compensating` | `config.updated` | (tutti i topic dei moduli Core come publisher)

```python
class OrchestratorConfig(BaseModel):
    max_concurrent_tasks_per_flow: int = 10
    saga_timeout_minutes: int = 60
    graceful_stop_timeout_minutes: int = 5

class OrchestratorTaskRequest(BaseModel):
    flow_name: str                         # "freelance" | "sfw_content" | "nsfw_content"
    flow_version: str = "latest"
    input_data: dict
    priority: Literal["low", "normal", "high"] = "normal"
    correlation_id: str

class OrchestratorTaskCompleted(BaseModel):
    flow_name: str
    output_data: dict
    steps_executed: list[str]
    total_cost_usd: float
    duration_ms: int
    correlation_id: str
```

---

### [L3-UI] Command Center
**Livello:** 3 | **Tipo:** Controllo | **Lifecycle:** controllabile

**Responsabilità:** Dashboard operativa interattiva costruita con Streamlit. Deve essere pienamente operativa — non solo un display passivo. Funzionalità richieste: visualizzazione stato di ogni modulo e flusso in tempo reale (con `streamlit-autorefresh`), modifica configurazione di ogni modulo con form interattivi, controllo lifecycle (pausa/stop/resume) tramite bottoni con conferma esplicita, approvazione manuale task ad alto rischio, monitoring log strutturati con filtri per modulo e livello. Legge da PostgreSQL e sottoscrive topic Redis in sola lettura. Scrive tramite Bus (pubblica su `module.lifecycle.requested` e `config.update.requested`).

---

### [L3-SRE] AI SRE Module
**Livello:** 3 | **Tipo:** Controllo | **Lifecycle:** controllabile

**Responsabilità:** Agente dormiente di manutenzione automatica. Quando riceve un alert, analizza i log strutturati coinvolti (timeout, fallimenti ripetuti, variazioni DOM, errori API), poi chiama l'AI Model Router per formulare diagnosi e proposta di patch. Il risultato viene distribuito su due canali in parallelo:

- **GitHub:** apre una Pull Request sul repository del modulo coinvolto (es. `invariant-labs/core-platform-connector`) con la patch proposta come diff, descrizione della diagnosi e passi di verifica
- **Telegram:** invia tramite Notification Module un messaggio strutturato e ben formattato con diagnosi, causa probabile, link diretto alla PR su GitHub

L'operatore revisiona la PR su GitHub, la approva o modifica, e l'Auto-Updater rileva il merge e aggiorna il sistema locale automaticamente. L'SRE non applica mai nulla in autonomia.

**Topic in:** `sre.alert.triggered`
**Topic out:** `ai.request.created` (verso AI Model Router) | `notification.send.requested` (verso Notification Module)
**Accesso diretto:** GitHub API (unica eccezione a D1 per questo modulo — giustificata dalla natura della funzione)

---

### [L3-FINOPS] FinOps Module
**Livello:** 3 | **Tipo:** Controllo | **Lifecycle:** controllabile

**Responsabilità:** Contabilità operativa al millesimo di centesimo. Aggrega eventi di costo da AI Model Router, Media Composer, Storage Module, Platform Connector. Calcola ROI per flusso. Genera report per ottimizzazione fiscale. Notifica tramite Notification Module quando un flusso supera soglie configurabili.

**Topic in:** `finops.cost.recorded` | `finops.revenue.recorded`
**Topic out:** `finops.report.generated` | `finops.alert.threshold_exceeded`

```python
class FinOpsConfig(BaseModel):
    cost_alert_threshold_usd: float = 10.0
    report_interval_hours: int = 24
    currency: str = "EUR"
    tax_regime: str = "forfettario"
```

---

### [L0-UPDATER] Auto-Updater Module
**Livello:** 0 (bootstrap) | **Tipo:** Infrastruttura autonoma | **Lifecycle:** indipendente dal sistema

**Eccezione D10 — Bootstrap:** questo modulo opera in isolamento totale. Non usa Redis Bus, non dipende da DB Manager né da Vault. È l'unico modulo che può funzionare quando il resto del sistema è down, e per questo motivo è l'unico autorizzato a gestire aggiornamenti e riavvii del sistema stesso.

**Responsabilità:** Monitora i repository GitHub di `invariant-labs` per nuovi commit o merge di Pull Request sui branch configurati (tipicamente `main`). Quando rileva un aggiornamento su un modulo, esegue localmente `git pull` sul repo corrispondente, ricostruisce il container Docker del modulo aggiornato e lo riavvia. Notifica l'operatore via Telegram (chiamata HTTP diretta, senza passare dal Notification Module) dell'avvenuto aggiornamento o di eventuali errori durante il processo. Gestisce un lock file per evitare aggiornamenti concorrenti.

**Nessun topic Redis** — opera esclusivamente tramite GitHub API (polling o webhook) e comandi Docker locali.

```python
class AutoUpdaterConfig:
    # Letto da file YAML locale — non da PostgreSQL
    github_org: str = "invariant-labs"
    github_token: str               # da variabile d'ambiente locale
    watched_repos: list[str]        # lista repo da monitorare
    watched_branch: str = "main"
    poll_interval_seconds: int = 60
    telegram_bot_token: str         # da variabile d'ambiente locale
    telegram_chat_id: str
    docker_compose_path: str        # path locale al docker-compose.yml
    auto_restart_on_update: bool = True
```

---

## [SEZIONE 7 — TEMPLATE PROMPT OPERATIVO]

Prima di implementare ogni modulo, genera il suo Prompt Operativo e salvalo in `docs/prompts/[NOME_MODULO].md`.

```markdown
# Prompt Operativo — [NOME_MODULO]

## Ruolo nel Sistema
[Ruolo funzionale, moduli upstream e downstream.]

## Lifecycle
[CORE_IMMUTABLE | controllabile — comportamento in PAUSED e STOPPED]

## Configurazione
[Schema ModuleConfig completo con tutti i parametri, default e descrizioni.]

## Dipendenze
- Moduli già implementati: [lista]
- Moduli simulati dal Mock Module: [lista con schema name]

## Schema Pydantic Completo
[Espansione degli schemi base della Sezione 6.
Tutti i campi, con tipo, default, validator, Field(description=...).]

## Contratto Redis Streams
- Stream sottoscritti: [nome stream, consumer group]
- Stream pubblicati: [nome stream, tipo messaggio]
- Dead Letter Queue: [nome DLQ]
- Politica retry: [max tentativi, backoff]

## Flusso Principale
[Step-by-step con gestione esplicita degli errori e compensazione.]

## Struttura Directory
[Albero completo con descrizione file.]

## Test Richiesti
- Unit test: [lista scenari]
- Integration test con Mock Module: [lista scenari]
- Edge case: [lista casi limite]

## ADR Collegati
[Lista ADR che impattano questo modulo.]

## Definition of Done
- [ ] Tutti i test passano
- [ ] Nessuna chiamata sincrona bloccante
- [ ] Nessun segreto nel codice
- [ ] Schema di configurazione implementato e persistito
- [ ] Lifecycle RUNNING/PAUSED/STOPPED implementato (se non CORE_IMMUTABLE)
- [ ] Schema registrato nel Mock Module Schema Registry
- [ ] ADR documentato per ogni decisione ambigua
- [ ] Nessun riferimento ai flussi di business (D7)
- [ ] Dockerfile aggiornato
```

---

## [SEZIONE 8 — STRUTTURA REPOSITORY]

### Meta-repo: `invariant-labs/venture-studio`
```
venture-studio/                       # meta-repo
├── NORTH_STAR.md
├── docker-compose.yml                # referenzia immagini da ogni sotto-repo
├── docker-compose.test.yml
├── bootstrap.sh                      # clona tutti i sotto-repo e avvia il sistema
├── .env.example
└── docs/
    └── decisions/                    # ADR_NNN_*.md trasversali al sistema
```

### Struttura di ogni sotto-repo (es. `invariant-labs/core-ai-model-router`)
```
core-ai-model-router/
├── NORTH_STAR.md -> symlink al meta-repo (solo lettura)
├── Dockerfile
├── pyproject.toml
├── config/
│   └── ai_model_router.yaml          # configurazione default del modulo
├── docs/
│   └── prompts/
│       └── AI_MODEL_ROUTER.md        # Prompt Operativo auto-generato
├── src/
│   └── ai_model_router/
│       ├── __init__.py
│       ├── router.py
│       ├── config.py
│       ├── schemas.py
│       └── providers/
└── tests/
    ├── unit/
    └── integration/
```

### Repo speciale: `invariant-labs/core-auto-updater`
```
core-auto-updater/
├── Dockerfile
├── pyproject.toml
├── updater.py                        # entry point autonomo
├── config.yaml                       # configurazione locale (non da PostgreSQL)
└── tests/
```

---

## [SEZIONE 9 — ORDINE DI IMPLEMENTAZIONE]

Ogni step presuppone che il precedente abbia superato tutti i test.
Ogni step inizia con la generazione del relativo Prompt Operativo, salvato nel sotto-repo del modulo in `docs/prompts/`.

```
Step  1:  invariant-labs/core-bus                — Redis Stream Manager (fondamenta)
Step  2:  invariant-labs/core-vault              — Vault Module
Step  3:  invariant-labs/core-mock               — Mock Module ⭐ (sblocca testing indipendente)
Step  4:  invariant-labs/core-db                 — DB Manager + schema SQL + pgvector
Step  5:  invariant-labs/core-storage            — Storage Module + retention policy
Step  6:  invariant-labs/core-notification       — Notification Module
Step  7:  invariant-labs/core-ai-model-router    — AI Model Router (OpenRouter + media API)
Step  8:  invariant-labs/core-platform-connector — Platform Connector
Step  9:  invariant-labs/core-media-composer     — Media Composer
Step 10:  invariant-labs/core-executor           — Executor Module
Step 11:  invariant-labs/core-intelligence       — Intelligence Module
Step 12:  invariant-labs/core-orchestrator       — Agent Orchestrator + flow YAML
Step 13:  invariant-labs/control-finops          — FinOps Module
Step 14:  invariant-labs/control-sre             — AI SRE Module
Step 15:  invariant-labs/control-ui              — Command Center
Step 16:  invariant-labs/core-auto-updater       — Auto-Updater Module (isolato)
Step 17:  invariant-labs/venture-studio          — meta-repo: docker-compose, bootstrap.sh
```

---

## [SEZIONE 10 — INIZIO SESSIONE]

Il tuo primo task è:

1. Crea l'organizzazione GitHub `invariant-labs` e tutti i repository elencati nella Sezione 3 (se non esistono già)
2. Clona localmente tutti i repository in una cartella comune
3. Inizia dallo Step 1: genera il Prompt Operativo per `core-bus`, salvalo in `core-bus/docs/prompts/CORE_BUS.md`, poi implementa il modulo
4. Procedi in sequenza seguendo l'ordine della Sezione 9

Ad ogni step completato, annuncia: `[STEP N COMPLETATO] — Procedo con: [nome repo successivo]` e continua autonomamente.

**Riorientamento sessione:** se stai riprendendo una sessione interrotta, controlla quali repo hanno già contenuto in `src/` e `tests/`, identifica lo step corrente, e riprendi da lì.
