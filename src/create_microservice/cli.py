"""CLI entry point for create-microservice."""

from __future__ import annotations

import argparse
import re
import sys
from importlib.metadata import version
from pathlib import Path

from create_microservice.scaffold import ScaffoldConfig, create_project

DEFAULT_LIB_SOURCE = "usvc-lib @ git+https://github.com/mcintyjp/microservice-lib.git"


def _normalize_name(name: str) -> str:
    """Convert a project name to a valid Python module name.

    'my-service' -> 'my_service'
    'My Service' -> 'my_service'
    """
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="create-microservice",
        description="Scaffold a new usvc-lib microservice project.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Project name (e.g., my-service)",
    )
    parser.add_argument(
        "--provider",
        choices=["claude", "copilot"],
        default="claude",
        help="AI assistant provider (default: claude)",
    )
    parser.add_argument(
        "--lib-source",
        default=DEFAULT_LIB_SOURCE,
        help=f"usvc-lib dependency source (default: {DEFAULT_LIB_SOURCE})",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Skip git init",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('create-microservice')}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    project_name = args.name
    module_name = _normalize_name(project_name)

    if not re.match(r"^[a-z_][a-z0-9_]*$", module_name):
        print(
            f"Error: '{project_name}' cannot be converted to a valid Python module name.",
            file=sys.stderr,
        )
        sys.exit(1)

    target_dir = Path.cwd() / module_name

    if target_dir.exists():
        print(f"Error: directory '{target_dir}' already exists.", file=sys.stderr)
        sys.exit(1)

    config = ScaffoldConfig(
        project_name=project_name,
        module_name=module_name,
        target_dir=target_dir,
        provider=args.provider,
        usvc_lib_dependency=args.lib_source,
        init_git=not args.no_git,
    )

    create_project(config)
