"""Tests for envoy.validate.checker."""

import json
import os
from pathlib import Path

import pytest

from envoy.targets.registry import Target
from envoy.validate.checker import (
    ValidationError,
    ValidationResult,
    validate_target,
    validate_all_targets,
)


def write_env(path: Path, content: str) -> None:
    path.write_text(content)


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.env"
    write_env(p, "DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\nDEBUG=\n")
    return p


def make_target(name: str, path: Path) -> Target:
    return Target(name=name, config_path=str(path))


class TestValidationResult:
    def test_is_valid_when_no_issues(self):
        r = ValidationResult(target_name="prod")
        assert r.is_valid is True

    def test_invalid_when_missing_required(self):
        r = ValidationResult(target_name="prod", missing_required=["SECRET_KEY"])
        assert r.is_valid is False

    def test_invalid_when_empty_values(self):
        r = ValidationResult(target_name="prod", empty_values=["DEBUG"])
        assert r.is_valid is False

    def test_summary_contains_target_name(self):
        r = ValidationResult(target_name="staging")
        assert "staging" in r.summary()

    def test_summary_shows_passed_when_valid(self):
        r = ValidationResult(target_name="prod")
        assert "passed" in r.summary()

    def test_summary_lists_missing_keys(self):
        r = ValidationResult(target_name="prod", missing_required=["API_KEY"])
        assert "API_KEY" in r.summary()

    def test_summary_lists_unknown_keys(self):
        r = ValidationResult(target_name="prod", unknown_keys=["ROGUE_VAR"])
        assert "ROGUE_VAR" in r.summary()


class TestValidateTarget:
    def test_all_required_present_is_valid(self, env_file: Path):
        t = make_target("prod", env_file)
        result = validate_target(t, required_keys=["DATABASE_URL", "SECRET_KEY"])
        assert result.is_valid is True
        assert result.missing_required == []

    def test_missing_required_key_reported(self, env_file: Path):
        t = make_target("prod", env_file)
        result = validate_target(t, required_keys=["MISSING_KEY"])
        assert "MISSING_KEY" in result.missing_required
        assert result.is_valid is False

    def test_empty_value_reported(self, env_file: Path):
        t = make_target("prod", env_file)
        result = validate_target(t, required_keys=["DEBUG"])
        assert "DEBUG" in result.empty_values
        assert result.is_valid is False

    def test_unknown_keys_detected_with_schema(self, env_file: Path):
        t = make_target("prod", env_file)
        result = validate_target(t, schema_keys=["DATABASE_URL"])
        assert "SECRET_KEY" in result.unknown_keys or "DEBUG" in result.unknown_keys

    def test_no_unknown_keys_when_schema_matches(self, env_file: Path):
        t = make_target("prod", env_file)
        result = validate_target(
            t, schema_keys=["DATABASE_URL", "SECRET_KEY", "DEBUG"]
        )
        assert result.unknown_keys == []

    def test_missing_file_raises_validation_error(self, tmp_path: Path):
        t = make_target("prod", tmp_path / "nonexistent.env")
        with pytest.raises(ValidationError):
            validate_target(t, required_keys=["KEY"])


def test_validate_all_targets_returns_one_per_target(env_file: Path, tmp_path: Path):
    env2 = tmp_path / "b.env"
    write_env(env2, "API_KEY=xyz\n")
    targets = [make_target("a", env_file), make_target("b", env2)]
    results = validate_all_targets(targets, required_keys=["API_KEY"])
    assert len(results) == 2
    names = {r.target_name for r in results}
    assert names == {"a", "b"}
