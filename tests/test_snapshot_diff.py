"""Tests for envoy.snapshot.diff module."""

import pytest
from pathlib import Path

from envoy.snapshot.store import Snapshot, SnapshotStore
from envoy.snapshot.diff import (
    SnapshotDiffError,
    diff_snapshots,
    diff_snapshot_against_env,
)
from envoy.diff.engine import DiffStatus


@pytest.fixture
def store(tmp_path: Path) -> SnapshotStore:
    return SnapshotStore(tmp_path / "snapshots.json")


@pytest.fixture
def populated_store(store: SnapshotStore) -> SnapshotStore:
    store.save(Snapshot(target="web", variables={"A": "1", "B": "old"}, label="v1"))
    store.save(Snapshot(target="web", variables={"A": "1", "B": "new", "C": "3"}, label="v2"))
    return store


def test_diff_snapshots_detects_changed(populated_store: SnapshotStore) -> None:
    result = diff_snapshots(populated_store, "v1", "v2")
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["B"] == DiffStatus.CHANGED


def test_diff_snapshots_detects_added(populated_store: SnapshotStore) -> None:
    result = diff_snapshots(populated_store, "v1", "v2")
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["C"] == DiffStatus.ADDED


def test_diff_snapshots_unchanged_excluded_by_default(populated_store: SnapshotStore) -> None:
    result = diff_snapshots(populated_store, "v1", "v2")
    statuses = {e.key: e.status for e in result.entries}
    assert "A" not in statuses


def test_diff_snapshots_unchanged_included_when_requested(populated_store: SnapshotStore) -> None:
    result = diff_snapshots(populated_store, "v1", "v2", include_unchanged=True)
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["A"] == DiffStatus.UNCHANGED


def test_diff_snapshots_missing_label_a_raises(populated_store: SnapshotStore) -> None:
    with pytest.raises(SnapshotDiffError, match="missing"):
        diff_snapshots(populated_store, "missing", "v2")


def test_diff_snapshots_missing_label_b_raises(populated_store: SnapshotStore) -> None:
    with pytest.raises(SnapshotDiffError, match="missing"):
        diff_snapshots(populated_store, "v1", "missing")


def test_diff_snapshot_against_env_detects_changes(populated_store: SnapshotStore) -> None:
    live = {"A": "1", "B": "live", "D": "4"}
    result = diff_snapshot_against_env(populated_store, "v1", live)
    statuses = {e.key: e.status for e in result.entries}
    assert statuses["B"] == DiffStatus.CHANGED
    assert statuses["D"] == DiffStatus.ADDED


def test_diff_snapshot_against_env_missing_label_raises(populated_store: SnapshotStore) -> None:
    with pytest.raises(SnapshotDiffError, match="ghost"):
        diff_snapshot_against_env(populated_store, "ghost", {"X": "1"})
