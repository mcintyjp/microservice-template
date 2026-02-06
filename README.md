# create-microservice

CLI tool that scaffolds production-ready microservice projects built on [usvc-lib](https://github.com/mcintyjp/microservice-lib).

## Quick Start

```bash
uv tool install .
create-microservice --name my-service
cd my_service && uv sync
```

## Usage

```
create-microservice --name <project-name> [options]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--name` | Project name (required) | — |
| `--provider` | AI assistant provider (`claude` or `copilot`) | `claude` |
| `--lib-source` | usvc-lib dependency source | git+https from GitHub |
| `--no-git` | Skip `git init` | `false` |
| `--version` | Print version and exit | — |

### Examples

```bash
# Basic scaffold with Claude AI instructions
create-microservice --name order-processor

# Use Copilot instead of Claude
create-microservice --name order-processor --provider copilot

# Skip git initialization
create-microservice --name order-processor --no-git
```

## Generated Structure

```
my_service/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── CLAUDE.md                        # or .github/copilot-instructions.md
├── src/
│   ├── my_service/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── actions/
│   │   ├── __init__.py
│   │   └── hello_world/
│   │       ├── __init__.py
│   │       ├── handler.py
│   │       └── schemas.py
│   └── services/
│       ├── __init__.py
│       └── example_api.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_hello_world.py
```

## Development

```bash
uv sync
uv run pytest
```
