"""Tests for envoy.export.writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.export.writer import (
    ExportFormat,
    ExportError,
    export_env,
    export_json,
    export,
)


SAMPLE: dict[str, str] = {
    "APP_ENV": "production",
    "DB_HOST": "localhost",
    "SECRET": "p@ss w0rd",
}


class TestExportEnv:
    def test_basic_key_value(self):
        result = export_env({"FOO": "bar"})
        assert "FOO=bar" in result

    def test_value_with_space_is_quoted(self):
        result = export_env({"MSG": "hello world"})
        assert 'MSG="hello world"' in result

    def test_value_with_hash_is_quoted(self):
        result = export_env({"COLOR": "#fff"})
        assert 'COLOR="#fff"' in result

    def test_keys_sorted_alphabetically(self):
        result = export_env({"ZZZ": "1", "AAA": "2"})
        lines = [l for l in result.splitlines() if "=" in l]
        assert lines[0].startswith("AAA")
        assert lines[1].startswith("ZZZ")

    def test_trailing_newline(self):
        result = export_env({"X": "y"})
        assert result.endswith("\n")

    def test_empty_dict_returns_empty_string(self):
        result = export_env({})
        assert result == ""

    def test_writes_to_file(self, tmp_path: Path):
        out = tmp_path / "out.env"
        export_env({"KEY": "val"}, output_path=out)
        assert out.exists()
        assert "KEY=val" in out.read_text()


class TestExportJson:
    def test_output_is_valid_json(self):
        result = export_json(SAMPLE)
        parsed = json.loads(result)
        assert parsed["APP_ENV"] == "production"

    def test_keys_sorted(self):
        result = export_json({"Z": "1", "A": "2"})
        parsed = json.loads(result)
        assert list(parsed.keys()) == ["A", "Z"]

    def test_writes_to_file(self, tmp_path: Path):
        out = tmp_path / "out.json"
        export_json({"K": "v"}, output_path=out)
        data = json.loads(out.read_text())
        assert data["K"] == "v"


class TestExportDispatch:
    def test_dispatch_env(self):
        result = export({"A": "1"}, ExportFormat.ENV)
        assert "A=1" in result

    def test_dispatch_json(self):
        result = export({"A": "1"}, ExportFormat.JSON)
        assert json.loads(result)["A"] == "1"

    def test_unsupported_format_raises(self):
        """Passing a raw invalid value should raise ExportError via dispatch."""
        with pytest.raises(ExportError):
            # Bypass enum validation to hit the fallback branch
            export({}, "xml")  # type: ignore[arg-type]
