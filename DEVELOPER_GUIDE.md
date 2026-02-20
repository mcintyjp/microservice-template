# usvc-lib

Python AI Agent Worker Library for building microservice job processors.

**Python 3.12+** · **Async-first** · **Pydantic v2**

---

## Features

- **Job polling** — polls an Oracle database queue for ready jobs, claims them atomically, processes concurrently
- **Action routing** — `@action` decorator maps job payloads to handler functions via an `"action"` field
- **Dependency injection** — type-hint-based injection of service dependencies into action handlers
- **REST API service template** — `RestAPIService` base class with built-in rate limiting, circuit breaking, and retries
- **Health monitoring** — three-tier health model (RED/YELLOW/GREEN) with aggregated `GET /health` endpoint
- **Prometheus metrics** — `GET /metrics` endpoint in Prometheus text exposition format
- **Structured logging** — structlog with JSON output and `token` field for job correlation
- **OpenTelemetry** — tracing and log export to any OTLP-compatible collector
- **Service registry** — optional MongoDB-based service registration with versioned schema publishing and heartbeat-based health broadcasting
- **Dev mode** — in-memory queue with `POST /dev/job` for local testing without Oracle

## Quick Start

### Install

```bash
uv add usvc-lib
# or
pip install usvc-lib
```

### Minimal Example

**1. Define an action** (`src/actions/greet/handler.py`):

```python
from pydantic import BaseModel
from usvc_lib import action

class GreetInput(BaseModel):
    name: str

class GreetOutput(BaseModel):
    message: str

@action("greet")
async def handle(input: GreetInput) -> GreetOutput:
    return GreetOutput(message=f"Hello, {input.name}!")
```

**2. Create the application** (`main.py`):

```python
from usvc_lib import Application

app = Application()
app.run()
```

**3. Configure and run**:

```bash
# .env
MICROSERVICE_NAME=greeting-service
DEV_MODE=True
```

```bash
uv run python main.py
```

**4. Submit a test job** (dev mode):

```bash
curl -X POST http://localhost:8000/dev/job \
  -H "Content-Type: application/json" \
  -d '{"action": "greet", "name": "World"}'
```

## Architecture Overview

```
                    ┌─────────────────────────────────────────┐
                    │              Application                │
                    │  (orchestrator: wires all components)   │
                    └────────────────┬────────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
     ┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐
     │   HTTP Server  │   │     Worker       │   │ ServiceContainer │
     │   (FastAPI +   │   │  (polling loop,  │   │   (DI, lifecycle │
     │    uvicorn)    │   │   concurrency)   │   │    management)   │
     └────────┬───────┘   └────────┬─────────┘   └────────┬─────────┘
              │                    │                       │
     ┌────────┴────────┐          │               ┌───────┴────────┐
     │ /health         │          ▼               │ ServiceProvider│
     │ /metrics        │   ┌─────────────┐        │ instances      │
     │ /dev/job        │   │    Queue     │        └────────────────┘
     └─────────────────┘   │ (Oracle or   │
                           │  InMemory)   │
                           └──────┬──────-┘
                                  │
                                  ▼
                           ┌─────────────┐
                           │   Action     │
                           │  Registry   │──▶ @action handlers
                           └─────────────┘
```

**Job lifecycle:** Ready → Assigned → Processing → Completed/Failed

## Actions

Actions are async handler functions decorated with `@action` that process jobs. The decorator inspects type hints to automatically wire input validation and service injection.

### Directory Structure

```
src/actions/
├── greet/
│   └── handler.py      # @action("greet")
├── summarize/
│   └── handler.py      # @action("summarize")
└── translate/
    └── handler.py      # @action("translate")
```

### Auto-Discovery

The `Application` automatically discovers actions by scanning the actions directory (default: `src/actions/`). Each subdirectory containing a `handler.py` is imported, and any function with an `@action` decorator is registered.

```python
# Custom actions directory
app = Application(actions_dir="path/to/my/actions")
```

### Handler Signature

The `@action` decorator inspects type hints to determine:

- **Input schema** — a parameter typed as a `BaseModel` subclass (validated with Pydantic)
- **Service dependencies** — parameters typed as `ServiceProvider` subclasses (resolved from the container)
- **Return type** — if a `BaseModel`, serialized via `model_dump(mode="json")`

```python
from pydantic import BaseModel
from usvc_lib import action

class SummarizeInput(BaseModel):
    text: str
    max_length: int = 200

@action("summarize")
async def handle(input: SummarizeInput, llm: LLMService) -> dict:
    summary = await llm.summarize(input.text, input.max_length)
    return {"summary": summary}
```

### Job Payload Format

Jobs are JSON objects with an `"action"` field that determines routing. The remaining fields are passed to the input schema:

```json
{
  "action": "summarize",
  "text": "Long article content...",
  "max_length": 150
}
```

## Services

Services are long-lived dependencies (API clients, database connections, etc.) injected into action handlers via type hints.

### ServiceProvider Base Class

```python
from usvc_lib import ServiceProvider

class LLMService(ServiceProvider):
    name = "llm"

    async def initialize(self) -> None:
        """Called once at startup — set up connections, auth, etc."""
        self.client = await create_llm_client()

    async def cleanup(self) -> None:
        """Called at shutdown — close connections, flush buffers."""
        await self.client.close()

    async def summarize(self, text: str, max_length: int) -> str:
        return await self.client.complete(prompt=f"Summarize: {text}")
```

### Registration

Register services before calling `app.run()`. **Registration order matters** — if service B depends on service A, register A first:

```python
app = Application()
app.register_service(DatabaseService)  # registered first
app.register_service(LLMService)       # can depend on DatabaseService
app.run()
```

The container supports **inter-service dependency injection**: if a `ServiceProvider.__init__` takes another `ServiceProvider` subclass as a parameter, it is automatically resolved from already-registered services.

### Health Integration

Every `ServiceProvider` receives a bound `HealthRegistry` via `bind_health_registry()`. Use `self.health_registry` to register and update health checks:

```python
class MyService(ServiceProvider):
    name = "my_service"

    async def initialize(self) -> None:
        self.health_registry.register("my_service")

    async def do_work(self) -> None:
        try:
            result = await self._call_external()
            self.health_registry.update("my_service", Status.GREEN)
        except Exception:
            self.health_registry.update("my_service", Status.RED, {"error": "connection failed"})
```

## REST API Service Template

`RestAPIService` is a `ServiceProvider` subclass that provides an httpx client with built-in rate limiting, circuit breaking, retries, and health reporting.

### Example

```python
from usvc_lib import RestAPIService, RestAPIConfig

class PaymentAPI(RestAPIService):
    name = "payment_api"
    config = RestAPIConfig(
        BASE_URL="https://payments.example.com",
        RATE_LIMIT_REQUESTS=50,
        RATE_LIMIT_WINDOW_SECONDS=60.0,
        CB_FAILURE_THRESHOLD=5,
        CB_RECOVERY_TIMEOUT=30.0,
        MAX_RETRIES=3,
    )

    async def charge(self, amount: float, currency: str) -> dict:
        response = await self.request(
            "POST",
            f"{self.config.BASE_URL}/charges",
            json={"amount": amount, "currency": currency},
        )
        response.raise_for_status()
        return response.json()
```

### RestAPIConfig Options

| Option | Type | Default | Description |
|---|---|---|---|
| `BASE_URL` | `str` | `http://localhost:8000` | Base URL for the API |
| `RATE_LIMIT_REQUESTS` | `int` | `100` | Max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `float` | `60.0` | Rate limit window duration |
| `CB_FAILURE_THRESHOLD` | `int` | `5` | Failures before circuit opens |
| `CB_RECOVERY_TIMEOUT` | `float` | `30.0` | Seconds before OPEN → HALF_OPEN |
| `CB_SUCCESS_THRESHOLD` | `int` | `2` | Successes in HALF_OPEN to close |
| `REQUEST_TIMEOUT_SECONDS` | `float` | `30.0` | Per-request timeout |
| `MAX_RETRIES` | `int` | `3` | Retry attempts for 5xx/timeout/connect errors |
| `RETRY_BACKOFF_BASE` | `float` | `1.0` | Exponential backoff base (seconds) |
| `CONNECTION_POOL_SIZE` | `int` | `10` | httpx connection pool size |

## Configuration Reference

All settings are loaded from environment variables (or a `.env` file) using pydantic-settings.

| Variable | Type | Default | Description |
|---|---|---|---|
| `MICROSERVICE_NAME` | `str` | **(required)** | Unique name for this microservice |
| `POLLING_INTERVAL_SECONDS` | `int` | `5` | Seconds between queue poll cycles |
| `MAX_CONCURRENT_JOBS` | `int` | `10` | Maximum concurrent job processing tasks |
| `SHUTDOWN_TIMEOUT_SECONDS` | `int` | `60` | Seconds to wait for in-flight jobs on shutdown |
| `JOB_TIMEOUT_SECONDS` | `int` | `300` | Maximum seconds per job before timeout |
| `ORACLE_DSN` | `str` | `XEPDB1` | Oracle Data Source Name |
| `ORACLE_USER` | `str` | `""` | Oracle username |
| `ORACLE_PASSWORD` | `str` | `""` | Oracle password |
| `ORACLE_TABLE` | `str` | `MICRO_SVC` | Oracle table name for job queue |
| `LOG_CONSOLE_JSON` | `bool` | `False` | Use JSON log output instead of console renderer |
| `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` | `str` | `""` | OTLP endpoint for log export |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | `str` | `""` | OTLP endpoint for trace export |
| `OTEL_EXPORTER_OTLP_USER` | `str` | `""` | OTLP basic auth username |
| `OTEL_EXPORTER_OTLP_PASSWORD` | `str` | `""` | OTLP basic auth password |
| `HTTP_HOST` | `str` | `0.0.0.0` | HTTP server bind address |
| `HTTP_PORT` | `int` | `8000` | HTTP server port |
| `MONGODB_URI` | `str` | `""` | MongoDB connection string (empty = no registry) |
| `MONGODB_DATABASE` | `str` | `microservices` | MongoDB database name |
| `MONGODB_HEARTBEAT_SECONDS` | `int` | `30` | Seconds between registry heartbeats |
| `MONGODB_KEY_TTL_SECONDS` | `int` | `90` | TTL (seconds) for registry documents |
| `MONGODB_MAX_POOL_SIZE` | `int` | `2` | MongoDB connection pool maximum |
| `MONGODB_MIN_POOL_SIZE` | `int` | `1` | MongoDB connection pool minimum |
| `SERVICE_VERSION` | `str` | `"0.0.0"` | Service version for schema key |
| `DEV_MODE` | `bool` | `False` | Enable dev mode (in-memory queue, `/dev/job` endpoint) |
| `DEBUG` | `bool` | `False` | Enable debug logging |

**Validation:** `ORACLE_USER` and `ORACLE_PASSWORD` are required when `DEV_MODE=False`. OTLP export is enabled independently for logs (`OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`) and traces (`OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`).

### Example `.env`

```env
MICROSERVICE_NAME=my-worker
ORACLE_DSN=XEPDB1
ORACLE_USER=app_user
ORACLE_PASSWORD=secret
POLLING_INTERVAL_SECONDS=5
MAX_CONCURRENT_JOBS=10
LOG_CONSOLE_JSON=True
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://otel-collector:4317
```

## API Endpoints

### `GET /health`

Returns aggregated health status. Returns HTTP 200 for GREEN/YELLOW, 503 for RED.

```json
{
  "status": "GREEN",
  "timestamp": "2025-01-15T10:30:00.000000+00:00",
  "checks": {
    "job_queue": {
      "status": "GREEN",
      "details": {"last_poll": "ok"}
    },
    "payment_api": {
      "status": "YELLOW",
      "details": {"last_status": 500, "attempt": 2}
    }
  }
}
```

### `GET /metrics`

Returns metrics in Prometheus text exposition format.

```
# HELP jobs_processed_total Total jobs completed
# TYPE jobs_processed_total counter
jobs_processed_total 42
# HELP jobs_errors_total Total jobs that resulted in errors
# TYPE jobs_errors_total counter
jobs_errors_total 3
# HELP active_jobs Number of jobs currently being processed
# TYPE active_jobs gauge
active_jobs 2
# HELP health_status Health status (0=RED, 1=YELLOW, 2=GREEN)
# TYPE health_status gauge
health_status 2
```

### `POST /dev/job` (dev mode only)

Submits a job and waits synchronously for the worker to process it. Returns the final result.

**Request:**
```json
{"action": "greet", "name": "World"}
```

**Response (200 — success):**
```json
{
  "job_id": "dev-1",
  "status": "Completed",
  "results": {"message": "Hello, World!"},
  "error": null,
  "runtime_ms": 12.5
}
```

**Response (422 — failure):**
```json
{
  "job_id": "dev-2",
  "status": "Failed",
  "results": null,
  "error": {"error_code": "UNKNOWN_ACTION", "error_message": "no action handler matched: invalid"},
  "runtime_ms": 1.2
}
```

## Resilience Patterns

### Circuit Breaker

Prevents cascading failures by stopping calls to unhealthy services.

**States:** CLOSED → OPEN → HALF_OPEN → CLOSED

| Parameter | Default | Description |
|---|---|---|
| `failure_threshold` | `5` | Consecutive failures before CLOSED → OPEN |
| `recovery_timeout` | `30.0` s | Time before OPEN → HALF_OPEN |
| `success_threshold` | `2` | Successes in HALF_OPEN before → CLOSED |

```python
from usvc_lib import CircuitBreaker, CircuitOpenError

cb = CircuitBreaker(failure_threshold=3, recovery_timeout=15.0)

if not cb.can_execute():
    raise CircuitOpenError("circuit open")

try:
    result = await call_external()
    cb.record_success()
except Exception:
    cb.record_failure()
    raise
```

### Rate Limiter

Token bucket algorithm for controlling request throughput.

| Parameter | Description |
|---|---|
| `max_tokens` | Maximum tokens in the bucket (= max burst size) |
| `refill_seconds` | Time to fully refill the bucket |

```python
from usvc_lib import RateLimiter

limiter = RateLimiter(max_tokens=100, refill_seconds=60.0)
await limiter.acquire()  # blocks until a token is available
```

## Health & Observability

### Three-Tier Health Model

| Status | Value | Meaning |
|---|---|---|
| `GREEN` | `2` | Healthy — all systems operational |
| `YELLOW` | `1` | Degraded — transient errors, retrying |
| `RED` | `0` | Broken — core functionality unavailable |

The overall status is the **minimum** across all registered health checks. Any single RED check makes the aggregate RED.

### Structured Logging

All log entries include a `token` field for job correlation. Use `logger` from the library:

```python
from usvc_lib import logger

logger.info("Processing item", token=job_id, item_id=42)
```

Output modes controlled by `LOG_CONSOLE_JSON`:
- `False` (default): human-readable console output
- `True`: JSON lines for log aggregation

### OpenTelemetry

Set `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` and/or `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` to enable:
- **Distributed tracing** — each job creates a span with the `token` attribute
- **Log export** — structlog events forwarded to the OTLP collector

## Service Registry

When `MONGODB_URI` is configured, each instance automatically registers itself in MongoDB with versioned schema publishing and periodic health heartbeats. This enables service discovery, capability advertisement, and health monitoring across a fleet of microservices.

The registry uses two collections: `service_schemas` (write-once, TTL-expiring schema records) and `service_instances` (active heartbeat tracking for live instances). Consumers query `service_instances` directly for service discovery.

```env
# .env — enable service registry
MONGODB_URI=mongodb://localhost:27017
SERVICE_VERSION=1.0.0
```

When MongoDB is enabled, a `mongodb_registry` health check is registered and reflected in `GET /health`, showing GREEN on successful publishes and RED after 3 consecutive failures.

## Development Mode

Enable with `DEV_MODE=True` to run locally without an Oracle database.

- Uses an **in-memory queue** instead of Oracle
- Mounts `POST /dev/job` for synchronous job submission and testing
- Oracle credentials are not required

```bash
# .env
MICROSERVICE_NAME=my-service
DEV_MODE=True
```

```bash
uv run python main.py
# Submit a job:
curl -X POST http://localhost:8000/dev/job \
  -H "Content-Type: application/json" \
  -d '{"action": "greet", "name": "World"}'
```

## Project Structure

```
src/usvc_lib/
├── __init__.py              # Public API exports
├── app.py                   # Application orchestrator
├── config.py                # WorkerSettings (pydantic-settings)
├── container.py             # ServiceContainer (DI + lifecycle)
├── logging.py               # Structured logging + OpenTelemetry setup
├── models.py                # Job, JobStatus data models
├── worker.py                # Worker engine (polling, processing, concurrency)
├── actions/
│   ├── decorator.py         # @action decorator + ActionDefinition
│   ├── discovery.py         # Auto-discovery from actions directory
│   └── registry.py          # ActionRegistry
├── api/
│   ├── dev.py               # POST /dev/job (dev mode)
│   ├── health.py            # GET /health
│   └── metrics.py           # GET /metrics + MetricsCollector
├── health/
│   ├── registry.py          # HealthRegistry
│   └── status.py            # Status enum (RED/YELLOW/GREEN)
├── patterns/
│   ├── circuit_breaker.py   # CircuitBreaker
│   └── rate_limiter.py      # RateLimiter (token bucket)
├── queue/
│   ├── interface.py         # QueueInterface (ABC)
│   ├── memory.py            # InMemoryQueue (dev mode)
│   └── oracle.py            # OracleQueue (production)
├── registry/
│   └── mongodb_publisher.py  # MongoDBRegistryPublisher (heartbeat + schema)
├── services/
│   └── base.py              # ServiceProvider base class
└── templates/
    └── rest_api.py           # RestAPIService + RestAPIConfig
```

## Testing

```bash
uv run pytest tests/ -v
```

Test stack: pytest, pytest-asyncio, pytest-cov

```bash
# With coverage
uv run pytest tests/ -v --cov=usvc_lib --cov-report=term-missing
```

## Tech Stack

| Component | Technology |
|---|---|
| Runtime | Python 3.12+ |
| HTTP framework | FastAPI + uvicorn |
| Validation | Pydantic v2 + pydantic-settings |
| Database | oracledb |
| HTTP client | httpx |
| Logging | structlog |
| Tracing | OpenTelemetry (API + SDK + OTLP exporter) |
| Service registry | MongoDB (motor, async) |
| Build | Hatchling |
