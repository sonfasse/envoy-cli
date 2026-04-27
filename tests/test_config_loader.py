"""Tests for envoy.config.loader module."""

import json
import pytest
from pathlib import Path

from envoy.config.loader import (
    ConfigLoadError,
    load_config,
    load_env_file,
    load_json_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_file(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------

class TestLoadEnvFile:
    def test_basic_key_value(self, tmp_path):
        path = write_file(tmp_path, ".env", "KEY=value\nFOO=bar\n")
        assert load_env_file(path) == {"KEY": "value", "FOO": "bar"}

    def test_quoted_values(self, tmp_path):
        path = write_file(tmp_path, ".env", 'A="hello world"\nB=\'single\'\n')
        result = load_env_file(path)
        assert result["A"] == "hello world"
        assert result["B"] == "single"

    def test_inline_comment_stripped(self, tmp_path):
        path = write_file(tmp_path, ".env", "PORT=8080 # web server port\n")
        assert load_env_file(path)["PORT"] == "8080"

    def test_blank_lines_and_comments_ignored(self, tmp_path):
        content = "\n# This is a comment\nKEY=value\n"
        path = write_file(tmp_path, ".env", content)
        assert load_env_file(path) == {"KEY": "value"}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ConfigLoadError, match="File not found"):
            load_env_file(str(tmp_path / "nonexistent.env"))

    def test_invalid_syntax_raises(self, tmp_path):
        path = write_file(tmp_path, ".env", "BADLINE\n")
        with pytest.raises(ConfigLoadError, match="Invalid syntax"):
            load_env_file(path)


# ---------------------------------------------------------------------------
# JSON loader
# ---------------------------------------------------------------------------

class TestLoadJsonFile:
    def test_basic_json(self, tmp_path):
        data = {"DB_HOST": "localhost", "DB_PORT": "5432"}
        path = write_file(tmp_path, "config.json", json.dumps(data))
        assert load_json_file(path) == data

    def test_numeric_values_cast_to_str(self, tmp_path):
        path = write_file(tmp_path, "config.json", json.dumps({"PORT": 3000}))
        assert load_json_file(path)["PORT"] == "3000"

    def test_invalid_json_raises(self, tmp_path):
        path = write_file(tmp_path, "bad.json", "{not valid json")
        with pytest.raises(ConfigLoadError, match="Invalid JSON"):
            load_json_file(path)

    def test_non_object_raises(self, tmp_path):
        path = write_file(tmp_path, "list.json", json.dumps(["a", "b"]))
        with pytest.raises(ConfigLoadError, match="Expected a JSON object"):
            load_json_file(path)


# ---------------------------------------------------------------------------
# Auto-detect loader
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_dispatches_json(self, tmp_path):
        path = write_file(tmp_path, "vars.json", json.dumps({"X": "1"}))
        assert load_config(path) == {"X": "1"}

    def test_dispatches_env(self, tmp_path):
        path = write_file(tmp_path, "vars.env", "X=1\n")
        assert load_config(path) == {"X": "1"}
