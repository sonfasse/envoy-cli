"""Tests for envoy.audit.reporter."""

from __future__ import annotations

import json
import pathlib
import pytest

from envoy.audit.log import AuditLog, AuditEntry
from envoy.audit.reporter import build_report, AuditReport


@pytest.fixture()
def log_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture()
def audit(log_path: pathlib.Path) -> AuditLog:
    return AuditLog(log_path)


def _record(audit: AuditLog, event: str, target: str) -> None:
    audit.record(event=event, target=target, detail={})


def test_empty_log_returns_zero_totals(audit: AuditLog) -> None:
    report = build_report(audit)
    assert report.total_events == 0
    assert report.by_event == {}
    assert report.by_target == {}
    assert report.recent == []


def test_total_events_counted(audit: AuditLog) -> None:
    _record(audit, "diff", "staging")
    _record(audit, "diff", "production")
    _record(audit, "snapshot.save", "staging")
    report = build_report(audit)
    assert report.total_events == 3


def test_by_event_counts(audit: AuditLog) -> None:
    _record(audit, "diff", "staging")
    _record(audit, "diff", "staging")
    _record(audit, "snapshot.save", "staging")
    report = build_report(audit)
    assert report.by_event["diff"] == 2
    assert report.by_event["snapshot.save"] == 1


def test_by_target_counts(audit: AuditLog) -> None:
    _record(audit, "diff", "staging")
    _record(audit, "diff", "production")
    _record(audit, "diff", "staging")
    report = build_report(audit)
    assert report.by_target["staging"] == 2
    assert report.by_target["production"] == 1


def test_recent_defaults_to_last_five(audit: AuditLog) -> None:
    for i in range(8):
        _record(audit, "diff", f"target-{i}")
    report = build_report(audit)
    assert len(report.recent) == 5
    assert report.recent[-1].target == "target-7"


def test_recent_n_respected(audit: AuditLog) -> None:
    for i in range(4):
        _record(audit, "diff", f"t{i}")
    report = build_report(audit, recent_n=2)
    assert len(report.recent) == 2


def test_summary_lines_contains_totals(audit: AuditLog) -> None:
    _record(audit, "diff", "staging")
    report = build_report(audit)
    lines = report.summary_lines()
    joined = "\n".join(lines)
    assert "Total events" in joined
    assert "diff" in joined
    assert "staging" in joined
