"""Export environment configs to various output formats."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


class ExportFormat(str, Enum):
    ENV = "env"
    JSON = "json"
    YAML = "yaml"


class ExportError(Exception):
    """Raised when an export operation fails."""


def export_env(data: Dict[str, str], output_path: Optional[Path] = None) -> str:
    """Serialize key/value pairs as a .env formatted string.

    Keys with values containing spaces or special characters are quoted.
    Returns the rendered string and optionally writes to *output_path*.
    """
    lines = []
    for key, value in sorted(data.items()):
        needs_quotes = any(c in value for c in (" ", "\t", "#", "'", '"'))
        formatted_value = f'"{value}"' if needs_quotes else value
        lines.append(f"{key}={formatted_value}")
    content = "\n".join(lines) + ("\n" if lines else "")
    if output_path is not None:
        Path(output_path).write_text(content, encoding="utf-8")
    return content


def export_json(data: Dict[str, str], output_path: Optional[Path] = None) -> str:
    """Serialize key/value pairs as pretty-printed JSON."""
    content = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if output_path is not None:
        Path(output_path).write_text(content, encoding="utf-8")
    return content


def export_yaml(data: Dict[str, str], output_path: Optional[Path] = None) -> str:
    """Serialize key/value pairs as YAML.

    Raises ExportError if PyYAML is not installed.
    """
    if not _YAML_AVAILABLE:
        raise ExportError(
            "PyYAML is required for YAML export. Install it with: pip install pyyaml"
        )
    content = _yaml.dump(dict(sorted(data.items())), default_flow_style=False, allow_unicode=True)
    if output_path is not None:
        Path(output_path).write_text(content, encoding="utf-8")
    return content


def export(data: Dict[str, str], fmt: ExportFormat, output_path: Optional[Path] = None) -> str:
    """Dispatch to the correct exporter based on *fmt*."""
    if fmt == ExportFormat.ENV:
        return export_env(data, output_path)
    if fmt == ExportFormat.JSON:
        return export_json(data, output_path)
    if fmt == ExportFormat.YAML:
        return export_yaml(data, output_path)
    raise ExportError(f"Unsupported export format: {fmt}")
