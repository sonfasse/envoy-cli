"""Tests for envoy.export.merger module."""

import os
import pytest

from envoy.export.merger import merge_targets, MergeError, MergeResult
from envoy.targets.registry import Target


def make_target(tmp_path, name: str, content: str) -> Target:
    cfg_file = tmp_path / f"{name}.env"
    cfg_file.write_text(content)
    return Target(name=name, config_path=str(cfg_file))


def test_merge_single_target(tmp_path):
    t = make_target(tmp_path, "prod", "KEY=value\nFOO=bar\n")
    result = merge_targets([t])
    assert result.values == {"KEY": "value", "FOO": "bar"}
    assert result.merged_targets == ["prod"]
    assert not result.has_conflicts()


def test_merge_two_targets_no_conflict(tmp_path):
    t1 = make_target(tmp_path, "base", "A=1\nB=2\n")
    t2 = make_target(tmp_path, "override", "C=3\nD=4\n")
    result = merge_targets([t1, t2])
    assert result.values == {"A": "1", "B": "2", "C": "3", "D": "4"}
    assert not result.has_conflicts()


def test_merge_conflict_detected(tmp_path):
    t1 = make_target(tmp_path, "staging", "KEY=staging_val\n")
    t2 = make_target(tmp_path, "prod", "KEY=prod_val\n")
    result = merge_targets([t1, t2])
    assert result.has_conflicts()
    assert "KEY" in result.conflicts


def test_merge_override_order_respected(tmp_path):
    t1 = make_target(tmp_path, "base", "KEY=first\n")
    t2 = make_target(tmp_path, "override", "KEY=second\n")
    result = merge_targets([t1, t2], override_order=True)
    assert result.values["KEY"] == "second"


def test_merge_no_override_keeps_first(tmp_path):
    t1 = make_target(tmp_path, "base", "KEY=first\n")
    t2 = make_target(tmp_path, "override", "KEY=second\n")
    result = merge_targets([t1, t2], override_order=False)
    assert result.values["KEY"] == "first"


def test_base_target_merged_first(tmp_path):
    t1 = make_target(tmp_path, "extra", "KEY=extra\n")
    t2 = make_target(tmp_path, "base", "KEY=base\n")
    result = merge_targets([t1, t2], base_target=t2, override_order=True)
    # extra comes after base, so extra wins
    assert result.values["KEY"] == "extra"
    assert result.base_target == "base"


def test_origins_tracked_per_key(tmp_path):
    t1 = make_target(tmp_path, "a", "X=1\n")
    t2 = make_target(tmp_path, "b", "X=2\nY=3\n")
    result = merge_targets([t1, t2])
    assert ("a", "1") in result.origins["X"]
    assert ("b", "2") in result.origins["X"]
    assert result.origins["Y"] == [("b", "3")]


def test_conflict_summary_format(tmp_path):
    t1 = make_target(tmp_path, "dev", "PORT=3000\n")
    t2 = make_target(tmp_path, "prod", "PORT=8080\n")
    result = merge_targets([t1, t2])
    summary = result.conflict_summary()
    assert len(summary) == 1
    assert "PORT" in summary[0]
    assert "dev" in summary[0]
    assert "prod" in summary[0]


def test_empty_targets_raises(tmp_path):
    with pytest.raises(MergeError, match="At least one target"):
        merge_targets([])


def test_missing_config_file_raises(tmp_path):
    t = Target(name="ghost", config_path=str(tmp_path / "nonexistent.env"))
    with pytest.raises(MergeError, match="ghost"):
        merge_targets([t])
