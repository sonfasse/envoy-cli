"""Compare snapshots to produce diff results."""

from __future__ import annotations

from typing import Optional

from envoy.diff.engine import DiffResult, compute_diff
from envoy.snapshot.store import Snapshot, SnapshotStore, SnapshotError


class SnapshotDiffError(Exception):
    """Raised when a snapshot diff operation fails."""


def diff_snapshots(
    store: SnapshotStore,
    label_a: str,
    label_b: str,
    include_unchanged: bool = False,
) -> DiffResult:
    """Load two snapshots by label and return a DiffResult between them.

    Args:
        store: The SnapshotStore to load snapshots from.
        label_a: Label of the base snapshot.
        label_b: Label of the target snapshot.
        include_unchanged: Whether to include unchanged keys in the result.

    Returns:
        A DiffResult comparing the two snapshots.

    Raises:
        SnapshotDiffError: If either snapshot cannot be found.
    """
    snap_a = store.get(label_a)
    if snap_a is None:
        raise SnapshotDiffError(f"Snapshot not found: '{label_a}'")

    snap_b = store.get(label_b)
    if snap_b is None:
        raise SnapshotDiffError(f"Snapshot not found: '{label_b}'")

    return compute_diff(
        snap_a.variables,
        snap_b.variables,
        include_unchanged=include_unchanged,
    )


def diff_snapshot_against_env(
    store: SnapshotStore,
    label: str,
    env: dict[str, str],
    include_unchanged: bool = False,
) -> DiffResult:
    """Compare a stored snapshot against a live environment dict.

    Args:
        store: The SnapshotStore to load the snapshot from.
        label: Label of the snapshot to compare.
        env: Live environment variables dict.
        include_unchanged: Whether to include unchanged keys.

    Returns:
        A DiffResult comparing snapshot to live env.

    Raises:
        SnapshotDiffError: If the snapshot cannot be found.
    """
    snap = store.get(label)
    if snap is None:
        raise SnapshotDiffError(f"Snapshot not found: '{label}'")

    return compute_diff(
        snap.variables,
        env,
        include_unchanged=include_unchanged,
    )
