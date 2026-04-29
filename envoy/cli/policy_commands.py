"""CLI commands for running and displaying audit policy checks."""

import click
from pathlib import Path
from envoy.audit.log import AuditLog
from envoy.audit.policy import evaluate_policy, DEFAULT_RULES


@click.group(name="policy")
def policy_group():
    """Evaluate audit logs against policy rules."""


@policy_group.command(name="check")
@click.option(
    "--audit-log",
    "audit_log_path",
    default=".envoy_audit.jsonl",
    show_default=True,
    help="Path to the audit log file.",
)
@click.option(
    "--min-severity",
    type=click.Choice(["info", "warn", "critical"], case_sensitive=False),
    default="info",
    show_default=True,
    help="Minimum severity level to display.",
)
@click.pass_context
def check_command(ctx: click.Context, audit_log_path: str, min_severity: str):
    """Check audit log entries against built-in policy rules."""
    severity_order = {"info": 0, "warn": 1, "critical": 2}
    min_level = severity_order[min_severity.lower()]

    log_file = Path(audit_log_path)
    if not log_file.exists():
        click.echo("No audit log found. Nothing to check.")
        return

    audit = AuditLog(log_file)
    entries = audit.read_all()

    if not entries:
        click.echo("Audit log is empty. No violations.")
        return

    violations = evaluate_policy(entries, rules=DEFAULT_RULES)
    filtered = [
        v for v in violations
        if severity_order.get(v.severity, 0) >= min_level
    ]

    if not filtered:
        click.echo(f"No policy violations at or above '{min_severity}' severity.")
        return

    click.echo(f"Found {len(filtered)} policy violation(s):\n")
    for v in filtered:
        ts = v.entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        severity_label = v.severity.upper().ljust(8)
        click.echo(f"  [{severity_label}] {ts}  {v.description}")
        if v.entry.metadata:
            for k, val in v.entry.metadata.items():
                click.echo(f"             {k}: {val}")

    critical_count = sum(1 for v in filtered if v.severity == "critical")
    if critical_count:
        ctx.exit(2)
