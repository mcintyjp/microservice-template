CONTENT = """\
# {project_name}

A microservice built with [usvc-lib](https://github.com/mcintyjp/microservice-lib).

## Setup

```bash
uv sync
cp .env.example .env  # Edit as needed
```

## Run

```bash
uv run python -m {module_name}.main
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
then register it in `src/{module_name}/main.py`:

```python
from usvc_lib import Application
from services.example_api import MyAPI

app = Application()
app.register_service(MyAPI)
app.run()
```
"""
