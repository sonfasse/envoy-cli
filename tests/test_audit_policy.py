"""Tests for envoy.audit.policy."""

from datetime import datetime, timezone
from envoy.audit.log import AuditEntry, AuditEvent
from envoy.audit.policy import (
    PolicyRule,
    PolicyViolation,
    evaluate_policy,
    DEFAULT_RULES,
)


def make_entry(event: AuditEvent, metadata: dict | None = None) -> AuditEntry:
    return AuditEntry(
        event=event,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        metadata=metadata or {},
    )


def test_diff_run_triggers_info_rule():
    entries = [make_entry(AuditEvent.DIFF_RUN)]
    violations = evaluate_policy(entries)
    assert any(v.severity == "info" for v in violations)


def test_snapshot_cleared_triggers_warn():
    entries = [make_entry(AuditEvent.SNAPSHOT_CLEARED)]
    violations = evaluate_policy(entries)
    severities = [v.severity for v in violations]
    assert "warn" in severities


def test_no_violations_for_empty_entries():
    assert evaluate_policy([]) == []


def test_custom_rule_overrides_defaults():
    custom_rule = PolicyRule(
        event=AuditEvent.DIFF_RUN,
        severity="critical",
        description="Custom: diff is critical",
    )
    entries = [make_entry(AuditEvent.DIFF_RUN)]
    violations = evaluate_policy(entries, rules=[custom_rule])
    assert len(violations) == 1
    assert violations[0].severity == "critical"
    assert violations[0].description == "Custom: diff is critical"


def test_key_pattern_filters_correctly():
    rule = PolicyRule(
        event=AuditEvent.SNAPSHOT_SAVED,
        severity="warn",
        description="Sensitive key snapshot",
        key_pattern="secret",
    )
    entry_match = make_entry(AuditEvent.SNAPSHOT_SAVED, {"key": "SECRET_TOKEN"})
    entry_no_match = make_entry(AuditEvent.SNAPSHOT_SAVED, {"key": "DATABASE_URL"})

    violations = evaluate_policy([entry_match, entry_no_match], rules=[rule])
    assert len(violations) == 1
    assert violations[0].entry is entry_match


def test_violation_exposes_entry_and_rule():
    entries = [make_entry(AuditEvent.SNAPSHOT_CLEARED)]
    violations = evaluate_policy(entries)
    v = next(v for v in violations if v.severity == "warn")
    assert v.entry.event == AuditEvent.SNAPSHOT_CLEARED
    assert isinstance(v.rule, PolicyRule)


def test_multiple_rules_can_match_same_entry():
    rule_a = PolicyRule(event=AuditEvent.DIFF_RUN, severity="info", description="A")
    rule_b = PolicyRule(event=AuditEvent.DIFF_RUN, severity="warn", description="B")
    entries = [make_entry(AuditEvent.DIFF_RUN)]
    violations = evaluate_policy(entries, rules=[rule_a, rule_b])
    assert len(violations) == 2


def test_default_rules_are_nonempty():
    assert len(DEFAULT_RULES) > 0
