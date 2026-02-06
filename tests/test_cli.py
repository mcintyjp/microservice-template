"""Tests for the CLI module."""

import pytest

from create_worker.cli import _normalize_name, _parse_args


class TestNormalizeName:
    def test_hyphen_to_underscore(self):
        assert _normalize_name("my-service") == "my_service"

    def test_spaces_to_underscore(self):
        assert _normalize_name("My Service") == "my_service"

    def test_already_valid(self):
        assert _normalize_name("my_service") == "my_service"

    def test_mixed_separators(self):
        assert _normalize_name("My-Cool Service") == "my_cool_service"

    def test_uppercase(self):
        assert _normalize_name("MyService") == "myservice"

    def test_strips_leading_trailing(self):
        assert _normalize_name("-my-service-") == "my_service"


class TestParseArgs:
    def test_name_required(self):
        with pytest.raises(SystemExit):
            _parse_args([])

    def test_name_only(self):
        args = _parse_args(["--name", "my-service"])
        assert args.name == "my-service"
        assert args.provider == "claude"
        assert args.no_git is False

    def test_provider_copilot(self):
        args = _parse_args(["--name", "svc", "--provider", "copilot"])
        assert args.provider == "copilot"

    def test_no_git_flag(self):
        args = _parse_args(["--name", "svc", "--no-git"])
        assert args.no_git is True

    def test_lib_source_override(self):
        args = _parse_args(["--name", "svc", "--lib-source", "usvc-lib>=0.1"])
        assert args.lib_source == "usvc-lib>=0.1"

    def test_invalid_provider(self):
        with pytest.raises(SystemExit):
            _parse_args(["--name", "svc", "--provider", "invalid"])


class TestMainExistingDir:
    def test_existing_directory_exits(self, tmp_path, monkeypatch):
        """main() should exit with error if target directory already exists."""
        import sys

        monkeypatch.chdir(tmp_path)
        (tmp_path / "existing-project").mkdir()

        from create_worker.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--name", "existing-project"])
        assert exc_info.value.code == 1
