"""Validation module for checking env config targets against defined rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.targets.registry import Target
from envoy.config.loader import load_config


class ValidationError(Exception):
    """Raised when validation cannot be performed."""


@dataclass
class ValidationResult:
    target_name: str
    missing_required: List[str] = field(default_factory=list)
    empty_values: List[str] = field(default_factory=list)
    unknown_keys: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not (self.missing_required or self.empty_values)

    def summary(self) -> str:
        lines = [f"Target: {self.target_name}"]
        if self.is_valid:
            lines.append("  ✓ All checks passed")
        else:
            for key in self.missing_required:
                lines.append(f"  ✗ Missing required key: {key}")
            for key in self.empty_values:
                lines.append(f"  ⚠ Empty value for key: {key}")
        if self.unknown_keys:
            for key in self.unknown_keys:
                lines.append(f"  ? Unknown key (not in schema): {key}")
        return "\n".join(lines)


def validate_target(
    target: Target,
    required_keys: Optional[List[str]] = None,
    schema_keys: Optional[List[str]] = None,
) -> ValidationResult:
    """Validate a single target's env config."""
    try:
        config: Dict[str, str] = load_config(target.resolved_path)
    except Exception as exc:
        raise ValidationError(f"Could not load config for '{target.name}': {exc}") from exc

    result = ValidationResult(target_name=target.name)

    if required_keys:
        for key in required_keys:
            if key not in config:
                result.missing_required.append(key)
            elif config[key].strip() == "":
                result.empty_values.append(key)

    if schema_keys:
        for key in config:
            if key not in schema_keys:
                result.unknown_keys.append(key)

    return result


def validate_all_targets(
    targets: List[Target],
    required_keys: Optional[List[str]] = None,
    schema_keys: Optional[List[str]] = None,
) -> List[ValidationResult]:
    """Validate multiple targets and return all results."""
    return [
        validate_target(t, required_keys=required_keys, schema_keys=schema_keys)
        for t in targets
    ]
