"""Tests for snapshot-diff CLI commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli.snapshot_diff_commands import snapshot_diff_group
from envoy.snapshot.store import Snapshot, SnapshotStore


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def store_file(tmp_path: Path) -> Path:
    path = tmp_path / "snapshots.json"
    store = SnapshotStore(path)
    store.save(Snapshot(target="api", variables={"HOST": "localhost", "PORT": "8080"}, label="base"))
    store.save(Snapshot(target="api", variables={"HOST": "prod.example.com", "PORT": "443", "TLS": "true"}, label="prod"))
    return path


def test_compare_shows_changed_key(runner: CliRunner, store_file: Path) -> None:
    result = runner.invoke(
        snapshot_diff_group,
        ["compare", "base", "prod", "--store", str(store_file)],
    )
    assert result.exit_code == 0
    assert "HOST" in result.output


def test_compare_shows_added_key(runner: CliRunner, store_file: Path) -> None:
    result = runner.invoke(
        snapshot_diff_group,
        ["compare", "base", "prod", "--store", str(store_file)],
    )
    assert result.exit_code == 0
    assert "TLS" in result.output


def test_compare_no_differences_message(runner: CliRunner, store_file: Path) -> None:
    result = runner.invoke(
        snapshot_diff_group,
        ["compare", "base", "base", "--store", str(store_file)],
    )
    assert result.exit_code == 0
    assert "No differences found" in result.output


def test_compare_include_unchanged(runner: CliRunner, store_file: Path) -> None:
    result = runner.invoke(
        snapshot_diff_group,
        ["compare", "base", "base", "--store", str(store_file), "--all"],
    )
    assert result.exit_code == 0
    assert "HOST" in result.output


def test_compare_missing_label_exits_nonzero(runner: CliRunner, store_file: Path) -> None:
    result = runner.invoke(
        snapshot_diff_group,
        ["compare", "base", "ghost", "--store", str(store_file)],
    )
    assert result.exit_code != 0
    assert "ghost" in result.output


def test_compare_missing_store_exits_nonzero(runner: CliRunner, tmp_path: Path) -> None:
    missing = tmp_path / "no_such.json"
    result = runner.invoke(
        snapshot_diff_group,
        ["compare", "a", "b", "--store", str(missing)],
    )
    assert result.exit_code != 0
