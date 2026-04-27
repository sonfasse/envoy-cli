"""Tests for envoy.targets.registry."""

import json
import pytest
from pathlib import Path

from envoy.targets.registry import Target, TargetRegistry, TargetLoadError


# ---------------------------------------------------------------------------
# Target dataclass
# ---------------------------------------------------------------------------

class TestTarget:
    def test_basic_creation(self):
        t = Target(name="staging", config_path="envs/staging.env")
        assert t.name == "staging"
        assert t.config_path == "envs/staging.env"
        assert t.tags == []
        assert t.description is None

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            Target(name="", config_path="envs/staging.env")

    def test_empty_config_path_raises(self):
        with pytest.raises(ValueError, match="config_path"):
            Target(name="staging", config_path="")

    def test_resolved_path_absolute(self):
        t = Target(name="prod", config_path="/abs/prod.env")
        assert t.resolved_path(Path("/some/base")) == Path("/abs/prod.env")

    def test_resolved_path_relative(self):
        t = Target(name="prod", config_path="envs/prod.env")
        assert t.resolved_path(Path("/project")) == Path("/project/envs/prod.env")

    def test_resolved_path_no_base(self):
        t = Target(name="prod", config_path="envs/prod.env")
        assert t.resolved_path() == Path("envs/prod.env")


# ---------------------------------------------------------------------------
# TargetRegistry
# ---------------------------------------------------------------------------

class TestTargetRegistry:
    def _make_registry(self):
        return TargetRegistry([
            Target(name="dev", config_path="envs/dev.env"),
            Target(name="staging", config_path="envs/staging.env", tags=["staging"]),
            Target(name="production", config_path="envs/prod.env", tags=["prod"]),
        ])

    def test_names(self):
        reg = self._make_registry()
        assert set(reg.names()) == {"dev", "staging", "production"}

    def test_get_known_target(self):
        reg = self._make_registry()
        t = reg.get("staging")
        assert t.name == "staging"

    def test_get_unknown_raises(self):
        reg = self._make_registry()
        with pytest.raises(TargetLoadError, match="Unknown target"):
            reg.get("nonexistent")

    def test_duplicate_name_raises(self):
        with pytest.raises(TargetLoadError, match="Duplicate"):
            TargetRegistry([
                Target(name="dev", config_path="a.env"),
                Target(name="dev", config_path="b.env"),
            ])

    def test_all_returns_all(self):
        reg = self._make_registry()
        assert len(reg.all()) == 3


# ---------------------------------------------------------------------------
# TargetRegistry.from_file
# ---------------------------------------------------------------------------

def write_manifest(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "targets.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


class TestFromFile:
    def test_loads_valid_manifest(self, tmp_path):
        p = write_manifest(tmp_path, {
            "targets": [
                {"name": "dev", "config_path": "envs/dev.env"},
                {"name": "prod", "config_path": "envs/prod.env", "tags": ["prod"], "description": "Production"},
            ]
        })
        reg = TargetRegistry.from_file(p)
        assert set(reg.names()) == {"dev", "prod"}
        assert reg.get("prod").description == "Production"
        assert reg.get("prod").tags == ["prod"]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(TargetLoadError, match="not found"):
            TargetRegistry.from_file(tmp_path / "missing.json")

    def test_invalid_json_raises(self, tmp_path):
        p = tmp_path / "targets.json"
        p.write_text("not json", encoding="utf-8")
        with pytest.raises(TargetLoadError, match="Invalid JSON"):
            TargetRegistry.from_file(p)

    def test_missing_targets_key_raises(self, tmp_path):
        p = write_manifest(tmp_path, {"other": []})
        with pytest.raises(TargetLoadError, match="'targets' list"):
            TargetRegistry.from_file(p)

    def test_entry_missing_name_raises(self, tmp_path):
        p = write_manifest(tmp_path, {"targets": [{"config_path": "x.env"}]})
        with pytest.raises(TargetLoadError, match="missing required key"):
            TargetRegistry.from_file(p)

    def test_empty_targets_list(self, tmp_path):
        p = write_manifest(tmp_path, {"targets": []})
        reg = TargetRegistry.from_file(p)
        assert reg.names() == []
