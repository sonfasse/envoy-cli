"""Target registry for managing deployment targets and their config sources."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class TargetLoadError(Exception):
    """Raised when a target configuration cannot be loaded."""


@dataclass
class Target:
    """Represents a single deployment target with an associated config file."""

    name: str
    config_path: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Target name must not be empty")
        if not self.config_path or not self.config_path.strip():
            raise ValueError("Target config_path must not be empty")

    def resolved_path(self, base_dir: Optional[Path] = None) -> Path:
        """Return the config path, optionally resolved relative to a base directory."""
        p = Path(self.config_path)
        if base_dir and not p.is_absolute():
            return base_dir / p
        return p


class TargetRegistry:
    """Holds all known deployment targets loaded from a targets manifest."""

    def __init__(self, targets: Optional[List[Target]] = None) -> None:
        self._targets: Dict[str, Target] = {}
        for t in targets or []:
            self._register(t)

    def _register(self, target: Target) -> None:
        if target.name in self._targets:
            raise TargetLoadError(f"Duplicate target name: '{target.name}'")
        self._targets[target.name] = target

    def get(self, name: str) -> Target:
        if name not in self._targets:
            raise TargetLoadError(f"Unknown target: '{name}'")
        return self._targets[name]

    def all(self) -> List[Target]:
        return list(self._targets.values())

    def names(self) -> List[str]:
        return list(self._targets.keys())

    @classmethod
    def from_file(cls, path: str | Path) -> "TargetRegistry":
        """Load a TargetRegistry from a JSON manifest file.

        Expected format::

            {
              "targets": [
                {"name": "staging", "config_path": "envs/staging.env"},
                {"name": "production", "config_path": "envs/production.env", "tags": ["prod"]}
              ]
            }
        """
        p = Path(path)
        if not p.exists():
            raise TargetLoadError(f"Targets manifest not found: {p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TargetLoadError(f"Invalid JSON in targets manifest: {exc}") from exc

        raw_targets = data.get("targets")
        if not isinstance(raw_targets, list):
            raise TargetLoadError("Targets manifest must contain a 'targets' list")

        targets: List[Target] = []
        for idx, entry in enumerate(raw_targets):
            if not isinstance(entry, dict):
                raise TargetLoadError(f"Target entry {idx} must be a JSON object")
            try:
                targets.append(
                    Target(
                        name=entry["name"],
                        config_path=entry["config_path"],
                        description=entry.get("description"),
                        tags=entry.get("tags", []),
                    )
                )
            except KeyError as exc:
                raise TargetLoadError(f"Target entry {idx} missing required key: {exc}") from exc
            except ValueError as exc:
                raise TargetLoadError(f"Target entry {idx} invalid: {exc}") from exc

        return cls(targets)
