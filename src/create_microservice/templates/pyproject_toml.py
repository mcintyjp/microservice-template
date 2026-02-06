CONTENT = """\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "$project_name"
version = "0.1.0"
description = "$project_name microservice"
requires-python = ">=3.12"
dependencies = [
    "$usvc_lib_dependency",
]

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]

[tool.hatch.metadata]
allow-direct-references = true

[tool.hatch.build.targets.wheel]
packages = ["src/$module_name", "src/actions", "src/services"]
"""
