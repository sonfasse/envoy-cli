"""Tests for the audit log module."""

import json
import pytest
from pathlib import Path

from envoy.audit.log import AuditEntry, AuditEvent, AuditLog


@pytest.fixture
def log_path(tmp_path: Path) -> Path:
    return tmp_path / "audit.log"


@pytest.fixture
def audit(log_path: Path) -> AuditLog:
    return AuditLog(log_path)


def make_entry(event: AuditEvent = AuditEvent.DIFF, target: str = "staging", details: str = None) -> AuditEntry:
    return AuditEntry(event=event, target=target, details=details)


def test_record_creates_file(audit: AuditLog, log_path: Path) -> None:
    audit.record(make_entry())
    assert log_path.exists()


def test_record_appends_json_lines(audit: AuditLog, log_path: Path) -> None:
    audit.record(make_entry(target="staging"))
    audit.record(make_entry(target="production"))
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 2
    data = json.loads(lines[1])
    assert data["target"] == "production"


def test_read_all_returns_entries(audit: AuditLog) -> None:
    audit.record(make_entry(event=AuditEvent.SNAPSHOT_SAVE, target="dev"))
    entries = audit.read_all()
    assert len(entries) == 1
    assert entries[0].event == AuditEvent.SNAPSHOT_SAVE
    assert entries[0].target == "dev"


def test_read_all_empty_when_no_file(audit: AuditLog) -> None:
    assert audit.read_all() == []


def test_entry_details_preserved(audit: AuditLog) -> None:
    audit.record(make_entry(details="3 changes detected"))
    entries = audit.read_all()
    assert entries[0].details == "3 changes detected"


def test_clear_removes_log(audit: AuditLog, log_path: Path) -> None:
    audit.record(make_entry())
    assert log_path.exists()
    audit.clear()
    assert not log_path.exists()


def test_clear_noop_when_no_file(audit: AuditLog) -> None:
    audit.clear()  # should not raise


def test_roundtrip_all_event_types(audit: AuditLog) -> None:
    for event in AuditEvent:
        audit.record(make_entry(event=event))
    entries = audit.read_all()
    recorded_events = {e.event for e in entries}
    assert recorded_events == set(AuditEvent)


def test_entry_timestamp_present(audit: AuditLog) -> None:
    audit.record(make_entry())
    entry = audit.read_all()[0]
    assert "T" in entry.timestamp  # ISO 8601 format


def test_multiple_records_order_preserved(audit: AuditLog) -> None:
    targets = ["alpha", "beta", "gamma"]
    for t in targets:
        audit.record(make_entry(target=t))
    entries = audit.read_all()
    assert [e.target for e in entries] == targets
