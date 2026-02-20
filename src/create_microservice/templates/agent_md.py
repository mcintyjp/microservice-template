CONTENT = r"""# AGENT.md: usvc-lib Microservice Framework Guide

**Target Audience:** AI agents building microservices with usvc-lib
**Last Updated:** 2026-02-19

---

## Table of Contents

1. [Introduction & Overview](#1-introduction--overview)
2. [Core Concepts](#2-core-concepts)
3. [Quick Start Template](#3-quick-start-template)
4. [Action Handlers (Detailed)](#4-action-handlers-detailed)
5. [Schemas & Validation](#5-schemas--validation)
6. [Service Dependency Injection](#6-service-dependency-injection)
7. [Service Development](#7-service-development)
8. [REST API Service Template](#8-rest-api-service-template)
9. [Logging & Observability](#9-logging--observability)
10. [Error Handling & Job Processing](#10-error-handling--job-processing)
11. [Health Checks](#11-health-checks)
12. [Registry & Discovery (MongoDB)](#12-registry--discovery-mongodb)
13. [Application Lifecycle](#13-application-lifecycle)
14. [Configuration Reference](#14-configuration-reference)
15. [Example Patterns & Troubleshooting](#15-example-patterns--troubleshooting)

---

## 1. Introduction & Overview

**usvc-lib** is an async-first, type-safe Python microservice framework for building job-processing services with built-in resilience patterns.

### Key Features

- **Job Polling & Routing:** Automatic job polling from Oracle/in-memory queue with action-based routing
- **Action Auto-Discovery:** Actions are automatically discovered from `src/actions/*/handler.py` — no manual registration
- **Dependency Injection:** Service-based DI system with lifecycle management
- **Health Checks:** Three-tier health system (RED/YELLOW/GREEN) with aggregation
- **Structured Logging:** Built-in correlation tokens and OpenTelemetry integration
- **Service Registry:** Optional MongoDB-based distributed discovery
- **REST API Template:** Resilient HTTP client with rate limiting, circuit breaking, and retries

### Target Audience

This guide is for AI agents who need to:
- Add new functionality (action handlers)
- Work with existing patterns (services, REST template)
- Properly use logging and error handling
- Understand infrastructure components (health checks, registry)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       Application                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Worker     │  │   Queue      │  │  Container   │      │
│  │  (polling)   │──│  (Oracle/    │  │  (services)  │      │
│  │              │  │   memory)    │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                                      │             │
│         ├──────────────────────────────────────┘             │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Actions    │  │    Health    │  │   Registry   │      │
│  │ (auto-disc.) │  │   Registry   │  │  (MongoDB)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

**Design Principles:**
- **Async-first:** All I/O operations are async (asyncio)
- **Type-safe:** Heavy use of type hints and Pydantic validation
- **Auto-discovery:** Actions found automatically, services registered explicitly
- **Fail-fast:** Configuration errors caught at startup

---

## 2. Core Concepts

### Job Model & Lifecycle

Jobs flow through states: **NEW** → **PROCESSING** → **COMPLETED/FAILED**

```python
class Job:
    insistance_id: str       # Unique correlation token (typo is intentional)
    action: str              # Action name to route to
    input_data: str          # JSON-encoded payload
    parent_token: str | None # Optional parent correlation
    status: str              # NEW, PROCESSING, COMPLETED, FAILED
```

**Lifecycle:**
1. Job inserted into queue with status=NEW
2. Worker polls and claims job → status=PROCESSING
3. Action handler executes
4. Result written → status=COMPLETED (or FAILED on error)

### Action Definitions & @action Decorator

Actions are async functions marked with `@action(name="...")`:

```python
from usvc_lib.actions import action

@action(name="echo")
async def handle_echo(message: str) -> dict:
    return {"echo": message}
```

**Key file:** `src/usvc_lib/actions/decorator.py`

The decorator inspects type hints to identify:
- **Input schema:** Parameter typed as `BaseModel` subclass
- **Service dependencies:** Parameters typed as `ServiceProvider` subclass
- **Output schema:** Return type annotation

### Service Providers & DI

Services are classes that inherit from `ServiceProvider` and provide reusable functionality:

```python
from usvc_lib.services import ServiceProvider

class DatabaseService(ServiceProvider):
    async def initialize(self) -> None:
        # Setup: create connection pool
        pass

    async def cleanup(self) -> None:
        # Teardown: close connections
        pass
```

**Key file:** `src/usvc_lib/services/base.py`

Services are:
- Registered in `main.py` with `app.register_service(MyService)`
- Initialized automatically during startup
- Injected into action handlers by type annotation
- Cleaned up during shutdown

### Health Registry (RED/YELLOW/GREEN)

A three-tier system for monitoring component health:

- **GREEN:** Component is healthy
- **YELLOW:** Degraded (temporary issues, retrying)
- **RED:** Critical failure

**Key file:** `src/usvc_lib/health/registry.py`

Services register health checks and update status during operations. The `/health` endpoint aggregates all checks using the minimum status.

### Structured Logging with Correlation Tokens

All logs include the `insistance_id` (correlation token) for tracing:

```python
import structlog

logger = structlog.get_logger()
logger.info("Processing payment", token=job.insistance_id, amount=100)
```

**Key file:** `src/usvc_lib/logging.py`

Supports both JSON (production) and pretty (development) console output, plus OpenTelemetry export.

### Worker Polling Loop

The worker continuously:
1. Polls queue for NEW jobs
2. Claims jobs (optimistic locking)
3. Routes to action handlers
4. Updates job status (COMPLETED/FAILED)
5. Enforces concurrency limits (semaphore)
6. Handles timeouts and errors

**Key file:** `src/usvc_lib/worker.py`

---

## 3. Quick Start Template

**Goal:** Create your first action in 5 steps.

### Step 1: Create Directory Structure

```
src/actions/my_action/
└── handler.py
```

**IMPORTANT:** The framework auto-discovers actions from `src/actions/*/handler.py` — no changes to `main.py` are needed.

### Step 2: Write Handler

**File:** `src/actions/my_action/handler.py`

```python
from usvc_lib.actions import action

@action(name="greet")
async def handle_greet(name: str, age: int) -> dict:
    """Simple greeting action."""
    return {
        "message": f"Hello {name}, you are {age} years old!",
        "timestamp": "2026-02-19T10:00:00Z"
    }
```

### Step 3: Configure Environment

**File:** `.env`

```bash
MICROSERVICE_NAME=greeting-service
DEV_MODE=true
```

### Step 4: Run Service

```bash
uv run python -m usvc_lib
```

### Step 5: Test with Dev Endpoint

```bash
curl -X POST http://localhost:8000/dev/job \
  -H "Content-Type: application/json" \
  -d '{
    "action": "greet",
    "name": "Alice",
    "age": 30
  }'
```

**Response:**
```json
{
  "insistance_id": "uuid-here",
  "status": "COMPLETED",
  "results": {
    "message": "Hello Alice, you are 30 years old!",
    "timestamp": "2026-02-19T10:00:00Z"
  }
}
```

**That's it!** No changes to `main.py`, no imports, no registration. The action was auto-discovered.

---

## 4. Action Handlers (Detailed)

### What is an Action Handler?

An action handler is an async function that:
1. Is decorated with `@action(name="...")`
2. Receives typed parameters (input schema + services)
3. Returns a result (dict or Pydantic model)
4. Is automatically discovered from `src/actions/*/handler.py`

### Decorator Syntax

```python
from usvc_lib.actions import action

@action(name="my_action")
async def handle_my_action(...) -> ...:
    pass
```

**Key file:** `src/usvc_lib/actions/decorator.py:20-72`

### Parameter Inspection

The decorator inspects function signatures to identify:

**1. Input Schema (Pydantic BaseModel):**

```python
from pydantic import BaseModel
from usvc_lib.actions import action

class PaymentInput(BaseModel):
    amount: float
    currency: str

@action(name="process_payment")
async def handle_payment(input: PaymentInput) -> dict:
    return {"status": "paid", "amount": input.amount}
```

**2. Service Dependencies (ServiceProvider subclass):**

```python
from usvc_lib.actions import action
from services.database import DatabaseService

@action(name="save_user")
async def handle_save_user(name: str, db: DatabaseService) -> dict:
    await db.save({"name": name})
    return {"saved": True}
```

**3. Output Schema (return type):**

```python
from pydantic import BaseModel

class PaymentOutput(BaseModel):
    transaction_id: str
    status: str

@action(name="payment")
async def handle_payment(...) -> PaymentOutput:
    return PaymentOutput(transaction_id="tx-123", status="completed")
```

### Handler Invocation Flow

**Key file:** `src/usvc_lib/worker.py:177-311`

**7-step pipeline:**

1. **Parse JSON:** Job's `input_data` string → Python dict
2. **Extract action:** Pop `"action"` field from payload
3. **Lookup handler:** Find registered action by name
4. **Validate input:** If input schema exists, validate with Pydantic
5. **Resolve services:** Inject requested service instances
6. **Execute handler:** Call async function with kwargs
7. **Serialize result:** Convert result to JSON-serializable dict

### Discovery Mechanism

**Key file:** `src/usvc_lib/actions/discovery.py`

The framework scans `src/actions/*/handler.py` for functions with `__action_definition__` attribute (set by decorator).

**Directory structure:**

```
src/actions/
├── payment/
│   └── handler.py  # @action(name="process_payment")
├── user/
│   └── handler.py  # @action(name="create_user")
└── notification/
    └── handler.py  # @action(name="send_email")
```

All three actions are auto-discovered at startup.

### Code Examples

**Example 1: Simple action (no schema):**

```python
from usvc_lib.actions import action

@action(name="ping")
async def handle_ping() -> dict:
    return {"pong": True}
```

**Example 2: Action with input schema:**

```python
from pydantic import BaseModel, Field
from usvc_lib.actions import action

class CreateUserInput(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: str
    age: int = Field(ge=0, le=120)

@action(name="create_user")
async def handle_create_user(input: CreateUserInput) -> dict:
    return {
        "user_id": "usr-123",
        "username": input.username,
        "email": input.email
    }
```

**Example 3: Action with service dependency:**

```python
from usvc_lib.actions import action
from services.payment_api import PaymentAPI

@action(name="charge_card")
async def handle_charge_card(amount: float, card_token: str, api: PaymentAPI) -> dict:
    response = await api.charge(amount, card_token)
    return {"success": response.status == "approved"}
```

---

## 5. Schemas & Validation

### Input Schemas (Pydantic BaseModel)

Input schemas provide automatic validation and type coercion.

**Example:**

```python
from pydantic import BaseModel, Field, field_validator

class PaymentInput(BaseModel):
    amount: float = Field(gt=0, description="Payment amount in dollars")
    currency: str = Field(pattern="^[A-Z]{3}$", description="ISO 4217 currency code")
    card_token: str = Field(min_length=10)

    @field_validator('amount')
    @classmethod
    def amount_must_be_reasonable(cls, v: float) -> float:
        if v > 10000:
            raise ValueError('amount exceeds maximum limit')
        return v
```

### Output Schemas (return type annotations)

Return types can be:
- `dict` (most common)
- Pydantic `BaseModel` (auto-serialized with `model_dump()`)
- `None` (converted to empty dict)

**Example with Pydantic output:**

```python
from pydantic import BaseModel

class TransactionResult(BaseModel):
    transaction_id: str
    status: str
    timestamp: str

@action(name="payment")
async def handle_payment(input: PaymentInput) -> TransactionResult:
    return TransactionResult(
        transaction_id="tx-abc123",
        status="completed",
        timestamp="2026-02-19T10:00:00Z"
    )
```

### Validation Behavior

**Key file:** `src/usvc_lib/worker.py:250-268`

**Validation errors are caught and formatted:**

```python
# Input payload: {"action": "create_user", "age": -5}
# Schema requires: age >= 0

# Error response:
{
    "error_code": "VALIDATION_ERROR",
    "error_message": "Field 'age' should be greater than or equal to 0",
    "timestamp": "2026-02-19T10:00:00Z"
}
```

**Formatting logic:** `src/usvc_lib/worker.py:363-403`

Multiple validation errors are combined:

```
"3 validation errors: Field 'email' is required; Field 'age' should be greater than or equal to 0; Field 'username' should have at least 3 characters"
```

### Optional Fields & Nested Schemas

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class CreateUserInput(BaseModel):
    username: str
    email: str
    age: int | None = None              # Optional field
    address: Address | None = None      # Optional nested schema
```

### Field Validators

```python
from pydantic import BaseModel, field_validator

class PaymentInput(BaseModel):
    amount: float

    @field_validator('amount')
    @classmethod
    def validate_amount_range(cls, v: float) -> float:
        if v < 1 or v > 10000:
            raise ValueError(f'amount must be between 1 and 10000, got {v}')
        return v
```

**When validation fails:**
- Job status → FAILED
- Error code: `VALIDATION_ERROR`
- Error message: Clean, user-friendly formatting (no Pydantic URLs)

---

## 6. Service Dependency Injection

### What are ServiceProviders?

Services encapsulate reusable functionality with lifecycle management.

**Key file:** `src/usvc_lib/services/base.py`

**Base class:**

```python
class ServiceProvider:
    name: str = ""  # Optional health check name

    async def initialize(self) -> None:
        """Override for async setup (connection pools, auth tokens, etc.)."""
        pass

    async def cleanup(self) -> None:
        """Override for graceful shutdown (close connections, flush buffers)."""
        pass
```

### Lifecycle Hooks

**1. `initialize()`:** Called once at startup

```python
class DatabaseService(ServiceProvider):
    async def initialize(self) -> None:
        self.pool = await create_connection_pool()
        self.health_registry.register("database")
```

**2. `cleanup()`:** Called during shutdown

```python
    async def cleanup(self) -> None:
        await self.pool.close()
```

### Health Registry Integration

Every service has access to `self.health_registry`:

```python
from usvc_lib.health.status import Status

class CacheService(ServiceProvider):
    async def get(self, key: str) -> str | None:
        try:
            value = await self.redis.get(key)
            self.health_registry.update("cache", Status.GREEN, {"last_op": "ok"})
            return value
        except RedisError:
            self.health_registry.update("cache", Status.RED, {"last_op": "error"})
            raise
```

### Constructor Injection (Inter-Service Dependencies)

Services can depend on other services via constructor:

```python
class PaymentAPI(ServiceProvider):
    def __init__(self, database: DatabaseService) -> None:
        super().__init__()
        self.database = database

    async def charge(self, amount: float) -> dict:
        # Use database service
        await self.database.save_transaction({"amount": amount})
        return {"status": "approved"}
```

**CRITICAL:** When using constructor injection, register dependencies first:

```python
# main.py
app.register_service(DatabaseService)   # Must be first
app.register_service(PaymentAPI)        # Can now depend on DatabaseService
```

### Usage in Action Handlers

Inject services by type annotation:

```python
from usvc_lib.actions import action
from services.database import DatabaseService
from services.cache import CacheService

@action(name="get_user")
async def handle_get_user(
    user_id: str,
    db: DatabaseService,
    cache: CacheService
) -> dict:
    # Try cache first
    cached = await cache.get(f"user:{user_id}")
    if cached:
        return {"user": cached, "source": "cache"}

    # Fallback to database
    user = await db.fetch_user(user_id)
    await cache.set(f"user:{user_id}", user)
    return {"user": user, "source": "database"}
```

### Dependency Ordering Importance

**Example:**

```python
# WRONG: PaymentAPI registered before DatabaseService
app.register_service(PaymentAPI)
app.register_service(DatabaseService)
# Error: PaymentAPI constructor requires DatabaseService, but it doesn't exist yet

# CORRECT: Dependencies registered first
app.register_service(DatabaseService)
app.register_service(PaymentAPI)
```

**Order matters because:**
- The container resolves services in registration order
- Constructor injection happens during resolution
- Circular dependencies are not supported

---

## 7. Service Development

### Creating Custom Services (4 Steps)

**Step 1: Create Service Class**

**File:** `src/services/payment_api.py`

```python
from usvc_lib.services import ServiceProvider
from usvc_lib.health.status import Status
import httpx

class PaymentAPI(ServiceProvider):
    name = "payment_api"  # Health check name

    def __init__(self) -> None:
        super().__init__()
        self.client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Create HTTP client and register health check."""
        self.client = httpx.AsyncClient(
            base_url="https://payments.example.com",
            timeout=30.0
        )
        self.health_registry.register(self.name)
        self.health_registry.update(self.name, Status.GREEN, {})

    async def cleanup(self) -> None:
        """Close HTTP client."""
        if self.client is not None:
            await self.client.aclose()

    async def charge(self, amount: float, card_token: str) -> dict:
        """Charge a credit card."""
        assert self.client is not None
        try:
            response = await self.client.post(
                "/charges",
                json={"amount": amount, "card_token": card_token}
            )
            response.raise_for_status()
            self.health_registry.update(
                self.name, Status.GREEN, {"last_charge": "ok"}
            )
            return response.json()
        except httpx.HTTPError as e:
            self.health_registry.update(
                self.name, Status.RED, {"last_charge": "error", "error": str(e)}
            )
            raise
```

**Step 2: Register in main.py**

**File:** `main.py`

```python
from usvc_lib import Application
from services.payment_api import PaymentAPI

app = Application()
app.register_service(PaymentAPI)  # Register service
app.run()
```

**Step 3: Use in Action Handler**

**File:** `src/actions/payment/handler.py`

```python
from usvc_lib.actions import action
from services.payment_api import PaymentAPI

@action(name="charge_card")
async def handle_charge_card(amount: float, card_token: str, api: PaymentAPI) -> dict:
    result = await api.charge(amount, card_token)
    return {"success": True, "charge_id": result["id"]}
```

**Step 4: Test**

```bash
curl -X POST http://localhost:8000/dev/job \
  -d '{"action": "charge_card", "amount": 50.00, "card_token": "tok_123"}'
```

### Inter-Service Dependencies (Constructor Injection)

**Example: PaymentAPI depends on DatabaseService**

```python
# src/services/database.py
class DatabaseService(ServiceProvider):
    async def initialize(self) -> None:
        self.pool = await create_pool()

    async def save_transaction(self, data: dict) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO txns (...) VALUES (...)", data)
```

```python
# src/services/payment_api.py
class PaymentAPI(ServiceProvider):
    def __init__(self, database: DatabaseService) -> None:
        super().__init__()
        self.database = database

    async def charge(self, amount: float, card_token: str) -> dict:
        # Make API call
        result = await self._call_api(amount, card_token)

        # Save to database
        await self.database.save_transaction({
            "amount": amount,
            "status": result["status"]
        })

        return result
```

### Registration with Application (main.py)

**CRITICAL:** `main.py` is the **ONLY** place to register services.

**Why?**
- Services require explicit registration to control initialization order
- Dependencies must be registered before dependents
- Actions are auto-discovered and don't need registration

**Example main.py:**

```python
from usvc_lib import Application
from services.database import DatabaseService
from services.cache import CacheService
from services.payment_api import PaymentAPI
from services.notification import NotificationService

app = Application()

# Order matters: dependencies first
app.register_service(DatabaseService)      # No dependencies
app.register_service(CacheService)         # No dependencies
app.register_service(PaymentAPI)           # Depends on DatabaseService
app.register_service(NotificationService)  # Depends on DatabaseService

app.run()
```

**When NOT to modify main.py:**
- Adding action handlers (auto-discovered)
- Changing action logic (only modify handler files)
- Adding imports for actions (not needed)

**When TO modify main.py:**
- Registering a new service
- Changing service registration order
- Removing a service

---

## 8. REST API Service Template

### Purpose

The `RestAPIService` base class provides a resilient HTTP client for external API calls.

**Key file:** `src/usvc_lib/templates/rest_api.py`

### Built-in Features

1. **Rate Limiting:** Token bucket algorithm
2. **Circuit Breaker:** Fail-fast when downstream is unhealthy
3. **Retries:** Exponential backoff for transient failures
4. **Health Integration:** Automatic status updates
5. **Connection Pooling:** Reusable httpx client

### RestAPIConfig Options

**All 10 settings:**

```python
from usvc_lib.templates import RestAPIConfig

config = RestAPIConfig(
    # Endpoint
    BASE_URL="https://api.example.com",

    # Rate limiting
    RATE_LIMIT_REQUESTS=100,              # Max requests
    RATE_LIMIT_WINDOW_SECONDS=60.0,       # Per window

    # Circuit breaker
    CB_FAILURE_THRESHOLD=5,               # Failures before open
    CB_RECOVERY_TIMEOUT=30.0,             # Seconds to wait before retry
    CB_SUCCESS_THRESHOLD=2,               # Successes to close circuit

    # Request settings
    REQUEST_TIMEOUT_SECONDS=30.0,         # Per-request timeout
    MAX_RETRIES=3,                        # Retry attempts
    RETRY_BACKOFF_BASE=1.0,               # Exponential backoff base
    CONNECTION_POOL_SIZE=10,              # Max connections
)
```

### Making Requests with Automatic Resilience

**Example service:**

```python
from usvc_lib.templates import RestAPIService, RestAPIConfig

class PaymentAPI(RestAPIService):
    config = RestAPIConfig(
        BASE_URL="https://payments.example.com",
        RATE_LIMIT_REQUESTS=50,
        CB_FAILURE_THRESHOLD=3,
    )

    async def charge(self, amount: float, card_token: str) -> dict:
        # Automatically applies: rate limiting, circuit breaker, retries
        response = await self.request(
            "POST",
            f"{self.config.BASE_URL}/charges",
            json={"amount": amount, "card_token": card_token}
        )
        response.raise_for_status()
        return response.json()
```

### Error Handling (2xx-4xx vs 5xx)

**Key file:** `src/usvc_lib/templates/rest_api.py:94-177`

**Behavior:**

- **2xx–4xx:** Considered "success" from circuit breaker perspective
  - Status: GREEN
  - Circuit breaker: record success
  - No retry

- **5xx:** Server error — triggers retry and circuit breaker
  - Status: YELLOW (retrying) → RED (all retries failed)
  - Circuit breaker: record failure
  - Retries with exponential backoff

**Example:**

```python
# 404 Not Found — returns immediately (no retry)
response = await api.request("GET", "/users/999")
# response.status_code == 404

# 503 Service Unavailable — retries 3 times
response = await api.request("GET", "/health")
# After 3 failures, raises exception and opens circuit
```

### Multiple REST API Services Pattern

**Example: Two different APIs**

```python
# src/services/payment_api.py
class PaymentAPI(RestAPIService):
    config = RestAPIConfig(
        BASE_URL="https://payments.example.com",
        RATE_LIMIT_REQUESTS=50,
    )
    name = "payment_api"

# src/services/inventory_api.py
class InventoryAPI(RestAPIService):
    config = RestAPIConfig(
        BASE_URL="https://inventory.example.com",
        RATE_LIMIT_REQUESTS=200,
    )
    name = "inventory_api"
```

**Register both:**

```python
# main.py
app.register_service(PaymentAPI)
app.register_service(InventoryAPI)
```

**Use both in action:**

```python
@action(name="purchase")
async def handle_purchase(
    item_id: str,
    amount: float,
    payment: PaymentAPI,
    inventory: InventoryAPI
) -> dict:
    # Check inventory
    stock = await inventory.request("GET", f"/items/{item_id}")

    # Charge payment
    charge = await payment.charge(amount, "tok_123")

    # Reserve item
    await inventory.request("POST", f"/items/{item_id}/reserve")

    return {"success": True}
```

### Complete Example: PaymentAPI Service

**File:** `src/services/payment_api.py`

```python
from usvc_lib.templates import RestAPIService, RestAPIConfig
from pydantic import BaseModel

class PaymentAPI(RestAPIService):
    config = RestAPIConfig(
        BASE_URL="https://payments.example.com",
        RATE_LIMIT_REQUESTS=50,
        RATE_LIMIT_WINDOW_SECONDS=60.0,
        CB_FAILURE_THRESHOLD=3,
        REQUEST_TIMEOUT_SECONDS=15.0,
    )
    name = "payment_api"

    async def charge(self, amount: float, card_token: str) -> dict:
        """Charge a credit card."""
        response = await self.request(
            "POST",
            f"{self.config.BASE_URL}/v1/charges",
            json={
                "amount": int(amount * 100),  # Cents
                "currency": "usd",
                "source": card_token
            }
        )
        response.raise_for_status()
        return response.json()

    async def refund(self, charge_id: str) -> dict:
        """Refund a charge."""
        response = await self.request(
            "POST",
            f"{self.config.BASE_URL}/v1/refunds",
            json={"charge": charge_id}
        )
        response.raise_for_status()
        return response.json()
```

**Test file:** `tests/test_rest_api_template.py` shows more examples.

---

## 9. Logging & Observability

### Structured Logging with structlog

**Key file:** `src/usvc_lib/logging.py`

All logging uses `structlog` for structured output.

```python
import structlog

logger = structlog.get_logger()
logger.info("User created", user_id="usr-123", email="alice@example.com")
```

### Correlation Tokens (insistance_id)

Every job has a unique `insistance_id` (correlation token) for tracing.

**Usage in actions:**

```python
from usvc_lib.actions import action
import structlog

logger = structlog.get_logger()

@action(name="process_order")
async def handle_order(order_id: str) -> dict:
    # Get token from context (automatically bound by worker)
    logger.info("Processing order", order_id=order_id)

    # All logs for this job will include the same token
    await process_payment()
    logger.info("Payment completed", order_id=order_id)

    return {"status": "completed"}
```

**Worker automatically binds token:** `src/usvc_lib/worker.py:182-198`

```python
# Worker adds token to log context
logger.info("Processing started", token=job.insistance_id, input_data=job.input_data)
```

**Parent tokens:** If a job spawns child jobs, use `parent_token` to link them:

```python
logger.info("Child job started", token=child_id, parent_token=parent_id)
```

### Logging in Actions

**Example:**

```python
import structlog
from usvc_lib.actions import action

logger = structlog.get_logger()

@action(name="send_email")
async def handle_send_email(to: str, subject: str, body: str) -> dict:
    logger.info("Sending email", to=to, subject=subject)

    try:
        await email_client.send(to, subject, body)
        logger.info("Email sent successfully", to=to)
        return {"sent": True}
    except Exception as e:
        logger.error("Email send failed", to=to, error=str(e))
        raise
```

### Log Levels

```python
logger.debug("Detailed diagnostic info", ...)
logger.info("Normal operation", ...)
logger.warning("Unexpected but handled", ...)
logger.error("Error that impacts operation", ...)
logger.exception("Error with full traceback", ...)  # Use in except blocks
```

### Console Output Modes

**JSON mode (production):**

```bash
LOG_CONSOLE_JSON=true
```

Output:
```json
{"event": "Processing started", "token": "abc-123", "timestamp": "2026-02-19T10:00:00Z"}
```

**Pretty mode (development):**

```bash
LOG_CONSOLE_JSON=false  # Default
```

Output:
```
2026-02-19 10:00:00 [info     ] Processing started    token=abc-123
```

### OpenTelemetry Integration (Logs and Traces)

**Configuration:**

```bash
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://otel.example.com/v1/logs
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://otel.example.com/v1/traces
OTEL_EXPORTER_OTLP_USER=my-user
OTEL_EXPORTER_OTLP_PASSWORD=my-password
```

**Logs are automatically exported** when endpoints are configured.

**Span creation for tracing:**

```python
from usvc_lib.logging import create_span

with create_span("process_payment", token=job.insistance_id, amount=100):
    # All code in this block is traced
    await charge_card()
    await update_database()
```

**Worker creates spans automatically:** `src/usvc_lib/worker.py:182`

```python
with create_span("process_job", token=token):
    # Entire job processing is traced
    ...
```

### Best Practices

1. **Always include context:** Log with relevant fields (user_id, order_id, etc.)
2. **Use appropriate levels:** `info` for normal flow, `error` for exceptions
3. **Don't log sensitive data:** Mask passwords, tokens, PII
4. **Use exception() in except blocks:** Automatically includes traceback
5. **Correlation tokens are automatic:** Worker binds them, just use logger

**Example:**

```python
import structlog
from usvc_lib.actions import action

logger = structlog.get_logger()

@action(name="process_payment")
async def handle_payment(amount: float, card_token: str) -> dict:
    # Don't log full card token
    masked_token = card_token[:4] + "****"
    logger.info("Payment started", amount=amount, card_token=masked_token)

    try:
        result = await charge_api.charge(amount, card_token)
        logger.info("Payment completed", amount=amount, charge_id=result["id"])
        return {"success": True}
    except Exception:
        logger.exception("Payment failed", amount=amount)  # Auto-includes traceback
        raise
```

---

## 10. Error Handling & Job Processing

### How to Throw Errors

**Just raise standard Python exceptions:**

```python
@action(name="divide")
async def handle_divide(a: float, b: float) -> dict:
    if b == 0:
        raise ValueError("Division by zero")
    return {"result": a / b}
```

### Error Flow (6 Steps)

**Key file:** `src/usvc_lib/worker.py:301-310`

1. **Exception raised** in action handler
2. **Caught by worker** in try/except
3. **Error payload created** with code and message
4. **Job marked as FAILED** in queue
5. **Error logged** with context (token, runtime, error details)
6. **Metrics updated** (`jobs_errors_total` incremented)

**Error payload format:**

```python
{
    "error_code": "ValueError",
    "error_message": "Division by zero",
    "timestamp": "2026-02-19T10:00:00Z"
}
```

**Code:** `src/usvc_lib/worker.py:352-360`

### Validation Errors

Pydantic validation errors are caught separately and formatted cleanly.

**Example:**

```python
# Input: {"action": "create_user", "age": -5}
# Schema: age must be >= 0

# Job fails with:
{
    "error_code": "VALIDATION_ERROR",
    "error_message": "Field 'age' should be greater than or equal to 0",
    "timestamp": "..."
}
```

**Code:** `src/usvc_lib/worker.py:250-268`

### Timeout Handling

Jobs that exceed `JOB_TIMEOUT_SECONDS` are automatically failed.

**Configuration:**

```bash
JOB_TIMEOUT_SECONDS=300  # 5 minutes
```

**Behavior:**

```python
# Job running for 6 minutes
# Worker kills the task and fails the job:
{
    "error_code": "TIMEOUT",
    "error_message": "Job exceeded max processing time (300s)",
    "timestamp": "..."
}
```

**Code:** `src/usvc_lib/worker.py:158-168`

### Circuit Breaker Errors

If a REST API service has an open circuit, requests fail immediately:

```python
from usvc_lib.patterns.circuit_breaker import CircuitOpenError

@action(name="call_api")
async def handle_call_api(api: PaymentAPI) -> dict:
    try:
        response = await api.request("GET", "/status")
        return {"status": response.status_code}
    except CircuitOpenError:
        # Circuit is open due to too many failures
        raise RuntimeError("Payment API is unavailable")
```

**When does circuit open?**
- After `CB_FAILURE_THRESHOLD` consecutive failures (default: 5)
- Stays open for `CB_RECOVERY_TIMEOUT` seconds (default: 30)
- Closes after `CB_SUCCESS_THRESHOLD` successes (default: 2)

### Best Practices

1. **Raise specific exceptions:** Use `ValueError`, `RuntimeError`, etc. (not generic `Exception`)
2. **Include context in error message:** `raise ValueError(f"Invalid user_id: {user_id}")`
3. **Log before raising:** Provide additional context for debugging
4. **Don't catch and suppress:** Let worker handle failures
5. **Idempotency matters:** Ensure retried jobs don't cause duplicates

**Example:**

```python
import structlog
from usvc_lib.actions import action

logger = structlog.get_logger()

@action(name="process_refund")
async def handle_refund(order_id: str, amount: float, db: DatabaseService) -> dict:
    # Validate
    order = await db.get_order(order_id)
    if order is None:
        logger.warning("Refund attempted for non-existent order", order_id=order_id)
        raise ValueError(f"Order not found: {order_id}")

    if order["status"] == "refunded":
        # Idempotent: already refunded
        logger.info("Order already refunded", order_id=order_id)
        return {"refunded": True, "amount": order["refund_amount"]}

    # Process refund
    try:
        await payment_api.refund(order["charge_id"])
        await db.update_order(order_id, {"status": "refunded", "refund_amount": amount})
        logger.info("Refund completed", order_id=order_id, amount=amount)
        return {"refunded": True, "amount": amount}
    except Exception as e:
        logger.exception("Refund failed", order_id=order_id, amount=amount)
        raise RuntimeError(f"Refund processing failed: {e}")
```

---

## 11. Health Checks

### Three-Tier Status System

**Key file:** `src/usvc_lib/health/status.py`

```python
from enum import IntEnum

class Status(IntEnum):
    RED = 0      # Critical failure
    YELLOW = 1   # Degraded (temporary issues, retrying)
    GREEN = 2    # Healthy
```

**Why IntEnum?**
- Enables comparison: `min([Status.GREEN, Status.RED])` → `Status.RED`
- Aggregation uses minimum status across all checks

### Health Registry API

**Key file:** `src/usvc_lib/health/registry.py`

**Register a check:**

```python
self.health_registry.register("my_component", initial_status=Status.GREEN)
```

**Update status:**

```python
from usvc_lib.health.status import Status

self.health_registry.update(
    "my_component",
    Status.YELLOW,
    {"last_attempt": "error", "retry_count": 2}
)
```

**Aggregate all checks:**

```python
overall = self.health_registry.aggregate()  # Returns minimum status
```

**Snapshot (for HTTP endpoint):**

```python
snapshot = self.health_registry.snapshot()
# Returns:
{
    "status": "GREEN",
    "timestamp": "2026-02-19T10:00:00Z",
    "checks": {
        "job_queue": {"status": "GREEN", "details": {"last_poll": "ok"}},
        "payment_api": {"status": "GREEN", "details": {"last_status": 200}}
    }
}
```

### Embedding in Services

**Example:**

```python
from usvc_lib.services import ServiceProvider
from usvc_lib.health.status import Status
import httpx

class PaymentAPI(ServiceProvider):
    name = "payment_api"

    async def initialize(self) -> None:
        self.client = httpx.AsyncClient()
        self.health_registry.register(self.name)  # Register check

    async def charge(self, amount: float, card_token: str) -> dict:
        try:
            response = await self.client.post("/charges", json={...})
            response.raise_for_status()

            # Update to GREEN on success
            self.health_registry.update(
                self.name,
                Status.GREEN,
                {"last_charge": "ok", "status_code": response.status_code}
            )
            return response.json()

        except httpx.HTTPError as e:
            # Update to RED on error
            self.health_registry.update(
                self.name,
                Status.RED,
                {"last_charge": "error", "error": str(e)}
            )
            raise
```

### GET /health Endpoint

**Key file:** `src/usvc_lib/api/health.py`

**Request:**

```bash
curl http://localhost:8000/health
```

**Response (healthy):**

```json
{
  "status": "GREEN",
  "timestamp": "2026-02-19T10:00:00.123Z",
  "checks": {
    "job_queue": {
      "status": "GREEN",
      "details": {"last_poll": "ok"}
    },
    "payment_api": {
      "status": "GREEN",
      "details": {"last_status": 200}
    }
  }
}
```

**Response (degraded):**

```json
{
  "status": "RED",
  "timestamp": "2026-02-19T10:00:00.123Z",
  "checks": {
    "job_queue": {
      "status": "GREEN",
      "details": {"last_poll": "ok"}
    },
    "payment_api": {
      "status": "RED",
      "details": {"error": "timeout", "attempt": 3}
    }
  }
}
```

### Built-in Checks

Two checks are registered automatically:

**1. job_queue:** Updated by worker during polling

```python
# src/usvc_lib/worker.py:109-111
self._health_registry.update(
    "job_queue", Status.GREEN, {"last_poll": "ok"}
)
```

**2. mongodb_registry:** Updated by registry publisher (if enabled)

### Aggregation Logic

**Key file:** `src/usvc_lib/health/registry.py:34-37`

```python
def aggregate(self) -> Status:
    if not self._checks:
        return Status.GREEN
    return min(check["status"] for check in self._checks.values())
```

**Example:**

- job_queue: GREEN
- payment_api: YELLOW
- database: GREEN

**Aggregate:** YELLOW (minimum across all checks)

---

## 12. Registry & Discovery (MongoDB)

### Purpose

The MongoDB registry provides distributed service discovery:
- Services publish their schemas and instance metadata
- External systems query the registry to discover available services
- Automatic heartbeat and TTL management

**Key file:** `src/usvc_lib/registry/mongodb_publisher.py`

### Two-Collection Design

**1. `service_schemas` collection:**
- Stores action schemas (input/output types)
- Write-once per service version
- TTL refresh via periodic heartbeat
- Key: `{service_name}:{service_version}`

**2. `service_instances` collection:**
- Stores instance metadata (host, port, health)
- Updated every heartbeat interval
- TTL-based expiration for dead instances
- Key: `instance_id`

### Schema Publication (Write-Once with TTL Refresh)

**Document structure:**

```json
{
  "service_name": "payment-service",
  "service_version": "1.2.3",
  "actions": [
    {
      "name": "process_payment",
      "input_schema": {
        "type": "object",
        "properties": {
          "amount": {"type": "number"},
          "currency": {"type": "string"}
        },
        "required": ["amount", "currency"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "transaction_id": {"type": "string"},
          "status": {"type": "string"}
        }
      }
    }
  ],
  "published_at": "2026-02-19T10:00:00Z",
  "expires_at": "2026-02-19T10:01:30Z"
}
```

**Behavior:**
- Published once at startup
- TTL refreshed every heartbeat (prevents expiration)
- Indexed on: `{service_name, service_version, published_at}`

### Instance Heartbeat (Periodic Updates)

**Document structure:**

```json
{
  "instance_id": "uuid-abc-123",
  "service_name": "payment-service",
  "service_version": "1.2.3",
  "host": "10.0.1.42",
  "port": 8000,
  "health_status": "GREEN",
  "health_checks": {
    "job_queue": {"status": "GREEN", "details": {"last_poll": "ok"}},
    "payment_api": {"status": "GREEN", "details": {"last_status": 200}}
  },
  "last_heartbeat": "2026-02-19T10:00:30Z",
  "expires_at": "2026-02-19T10:02:00Z"
}
```

**Behavior:**
- Updated every `MONGODB_HEARTBEAT_SECONDS` (default: 30s)
- TTL: `MONGODB_KEY_TTL_SECONDS` (default: 90s)
- Dead instances expire automatically after missing ~3 heartbeats

### Configuration Settings

```bash
# MongoDB connection
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=microservices

# Heartbeat and TTL
MONGODB_HEARTBEAT_SECONDS=30   # How often to update instance
MONGODB_KEY_TTL_SECONDS=90     # When instances expire (3x heartbeat)

# Connection pool
MONGODB_MAX_POOL_SIZE=2
MONGODB_MIN_POOL_SIZE=1
```

### Enabling Registry

**Required:** Set `MONGODB_URI` in `.env`

```bash
MONGODB_URI=mongodb://localhost:27017
```

**Startup behavior:**

If MongoDB is configured:
1. Application connects to MongoDB
2. Creates indexes on both collections
3. Publishes service schema
4. Starts heartbeat task

If connection fails:
- Logs warning
- **Continues without registry** (graceful degradation)

**Code:** `src/usvc_lib/app.py:140-156`

### Querying from External Systems

**Example: Find all instances of payment-service**

```javascript
// MongoDB query
db.service_instances.find({
  service_name: "payment-service",
  health_status: "GREEN"
})
```

**Example: Get schema for a service version**

```javascript
db.service_schemas.findOne({
  service_name: "payment-service",
  service_version: "1.2.3"
})
```

### Graceful Degradation on Failures

**Behavior:**
- Registry publisher runs in background task
- Failures are logged but don't crash the application
- Health check for `mongodb_registry` turns RED on errors
- Application continues processing jobs normally

**Code:** `src/usvc_lib/app.py:216-224`

```python
async def _run_publisher(self) -> None:
    """Run the registry publisher, shielding the TaskGroup from crashes."""
    try:
        await self._registry_publisher.start()
    except Exception:
        logger.warning(
            "MongoDB registry publisher crashed — continuing without registry"
        )
```

---

## 13. Application Lifecycle

### Startup Sequence (10 Steps)

**Key file:** `src/usvc_lib/app.py:71-179`

**1. Load settings:**
```python
settings = WorkerSettings()  # From .env + env vars
```

**2. Configure logging:**
```python
configure_logging(settings)
```

**3. Discover actions:**
```python
discover_actions(actions_dir, action_registry)
# Scans src/actions/*/handler.py
```

**4. Create queue:**
```python
if settings.DEV_MODE:
    queue = InMemoryQueue(settings)
else:
    queue = OracleQueue(settings)
```

**5. Connect queue:**
```python
await queue.connect()
```

**6. Initialize health registry:**
```python
health_registry = HealthRegistry()
health_registry.register("job_queue")
```

**7. Register and initialize services:**
```python
container = ServiceContainer(health_registry)
for svc_class in service_classes:
    container.register(svc_class)
await container.initialize_all()
```

**8. Create metrics collector:**
```python
metrics = MetricsCollector()
```

**9. Create worker:**
```python
worker = Worker(queue, action_registry, container, settings, health_registry, metrics)
```

**10. Start MongoDB publisher (optional):**
```python
if settings.MONGODB_URI:
    publisher = MongoDBRegistryPublisher(...)
    await publisher.connect()
```

### Entry Point Code Example

**File:** `main.py`

```python
from usvc_lib import Application
from services.database import DatabaseService
from services.payment_api import PaymentAPI

app = Application()
app.register_service(DatabaseService)
app.register_service(PaymentAPI)
app.run()  # Blocks until shutdown
```

**What happens:**
1. `Application()` constructor initializes empty service list
2. `register_service()` adds services to registration list
3. `run()` triggers:
   - `asyncio.run(_run_async())`
   - `_startup()` (10 steps above)
   - `_serve()` (worker + HTTP server + registry)
   - `_shutdown()` (cleanup)

### Shutdown Sequence (Graceful Cleanup)

**Key file:** `src/usvc_lib/app.py:242-252`

**1. Worker shutdown:**
```python
await worker.shutdown()
# Waits for in-flight jobs (up to SHUTDOWN_TIMEOUT_SECONDS)
# Cancels remaining tasks
```

**2. Registry publisher disconnect:**
```python
await registry_publisher.disconnect()
# Stops heartbeat task
# Closes MongoDB connection
```

**3. Service cleanup:**
```python
await container.cleanup_all()
# Calls cleanup() on all services in reverse registration order
```

**4. Queue disconnect:**
```python
await queue.disconnect()
# Closes database connection pool
```

**Logs:**
```
[info] Application shut down
```

### Fail-Fast Principle

The framework fails immediately on critical errors:

**Example 1: Missing MICROSERVICE_NAME**
```
ValidationError: MICROSERVICE_NAME is required
```

**Example 2: No actions discovered**
```
RuntimeError: No actions discovered in src/actions. Ensure the directory exists and contains valid action modules.
```

**Example 3: Oracle credentials missing (non-dev mode)**
```
ValueError: ORACLE_USER and ORACLE_PASSWORD are required when DEV_MODE is not enabled
```

**Why fail-fast?**
- Catches configuration errors at startup (not during runtime)
- Prevents partial initialization
- Clear error messages for debugging

### Service Initialization Order

Services are initialized in registration order:

```python
app.register_service(DatabaseService)   # Initialized first
app.register_service(CacheService)      # Initialized second
app.register_service(PaymentAPI)        # Initialized third (can use Database + Cache)
```

**During startup:**
```python
# src/usvc_lib/container.py
for svc_class in service_classes:
    instance = svc_class()  # Constructor injection happens here
    await instance.initialize()
```

**During shutdown (reverse order):**
```python
for instance in reversed(service_instances):
    await instance.cleanup()
```

---

## 14. Configuration Reference

### Settings Class (WorkerSettings)

**Key file:** `src/usvc_lib/config.py`

All configuration uses `pydantic-settings` with automatic loading from:
1. Environment variables (highest priority)
2. `.env` file
3. Default values

### Loading Order

```python
# Example: POLLING_INTERVAL_SECONDS resolution
# 1. Check env var: POLLING_INTERVAL_SECONDS=10
# 2. Check .env file: POLLING_INTERVAL_SECONDS=5
# 3. Use default: 5
```

### All Settings Organized by Category

#### **Identity**

```bash
MICROSERVICE_NAME=payment-service  # REQUIRED — no default, fails if missing
SERVICE_VERSION=1.2.3              # Default: "0.0.0" (used for registry key)
```

#### **Polling**

```bash
POLLING_INTERVAL_SECONDS=5         # How often to poll for jobs
MAX_CONCURRENT_JOBS=10             # Max parallel job processing
```

#### **Shutdown**

```bash
SHUTDOWN_TIMEOUT_SECONDS=60        # How long to wait for in-flight jobs before cancelling
```

#### **Job Processing**

```bash
JOB_TIMEOUT_SECONDS=300            # Max time per job (5 minutes)
```

#### **Oracle Database**

```bash
ORACLE_DSN=XEPDB1                  # TNS name or host:port/service
ORACLE_USER=my_user                # Required in non-dev mode
ORACLE_PASSWORD=my_password        # Required in non-dev mode
ORACLE_TABLE=MICRO_SVC             # Table name for job queue
```

#### **Logging**

```bash
LOG_CONSOLE_JSON=false             # true = JSON, false = pretty
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://otel.example.com/v1/logs
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://otel.example.com/v1/traces
OTEL_EXPORTER_OTLP_USER=my-user
OTEL_EXPORTER_OTLP_PASSWORD=my-password
```

#### **HTTP Server**

```bash
HTTP_HOST=0.0.0.0                  # Bind address
HTTP_PORT=8000                     # Bind port
```

#### **MongoDB Registry**

```bash
MONGODB_URI=mongodb://localhost:27017                # Empty = disabled
MONGODB_DATABASE=microservices                       # Database name
MONGODB_HEARTBEAT_SECONDS=30                         # Heartbeat interval
MONGODB_KEY_TTL_SECONDS=90                           # TTL for documents (3x heartbeat)
MONGODB_MAX_POOL_SIZE=2                              # Connection pool max
MONGODB_MIN_POOL_SIZE=1                              # Connection pool min
```

#### **Dev Mode**

```bash
DEV_MODE=true                      # Enables in-memory queue + HTTP server
DEBUG=false                        # Additional debug logging
```

### Example .env File

```bash
# Identity
MICROSERVICE_NAME=payment-service
SERVICE_VERSION=1.2.3

# Polling
POLLING_INTERVAL_SECONDS=5
MAX_CONCURRENT_JOBS=10

# Job processing
JOB_TIMEOUT_SECONDS=300

# Oracle (production)
ORACLE_DSN=XEPDB1
ORACLE_USER=my_user
ORACLE_PASSWORD=my_password
ORACLE_TABLE=MICRO_SVC

# Logging
LOG_CONSOLE_JSON=false
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://otel.example.com/v1/logs
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://otel.example.com/v1/traces
OTEL_EXPORTER_OTLP_USER=my-user
OTEL_EXPORTER_OTLP_PASSWORD=my-password

# HTTP
HTTP_HOST=0.0.0.0
HTTP_PORT=8000

# MongoDB (optional)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=microservices
MONGODB_HEARTBEAT_SECONDS=30
MONGODB_KEY_TTL_SECONDS=90

# Dev mode
DEV_MODE=false
DEBUG=false
```

---

## 15. Example Patterns & Troubleshooting

### Common Patterns with Code

#### **Pattern 1: Simple Action (No Services)**

```python
# src/actions/ping/handler.py
from usvc_lib.actions import action

@action(name="ping")
async def handle_ping() -> dict:
    return {"pong": True, "timestamp": "2026-02-19T10:00:00Z"}
```

**Test:**
```bash
curl -X POST http://localhost:8000/dev/job -d '{"action": "ping"}'
```

#### **Pattern 2: Action with Service Dependency**

```python
# src/actions/get_user/handler.py
from usvc_lib.actions import action
from services.database import DatabaseService

@action(name="get_user")
async def handle_get_user(user_id: str, db: DatabaseService) -> dict:
    user = await db.fetch_user(user_id)
    return {"user": user}
```

**Requirements:**
- `DatabaseService` registered in `main.py`
- Parameter typed as `db: DatabaseService` for DI

#### **Pattern 3: Chaining Services**

```python
# src/services/cache.py
class CacheService(ServiceProvider):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str) -> None: ...

# src/services/database.py
class DatabaseService(ServiceProvider):
    async def fetch_user(self, user_id: str) -> dict: ...

# src/actions/get_user_cached/handler.py
from usvc_lib.actions import action
from services.cache import CacheService
from services.database import DatabaseService

@action(name="get_user_cached")
async def handle_get_user_cached(
    user_id: str,
    cache: CacheService,
    db: DatabaseService
) -> dict:
    # Try cache first
    cached = await cache.get(f"user:{user_id}")
    if cached:
        return {"user": cached, "source": "cache"}

    # Fallback to database
    user = await db.fetch_user(user_id)
    await cache.set(f"user:{user_id}", str(user))
    return {"user": user, "source": "database"}
```

#### **Pattern 4: Health Monitoring in Service**

```python
# src/services/payment_api.py
from usvc_lib.services import ServiceProvider
from usvc_lib.health.status import Status
import httpx

class PaymentAPI(ServiceProvider):
    name = "payment_api"

    async def initialize(self) -> None:
        self.client = httpx.AsyncClient()
        self.health_registry.register(self.name)

    async def charge(self, amount: float) -> dict:
        try:
            response = await self.client.post("/charges", json={"amount": amount})
            response.raise_for_status()

            # Update health to GREEN
            self.health_registry.update(self.name, Status.GREEN, {"last_charge": "ok"})
            return response.json()
        except Exception as e:
            # Update health to RED
            self.health_registry.update(
                self.name,
                Status.RED,
                {"last_charge": "error", "error": str(e)}
            )
            raise
```

#### **Pattern 5: Using RestAPIService**

```python
# src/services/inventory_api.py
from usvc_lib.templates import RestAPIService, RestAPIConfig

class InventoryAPI(RestAPIService):
    config = RestAPIConfig(
        BASE_URL="https://inventory.example.com",
        RATE_LIMIT_REQUESTS=100,
        CB_FAILURE_THRESHOLD=3,
    )
    name = "inventory_api"

    async def get_stock(self, item_id: str) -> dict:
        response = await self.request("GET", f"/items/{item_id}/stock")
        response.raise_for_status()
        return response.json()

    async def reserve_item(self, item_id: str, quantity: int) -> dict:
        response = await self.request(
            "POST",
            f"/items/{item_id}/reserve",
            json={"quantity": quantity}
        )
        response.raise_for_status()
        return response.json()
```

**Register:**
```python
# main.py
app.register_service(InventoryAPI)
```

**Use in action:**
```python
@action(name="purchase")
async def handle_purchase(item_id: str, quantity: int, api: InventoryAPI) -> dict:
    stock = await api.get_stock(item_id)
    if stock["available"] >= quantity:
        result = await api.reserve_item(item_id, quantity)
        return {"reserved": True, "reservation_id": result["id"]}
    return {"reserved": False, "reason": "insufficient_stock"}
```

#### **Pattern 6: Custom Error Handling**

```python
# src/actions/transfer/handler.py
import structlog
from usvc_lib.actions import action
from services.database import DatabaseService

logger = structlog.get_logger()

class InsufficientFundsError(Exception):
    pass

@action(name="transfer_funds")
async def handle_transfer(
    from_account: str,
    to_account: str,
    amount: float,
    db: DatabaseService
) -> dict:
    # Validate accounts exist
    from_bal = await db.get_balance(from_account)
    if from_bal is None:
        logger.warning("Transfer failed - source account not found", account=from_account)
        raise ValueError(f"Source account not found: {from_account}")

    # Check sufficient funds
    if from_bal < amount:
        logger.warning(
            "Transfer failed - insufficient funds",
            account=from_account,
            balance=from_bal,
            requested=amount
        )
        raise InsufficientFundsError(
            f"Insufficient funds: balance={from_bal}, requested={amount}"
        )

    # Perform transfer (idempotent)
    transfer_id = await db.create_transfer(from_account, to_account, amount)
    logger.info("Transfer completed", transfer_id=transfer_id, amount=amount)

    return {
        "transfer_id": transfer_id,
        "from_account": from_account,
        "to_account": to_account,
        "amount": amount
    }
```

### Troubleshooting Guide

#### **"No actions discovered"**

**Symptom:**
```
RuntimeError: No actions discovered in src/actions. Ensure the directory exists and contains valid action modules.
```

**Causes:**
1. `src/actions/` directory doesn't exist
2. No `handler.py` files in subdirectories
3. Handler files exist but have no `@action` decorators

**Solution:**
```bash
# Check directory structure
ls -R src/actions/

# Expected:
# src/actions/my_action/handler.py
```

**Verify decorator:**
```python
# handler.py must have:
from usvc_lib.actions import action

@action(name="my_action")
async def handle_my_action() -> dict:
    return {}
```

#### **"Service X not registered"**

**Symptom:**
```
KeyError: No service registered for type <class 'services.database.DatabaseService'>
```

**Cause:** Service used in action but not registered in `main.py`

**Solution:**
```python
# main.py
from services.database import DatabaseService

app = Application()
app.register_service(DatabaseService)  # Add this
app.run()
```

**Check registration order:**
```python
# If PaymentAPI depends on DatabaseService:
app.register_service(DatabaseService)   # First
app.register_service(PaymentAPI)        # Second
```

#### **"Validation error"**

**Symptom:**
```json
{
  "error_code": "VALIDATION_ERROR",
  "error_message": "Field 'amount' is required"
}
```

**Cause:** Input payload doesn't match schema

**Solution:**

**Schema:**
```python
class PaymentInput(BaseModel):
    amount: float
    currency: str
```

**Payload must include both fields:**
```json
{
  "action": "process_payment",
  "amount": 100.0,
  "currency": "USD"
}
```

**Check types:**
```json
// Wrong type
{"amount": "100"}

// Correct type
{"amount": 100.0}
```

#### **"Job stuck in PROCESSING"**

**Symptom:** Job never completes or fails

**Causes:**
1. Handler has infinite loop
2. Timeout too short for long-running operations
3. Handler raises exception that's caught and ignored

**Solution:**

**1. Check timeout:**
```bash
# .env
JOB_TIMEOUT_SECONDS=300  # Increase if needed
```

**2. Add logging:**
```python
@action(name="slow_task")
async def handle_slow_task() -> dict:
    logger.info("Starting slow task")
    await long_operation()
    logger.info("Slow task completed")
    return {}
```

**3. Don't catch and suppress:**
```python
# Bad: suppresses errors
try:
    result = await process()
except Exception:
    pass  # Job hangs

# Good: re-raise
try:
    result = await process()
except Exception:
    logger.exception("Processing failed")
    raise
```

#### **"Health endpoint RED"**

**Symptom:**
```json
{
  "status": "RED",
  "checks": {
    "payment_api": {"status": "RED", "details": {"error": "timeout"}}
  }
}
```

**Solution:**

**1. Check logs:**
```bash
grep "payment_api" logs/app.log
```

**2. Check service initialization:**
```python
class PaymentAPI(ServiceProvider):
    async def initialize(self) -> None:
        # Did this succeed?
        self.client = httpx.AsyncClient()
        self.health_registry.register("payment_api")
```

**3. Check external dependencies:**
```bash
# Can you reach the API?
curl https://payments.example.com/health
```

**4. Check circuit breaker:**
```
# If too many failures, circuit opens
# Wait for CB_RECOVERY_TIMEOUT (default: 30s)
```

---

## Summary

This guide covers all key aspects of the usvc-lib framework:

- **Adding functionality:** Create action handlers in `src/actions/*/handler.py`
- **Working with patterns:** Use services, REST template, DI
- **Logging & errors:** Structured logging, correlation tokens, error handling
- **Infrastructure:** Health checks, registry, application lifecycle

**Key principles:**
- Actions are auto-discovered (no main.py changes)
- Services are explicitly registered in main.py (order matters)
- Async-first, type-safe, fail-fast
- Built-in resilience patterns (circuit breaker, retries, health checks)

**Next steps:**
1. Read relevant sections for your task
2. Check example patterns for code templates
3. Reference troubleshooting guide for common issues
4. Explore key files in `src/usvc_lib/` for implementation details

**Questions?** Review the code in the referenced files for detailed implementation.
"""
