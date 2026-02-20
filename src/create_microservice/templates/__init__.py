"""Template modules and manifest for project scaffolding."""

from __future__ import annotations

from string import Template

from create_microservice.templates import (
    action_handler,
    action_schema,
    claude_md,
    claude_settings,
    config_py,
    conftest_py,
    copilot_md,
    env_example,
    gitignore,
    init_py,
    main_py,
    pyproject_toml,
    readme,
    service_example,
    test_example,
)

# (template_module, relative_path_template)
# Paths can contain {module_name} for project-specific paths.
MANIFEST: list[tuple[object, str]] = [
    (pyproject_toml, "pyproject.toml"),
    (readme, "README.md"),
    (gitignore, ".gitignore"),
    (env_example, ".env.example"),
    (main_py, "src/{module_name}/main.py"),
    (config_py, "src/{module_name}/config.py"),
    (init_py, "src/{module_name}/__init__.py"),
    (action_handler, "src/actions/hello_world/handler.py"),
    (action_schema, "src/actions/hello_world/schemas.py"),
    (init_py, "src/actions/__init__.py"),
    (init_py, "src/actions/hello_world/__init__.py"),
    (service_example, "src/services/example_api.py"),
    (init_py, "src/services/__init__.py"),
    (conftest_py, "tests/conftest.py"),
    (test_example, "tests/test_hello_world.py"),
    (init_py, "tests/__init__.py"),
]

# Provider-specific files
CLAUDE_MANIFEST: list[tuple[object, str]] = [
    (claude_md, "CLAUDE.md"),
    (claude_settings, ".claude/settings.json"),
]

COPILOT_MANIFEST: list[tuple[object, str]] = [
    (copilot_md, ".github/copilot-instructions.md"),
]


def render(template_module: object, **kwargs: str) -> str:
    """Render a template module's CONTENT with the given variables."""
    content: str = getattr(template_module, "CONTENT")
    return Template(content).substitute(**kwargs)
