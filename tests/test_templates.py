"""Tests for template modules."""

import pytest

from create_worker.templates import (
    CLAUDE_MANIFEST,
    COPILOT_MANIFEST,
    MANIFEST,
    render,
)


TEMPLATE_VARS = {
    "project_name": "test-service",
    "module_name": "test_service",
    "usvc_lib_dependency": "usvc-lib @ git+https://github.com/mcintyjp/microservice-lib.git",
}


class TestTemplateRendering:
    @pytest.mark.parametrize(
        "template_module,path_template",
        MANIFEST + CLAUDE_MANIFEST + COPILOT_MANIFEST,
        ids=lambda x: x if isinstance(x, str) else getattr(x, "__name__", str(x)),
    )
    def test_no_unresolved_placeholders(self, template_module, path_template):
        """Template placeholders should all be resolved after rendering."""
        rendered = render(template_module, **TEMPLATE_VARS)
        # Only check for our known template variables remaining unresolved
        for var_name in TEMPLATE_VARS:
            assert f"{{{var_name}}}" not in rendered, (
                f"Unresolved placeholder {{{var_name}}} in {path_template}"
            )


class TestPythonTemplateSyntax:
    """Verify that templates producing Python files are syntactically valid."""

    PYTHON_TEMPLATES = [
        (mod, path)
        for mod, path in MANIFEST + CLAUDE_MANIFEST + COPILOT_MANIFEST
        if path.endswith(".py")
    ]

    @pytest.mark.parametrize(
        "template_module,path_template",
        PYTHON_TEMPLATES,
        ids=lambda x: x if isinstance(x, str) else getattr(x, "__name__", str(x)),
    )
    def test_python_compile(self, template_module, path_template):
        """Rendered Python templates should pass compile()."""
        rendered = render(template_module, **TEMPLATE_VARS)
        compile(rendered, path_template, "exec")


class TestManifestCompleteness:
    def test_manifest_has_entries(self):
        assert len(MANIFEST) > 0

    def test_claude_manifest_has_entries(self):
        assert len(CLAUDE_MANIFEST) > 0

    def test_copilot_manifest_has_entries(self):
        assert len(COPILOT_MANIFEST) > 0

    def test_all_templates_have_content(self):
        for template_module, _ in MANIFEST + CLAUDE_MANIFEST + COPILOT_MANIFEST:
            assert hasattr(template_module, "CONTENT"), (
                f"{template_module} missing CONTENT attribute"
            )
