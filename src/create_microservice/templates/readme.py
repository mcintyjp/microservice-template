CONTENT = """\
# $project_name

A microservice built with [usvc-lib](https://github.com/mcintyjp/microservice-lib).

## Setup

```bash
uv sync
```

> **Note:** `.env` is already created from `.env.example` during scaffolding.
> Copying again would overwrite the file. Edit `.env` directly as needed.

### Upgrading usvc-lib

To pull the latest changes from the `usvc-lib` dependency:

```bash
uv sync --upgrade-package usvc-lib
```

This updates the lock file with the latest commit from the library's repository and syncs your environment.

## Configuration

### OpenTelemetry (Optional)

To enable distributed tracing and observability, configure these environment variables in `.env`:

- `OTEL_EXPORTER_OTLP_ENDPOINT` — URL of your OTLP collector (e.g., `http://localhost:4318`)
- `OTEL_EXPORTER_OTLP_USER` — Username for authenticated OTLP endpoints
- `OTEL_EXPORTER_OTLP_PASSWORD` — Password for authenticated OTLP endpoints

These credentials are used when your OpenTelemetry collector requires HTTP basic authentication.

## Run

```bash
uv run python -m $module_name.main
```

## Test

```bash
uv run pytest tests/ -v
```

## Adding Actions

Create a new directory under `src/actions/` with:
- `handler.py` — async handler function decorated with `@action(name="your_action")`
- `schemas.py` — Pydantic `BaseModel` for the action input

See `src/actions/hello_world/` for an example.

## Adding Services

Create a service class in `src/services/` that extends `ServiceProvider` or `RestAPIService`,
then register it in `src/$module_name/main.py`:

```python
from usvc_lib import Application
from services.example_api import MyAPI

app = Application()
app.register_service(MyAPI)
app.run()
```
"""
