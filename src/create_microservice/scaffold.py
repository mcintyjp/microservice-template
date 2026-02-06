"""Core scaffolding engine for project generation."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from create_microservice.templates import (
    CLAUDE_MANIFEST,
    COPILOT_MANIFEST,
    MANIFEST,
    render,
)


@dataclass
class ScaffoldConfig:
    project_name: str
    module_name: str
    target_dir: Path
    provider: str = "claude"
    usvc_lib_dependency: str = "usvc-lib @ git+https://github.com/mcintyjp/microservice-lib.git"
    init_git: bool = True


def create_project(config: ScaffoldConfig) -> None:
    """Create a complete microservice project from templates."""
    template_vars = {
        "project_name": config.project_name,
        "module_name": config.module_name,
        "usvc_lib_dependency": config.usvc_lib_dependency,
    }

    # Write base manifest files
    for template_module, path_template in MANIFEST:
        rel_path = path_template.format(**template_vars)
        _write_file(config.target_dir, rel_path, render(template_module, **template_vars))

    # Write provider-specific files
    if config.provider == "claude":
        provider_manifest = CLAUDE_MANIFEST
    elif config.provider == "copilot":
        provider_manifest = COPILOT_MANIFEST
    else:
        provider_manifest = []

    for template_module, path_template in provider_manifest:
        rel_path = path_template.format(**template_vars)
        _write_file(config.target_dir, rel_path, render(template_module, **template_vars))

    # Copy .env.example to .env
    env_example = config.target_dir / ".env.example"
    env_file = config.target_dir / ".env"
    if env_example.exists():
        shutil.copy2(env_example, env_file)

    # Git init
    if config.init_git:
        _git_init(config.target_dir)

    # Print next steps
    _print_next_steps(config)


def _write_file(base_dir: Path, rel_path: str, content: str) -> None:
    """Write content to a file, creating parent directories as needed."""
    file_path = base_dir / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def _git_init(target_dir: Path) -> None:
    """Initialize a git repo and create an initial commit."""
    try:
        subprocess.run(["git", "init"], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial scaffold from create-microservice"],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Warning: git init failed ({e}). Skipping.", file=sys.stderr)


def _print_next_steps(config: ScaffoldConfig) -> None:
    """Print instructions for getting started."""
    print(f"\nCreated project: {config.project_name}")
    print(f"  Directory: {config.target_dir}\n")
    print("Next steps:")
    print(f"  cd {config.target_dir.name}")
    print("  uv sync")
    print("  # Edit .env as needed")
    print(f"  uv run python -m {config.module_name}.main")
    print(f"  uv run pytest tests/ -v")
