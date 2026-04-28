"""Audit log for tracking envoy-cli operations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional


class AuditEvent(str, Enum):
    DIFF = "diff"
    SNAPSHOT_SAVE = "snapshot_save"
    SNAPSHOT_COMPARE = "snapshot_compare"
    SNAPSHOT_CLEAR = "snapshot_clear"


@dataclass
class AuditEntry:
    event: AuditEvent
    target: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "event": self.event.value,
            "target": self.target,
            "timestamp": self.timestamp,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            event=AuditEvent(data["event"]),
            target=data["target"],
            timestamp=data["timestamp"],
            details=data.get("details"),
        )


class AuditLog:
    def __init__(self, log_path: Path) -> None:
        self.log_path = Path(log_path)

    def record(self, entry: AuditEntry) -> None:
        """Append an audit entry to the log file."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")

    def read_all(self) -> List[AuditEntry]:
        """Return all audit entries from the log file."""
        if not self.log_path.exists():
            return []
        entries: List[AuditEntry] = []
        with self.log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(AuditEntry.from_dict(json.loads(line)))
        return entries

    def clear(self) -> None:
        """Remove all audit log entries."""
        if self.log_path.exists():
            self.log_path.unlink()
