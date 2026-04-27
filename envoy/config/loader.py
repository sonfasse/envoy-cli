"""Environment config loader supporting .env and JSON formats."""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class ConfigLoadError(Exception):
    """Raised when a config file cannot be loaded or parsed."""


def load_env_file(path: str) -> Dict[str, str]:
    """Parse a .env file into a key-value dictionary.

    Supports:
    - KEY=VALUE pairs
    - Quoted values (single or double)
    - Inline comments after a '#'
    - Blank lines and full-line comments are ignored
    """
    config: Dict[str, str] = {}
    file_path = Path(path)

    if not file_path.exists():
        raise ConfigLoadError(f"File not found: {path}")

    with file_path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ConfigLoadError(
                    f"Invalid syntax at line {lineno} in {path}: '{line}'"
                )
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip inline comments
            if " #" in value:
                value = value[: value.index(" #")].strip()
            # Strip surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            config[key] = value

    return config


def load_json_file(path: str) -> Dict[str, str]:
    """Load environment variables from a JSON file (flat key-value object)."""
    file_path = Path(path)

    if not file_path.exists():
        raise ConfigLoadError(f"File not found: {path}")

    with file_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ConfigLoadError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigLoadError(f"Expected a JSON object at the top level in {path}")

    return {str(k): str(v) for k, v in data.items()}


def load_config(path: str) -> Dict[str, str]:
    """Auto-detect file format and load environment variables."""
    ext = Path(path).suffix.lower()
    if ext == ".json":
        return load_json_file(path)
    # Default: treat as .env
    return load_env_file(path)
