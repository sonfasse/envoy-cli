"""Snapshot store for saving and loading environment variable snapshots."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class Snapshot:
    """A point-in-time capture of an environment config for a target."""

    target: str
    env: Dict[str, str]
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "env": self.env,
            "created_at": self.created_at,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            target=data["target"],
            env=data["env"],
            created_at=data["created_at"],
            label=data.get("label"),
        )


class SnapshotStore:
    """Persists and retrieves snapshots from a JSON file."""

    def __init__(self, store_path: str | Path) -> None:
        self.store_path = Path(store_path)

    def _load_all(self) -> List[dict]:
        if not self.store_path.exists():
            return []
        try:
            with self.store_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            raise SnapshotError(f"Failed to read snapshot store: {exc}") from exc

    def _save_all(self, records: List[dict]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.store_path.open("w", encoding="utf-8") as fh:
                json.dump(records, fh, indent=2)
        except OSError as exc:
            raise SnapshotError(f"Failed to write snapshot store: {exc}") from exc

    def save(self, snapshot: Snapshot) -> None:
        """Append a snapshot to the store."""
        records = self._load_all()
        records.append(snapshot.to_dict())
        self._save_all(records)

    def list_for_target(self, target: str) -> List[Snapshot]:
        """Return all snapshots for a given target, oldest first."""
        return [
            Snapshot.from_dict(r)
            for r in self._load_all()
            if r.get("target") == target
        ]

    def latest_for_target(self, target: str) -> Optional[Snapshot]:
        """Return the most recently saved snapshot for a target, or None."""
        snaps = self.list_for_target(target)
        return snaps[-1] if snaps else None

    def clear_for_target(self, target: str) -> int:
        """Remove all snapshots for a target. Returns number removed."""
        records = self._load_all()
        remaining = [r for r in records if r.get("target") != target]
        removed = len(records) - len(remaining)
        self._save_all(remaining)
        return removed
