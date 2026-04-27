"""Diff engine for comparing environment variable configs across targets."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class DiffStatus(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    status: DiffStatus
    base_value: Optional[str] = None
    target_value: Optional[str] = None

    @property
    def is_sensitive(self) -> bool:
        """Heuristic check for sensitive keys."""
        sensitive_patterns = ("SECRET", "PASSWORD", "TOKEN", "KEY", "PASS")
        return any(p in self.key.upper() for p in sensitive_patterns)


@dataclass
class DiffResult:
    base_name: str
    target_name: str
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.ADDED]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.REMOVED]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.CHANGED]

    @property
    def unchanged(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.UNCHANGED]

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def diff_configs(
    base: Dict[str, str],
    target: Dict[str, str],
    base_name: str = "base",
    target_name: str = "target",
    include_unchanged: bool = False,
) -> DiffResult:
    """Compare two env config dicts and return a DiffResult."""
    result = DiffResult(base_name=base_name, target_name=target_name)
    all_keys = sorted(set(base.keys()) | set(target.keys()))

    for key in all_keys:
        in_base = key in base
        in_target = key in target

        if in_base and not in_target:
            result.entries.append(
                DiffEntry(key=key, status=DiffStatus.REMOVED, base_value=base[key])
            )
        elif not in_base and in_target:
            result.entries.append(
                DiffEntry(key=key, status=DiffStatus.ADDED, target_value=target[key])
            )
        elif base[key] != target[key]:
            result.entries.append(
                DiffEntry(
                    key=key,
                    status=DiffStatus.CHANGED,
                    base_value=base[key],
                    target_value=target[key],
                )
            )
        elif include_unchanged:
            result.entries.append(
                DiffEntry(
                    key=key,
                    status=DiffStatus.UNCHANGED,
                    base_value=base[key],
                    target_value=target[key],
                )
            )

    return result
