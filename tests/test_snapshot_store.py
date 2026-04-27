"""Tests for envoy.snapshot.store."""

import json
import pytest
from pathlib import Path

from envoy.snapshot.store import Snapshot, SnapshotStore, SnapshotError


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "snapshots.json"


@pytest.fixture
def store(store_path: Path) -> SnapshotStore:
    return SnapshotStore(store_path)


def make_snapshot(target: str = "prod", env: dict | None = None, label: str | None = None) -> Snapshot:
    return Snapshot(target=target, env=env or {"KEY": "value"}, label=label)


# ---------------------------------------------------------------------------
# Snapshot dataclass
# ---------------------------------------------------------------------------

def test_snapshot_roundtrip():
    snap = make_snapshot(label="before-deploy")
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored.target == snap.target
    assert restored.env == snap.env
    assert restored.label == snap.label
    assert restored.created_at == snap.created_at


def test_snapshot_label_optional():
    snap = make_snapshot()
    assert snap.label is None
    assert Snapshot.from_dict(snap.to_dict()).label is None


# ---------------------------------------------------------------------------
# SnapshotStore.save / list_for_target
# ---------------------------------------------------------------------------

def test_save_creates_file(store: SnapshotStore, store_path: Path):
    store.save(make_snapshot())
    assert store_path.exists()


def test_list_empty_when_no_file(store: SnapshotStore):
    assert store.list_for_target("prod") == []


def test_list_returns_saved_snapshots(store: SnapshotStore):
    store.save(make_snapshot(env={"A": "1"}))
    store.save(make_snapshot(env={"A": "2"}))
    snaps = store.list_for_target("prod")
    assert len(snaps) == 2
    assert snaps[0].env == {"A": "1"}
    assert snaps[1].env == {"A": "2"}


def test_list_filters_by_target(store: SnapshotStore):
    store.save(make_snapshot(target="prod"))
    store.save(make_snapshot(target="staging"))
    assert len(store.list_for_target("prod")) == 1
    assert len(store.list_for_target("staging")) == 1


# ---------------------------------------------------------------------------
# SnapshotStore.latest_for_target
# ---------------------------------------------------------------------------

def test_latest_returns_none_when_empty(store: SnapshotStore):
    assert store.latest_for_target("prod") is None


def test_latest_returns_last_saved(store: SnapshotStore):
    store.save(make_snapshot(env={"V": "old"}))
    store.save(make_snapshot(env={"V": "new"}))
    latest = store.latest_for_target("prod")
    assert latest is not None
    assert latest.env["V"] == "new"


# ---------------------------------------------------------------------------
# SnapshotStore.clear_for_target
# ---------------------------------------------------------------------------

def test_clear_removes_target_snapshots(store: SnapshotStore):
    store.save(make_snapshot(target="prod"))
    store.save(make_snapshot(target="staging"))
    removed = store.clear_for_target("prod")
    assert removed == 1
    assert store.list_for_target("prod") == []
    assert len(store.list_for_target("staging")) == 1


def test_clear_returns_zero_when_none(store: SnapshotStore):
    assert store.clear_for_target("ghost") == 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_load_raises_on_corrupt_json(store_path: Path):
    store_path.write_text("NOT JSON", encoding="utf-8")
    s = SnapshotStore(store_path)
    with pytest.raises(SnapshotError):
        s.list_for_target("prod")


def test_parent_dirs_created_automatically(tmp_path: Path):
    nested = tmp_path / "a" / "b" / "snapshots.json"
    s = SnapshotStore(nested)
    s.save(make_snapshot())
    assert nested.exists()
