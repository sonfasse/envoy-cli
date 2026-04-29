"""Policy engine for flagging audit events based on configurable rules."""

from dataclasses import dataclass, field
from typing import List, Optional
from envoy.audit.log import AuditEntry, AuditEvent


@dataclass
class PolicyRule:
    """A single rule that matches audit entries and assigns a severity."""
    event: AuditEvent
    severity: str  # 'info', 'warn', 'critical'
    description: str
    key_pattern: Optional[str] = None  # substring match on key, if relevant

    def matches(self, entry: AuditEntry) -> bool:
        if entry.event != self.event:
            return False
        if self.key_pattern is not None:
            key = entry.metadata.get("key", "")
            if self.key_pattern.lower() not in key.lower():
                return False
        return True


@dataclass
class PolicyViolation:
    entry: AuditEntry
    rule: PolicyRule

    @property
    def severity(self) -> str:
        return self.rule.severity

    @property
    def description(self) -> str:
        return self.rule.description


# Default built-in policy rules
DEFAULT_RULES: List[PolicyRule] = [
    PolicyRule(
        event=AuditEvent.SNAPSHOT_CLEARED,
        severity="warn",
        description="Snapshot store was cleared",
    ),
    PolicyRule(
        event=AuditEvent.DIFF_RUN,
        severity="info",
        description="Diff was executed between targets",
    ),
    PolicyRule(
        event=AuditEvent.SNAPSHOT_SAVED,
        severity="info",
        description="Snapshot was saved",
        key_pattern=None,
    ),
]


def evaluate_policy(
    entries: List[AuditEntry],
    rules: Optional[List[PolicyRule]] = None,
) -> List[PolicyViolation]:
    """Return a list of violations for all matching (entry, rule) pairs."""
    active_rules = rules if rules is not None else DEFAULT_RULES
    violations: List[PolicyViolation] = []
    for entry in entries:
        for rule in active_rules:
            if rule.matches(entry):
                violations.append(PolicyViolation(entry=entry, rule=rule))
    return violations
