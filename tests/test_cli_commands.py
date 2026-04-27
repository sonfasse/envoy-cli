"""Tests for CLI commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli.commands import cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_env_files(tmp_path):
    """Create two simple .env files and a registry pointing to them."""
    staging = tmp_path / "staging.env"
    staging.write_text("DB_HOST=staging.db\nDEBUG=true\nAPI_KEY=secret\n")

    production = tmp_path / "production.env"
    production.write_text("DB_HOST=prod.db\nDEBUG=false\nNEW_KEY=added\n")

    registry_data = {
        "targets": [
            {"name": "staging", "config_path": str(staging)},
            {"name": "production", "config_path": str(production)},
        ]
    }
    registry_file = tmp_path / "targets.json"
    registry_file.write_text(json.dumps(registry_data))

    return tmp_path, registry_file


def test_diff_shows_changes(runner, tmp_env_files):
    _, registry_file = tmp_env_files
    result = runner.invoke(
        cli, ["diff", "staging", "production", "--registry", str(registry_file)]
    )
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "DEBUG" in result.output


def test_diff_no_differences_message(runner, tmp_path):
    env_file = tmp_path / "same.env"
    env_file.write_text("FOO=bar\n")
    registry_data = {
        "targets": [
            {"name": "a", "config_path": str(env_file)},
            {"name": "b", "config_path": str(env_file)},
        ]
    }
    registry_file = tmp_path / "targets.json"
    registry_file.write_text(json.dumps(registry_data))

    result = runner.invoke(cli, ["diff", "a", "b", "--registry", str(registry_file)])
    assert result.exit_code == 0
    assert "No differences found" in result.output


def test_diff_unknown_target_exits_nonzero(runner, tmp_env_files):
    _, registry_file = tmp_env_files
    result = runner.invoke(
        cli, ["diff", "staging", "nonexistent", "--registry", str(registry_file)]
    )
    assert result.exit_code != 0


def test_diff_missing_registry_exits_nonzero(runner, tmp_path):
    result = runner.invoke(
        cli,
        ["diff", "staging", "production", "--registry", str(tmp_path / "missing.json")],
    )
    assert result.exit_code != 0


def test_list_shows_targets(runner, tmp_env_files):
    _, registry_file = tmp_env_files
    result = runner.invoke(cli, ["list", "--registry", str(registry_file)])
    assert result.exit_code == 0
    assert "staging" in result.output
    assert "production" in result.output


def test_list_empty_registry(runner, tmp_path):
    registry_file = tmp_path / "targets.json"
    registry_file.write_text(json.dumps({"targets": []}))
    result = runner.invoke(cli, ["list", "--registry", str(registry_file)])
    assert result.exit_code == 0
    assert "No targets registered" in result.output


def test_version_flag(runner):
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
