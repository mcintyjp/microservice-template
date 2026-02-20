"""Tests for the scaffolding engine."""

import pytest

from create_microservice.scaffold import ScaffoldConfig, create_project


@pytest.fixture
def config(tmp_path):
    """A scaffold config targeting a temporary directory."""
    return ScaffoldConfig(
        project_name="test-service",
        module_name="test_service",
        target_dir=tmp_path / "test-service",
        provider="claude",
        init_git=False,  # Skip git in tests for speed
    )


class TestCreateProject:
    def test_creates_directory_tree(self, config):
        create_project(config)
        root = config.target_dir

        expected_files = [
            "pyproject.toml",
            "README.md",
            ".gitignore",
            ".env.example",
            ".env",
            "src/test_service/main.py",
            "src/test_service/config.py",
            "src/test_service/__init__.py",
            "src/actions/__init__.py",
            "src/actions/hello_world/__init__.py",
            "src/actions/hello_world/handler.py",
            "src/actions/hello_world/schemas.py",
            "src/services/__init__.py",
            "src/services/example_api.py",
            "tests/__init__.py",
            "tests/conftest.py",
            "tests/test_hello_world.py",
        ]

        for rel_path in expected_files:
            assert (root / rel_path).exists(), f"Missing: {rel_path}"

    def test_env_is_copy_of_example(self, config):
        create_project(config)
        root = config.target_dir

        example_content = (root / ".env.example").read_text()
        env_content = (root / ".env").read_text()
        assert example_content == env_content

    def test_pyproject_contains_project_name(self, config):
        create_project(config)
        content = (config.target_dir / "pyproject.toml").read_text()
        assert 'name = "test-service"' in content

    def test_pyproject_contains_lib_dependency(self, config):
        create_project(config)
        content = (config.target_dir / "pyproject.toml").read_text()
        assert "usvc-lib @ git+https://github.com/mcintyjp/microservice-lib.git" in content

    def test_main_py_imports_application(self, config):
        create_project(config)
        content = (config.target_dir / "src" / "test_service" / "main.py").read_text()
        assert "from usvc_lib import Application" in content
        assert "from test_service.config import Settings" in content
        assert "settings_class=Settings" in content
        assert "app.run()" in content


class TestProviderFiles:
    def test_claude_provider_creates_claude_files(self, config):
        config.provider = "claude"
        create_project(config)
        root = config.target_dir

        assert (root / "CLAUDE.md").exists()
        assert (root / ".claude" / "settings.json").exists()
        assert not (root / ".github" / "copilot-instructions.md").exists()

    def test_copilot_provider_creates_copilot_files(self, config):
        config.provider = "copilot"
        create_project(config)
        root = config.target_dir

        assert (root / ".github" / "copilot-instructions.md").exists()
        assert not (root / "CLAUDE.md").exists()
        assert not (root / ".claude").exists()

    def test_claude_md_contains_module_name(self, config):
        config.provider = "claude"
        create_project(config)
        content = (config.target_dir / "CLAUDE.md").read_text()
        assert "test_service" in content


class TestCustomLibSource:
    def test_custom_lib_source(self, tmp_path):
        config = ScaffoldConfig(
            project_name="my-svc",
            module_name="my_svc",
            target_dir=tmp_path / "my-svc",
            usvc_lib_dependency="usvc-lib>=0.2.0",
            init_git=False,
        )
        create_project(config)
        content = (config.target_dir / "pyproject.toml").read_text()
        assert "usvc-lib>=0.2.0" in content


class TestGeneratedPythonValidity:
    def test_all_python_files_compile(self, config):
        """All generated .py files should be syntactically valid Python."""
        create_project(config)

        py_files = list(config.target_dir.rglob("*.py"))
        assert len(py_files) > 0

        for py_file in py_files:
            source = py_file.read_text(encoding="utf-8")
            try:
                compile(source, str(py_file), "exec")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file}: {e}")
