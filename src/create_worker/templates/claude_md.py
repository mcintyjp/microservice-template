CONTENT = """\
# {project_name}

## Architecture

This is a microservice built with `usvc-lib`. It uses a job queue pattern:
- Actions are discovered from `src/actions/` at startup
- Each action has a `handler.py` (with `@action` decorator) and `schemas.py` (Pydantic input model)
- Services in `src/services/` provide external API clients (extend `RestAPIService`)
- Configuration is loaded from `.env` via `WorkerSettings` (pydantic-settings)

## Key Commands

```bash
uv run python -m {module_name}.main    # Run the service
uv run pytest tests/ -v                # Run tests
```

## Adding a New Action

1. Create `src/actions/my_action/` with `__init__.py`, `handler.py`, `schemas.py`
2. In `handler.py`: use `@action(name="my_action")` on an async function
3. The input parameter must be a Pydantic BaseModel subclass
4. Service dependencies are injected by type-hinting parameters with ServiceProvider subclasses

## Adding a Service

1. Create a class in `src/services/` extending `RestAPIService` or `ServiceProvider`
2. Register it in `src/{module_name}/main.py` with `app.register_service(MyService)`

## Environment

- Always use `uv run` to execute commands
- DEV_MODE=true uses an in-memory queue (no Oracle needed)
"""
