"""Audit report generation: summarize audit log entries by event type and target."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict

from envoy.audit.log import AuditEntry, AuditLog


@dataclass
class AuditReport:
    total_events: int = 0
    by_event: Dict[str, int] = field(default_factory=dict)
    by_target: Dict[str, int] = field(default_factory=dict)
    recent: List[AuditEntry] = field(default_factory=list)

    def summary_lines(self) -> List[str]:
        lines = [
            f"Total events : {self.total_events}",
            "",
            "By event type:",
        ]
        for event, count in sorted(self.by_event.items()):
            lines.append(f"  {event:<20} {count}")
        lines.append("")
        lines.append("By target:")
        for target, count in sorted(self.by_target.items()):
            lines.append(f"  {target:<20} {count}")
        if self.recent:
            lines.append("")
            lines.append(f"Last {len(self.recent)} events:")
            for entry in self.recent:
                ts = entry.timestamp[:19].replace("T", " ")
                lines.append(f"  [{ts}] {entry.event:<16} target={entry.target}")
        return lines


def build_report(log: AuditLog, recent_n: int = 5) -> AuditReport:
    """Build an AuditReport from all entries in *log*."""
    entries = log.load()

    event_counter: Counter = Counter()
    target_counter: Counter = Counter()

    for entry in entries:
        event_counter[entry.event] += 1
        target_counter[entry.target] += 1

    recent = entries[-recent_n:] if entries else []

    return AuditReport(
        total_events=len(entries),
        by_event=dict(event_counter),
        by_target=dict(target_counter),
        recent=recent,
    )
