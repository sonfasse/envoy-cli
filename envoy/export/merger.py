"""Merge multiple environment config targets into a single unified view."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.config.loader import load_config
from envoy.targets.registry import Target


class MergeError(Exception):
    """Raised when merging configs fails."""


@dataclass
class MergeResult:
    """Result of merging multiple target configs."""

    base_target: str
    merged_targets: List[str]
    # key -> value from final merged result
    values: Dict[str, str] = field(default_factory=dict)
    # key -> list of (target_name, value) showing origin of each key
    origins: Dict[str, List[tuple]] = field(default_factory=dict)
    # keys that had conflicting values across targets
    conflicts: Dict[str, List[tuple]] = field(default_factory=dict)

    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def conflict_summary(self) -> List[str]:
        lines = []
        for key, sources in self.conflicts.items():
            parts = ", ".join(f"{name}={val!r}" for name, val in sources)
            lines.append(f"{key}: [{parts}]")
        return lines


def merge_targets(
    targets: List[Target],
    base_target: Optional[Target] = None,
    override_order: bool = True,
) -> MergeResult:
    """Merge configs from multiple targets.

    Args:
        targets: List of Target objects to merge.
        base_target: If provided, treat this as the base layer (merged first).
        override_order: If True, later targets override earlier ones on conflict.

    Returns:
        MergeResult with combined values, origins, and conflict info.
    """
    if not targets:
        raise MergeError("At least one target must be provided for merging.")

    ordered = list(targets)
    if base_target and base_target in ordered:
        ordered.remove(base_target)
        ordered.insert(0, base_target)

    merged: Dict[str, str] = {}
    origins: Dict[str, List[tuple]] = {}
    conflicts: Dict[str, List[tuple]] = {}

    for target in ordered:
        try:
            config = load_config(target.resolved_path)
        except Exception as exc:
            raise MergeError(
                f"Failed to load config for target '{target.name}': {exc}"
            ) from exc

        for key, value in config.items():
            if key in merged:
                if merged[key] != value:
                    if key not in conflicts:
                        conflicts[key] = list(origins[key])
                    conflicts[key].append((target.name, value))
                if override_order:
                    merged[key] = value
            else:
                merged[key] = value

            origins.setdefault(key, []).append((target.name, value))

    base_name = base_target.name if base_target else ordered[0].name
    return MergeResult(
        base_target=base_name,
        merged_targets=[t.name for t in ordered],
        values=merged,
        origins=origins,
        conflicts=conflicts,
    )
