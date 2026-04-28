"""CLI commands for viewing the envoy audit log."""

import click
from pathlib import Path

from envoy.audit.log import AuditLog


DEFAULT_LOG_PATH = Path.home() / ".envoy" / "audit.log"


@click.group("audit")
def audit_group() -> None:
    """View and manage the envoy audit log."""


@audit_group.command("list")
@click.option("--log", default=str(DEFAULT_LOG_PATH), show_default=True, help="Path to audit log file.")
@click.option("--event", default=None, help="Filter by event type (diff, snapshot_save, etc.).")
@click.option("--limit", default=20, show_default=True, help="Maximum number of entries to show.")
def list_command(log: str, event: str, limit: int) -> None:
    """List recent audit log entries."""
    audit = AuditLog(Path(log))
    entries = audit.read_all()

    if event:
        entries = [e for e in entries if e.event.value == event]

    entries = entries[-limit:]

    if not entries:
        click.echo("No audit log entries found.")
        return

    for entry in entries:
        detail_str = f" — {entry.details}" if entry.details else ""
        click.echo(f"[{entry.timestamp}] {entry.event.value:<20} target={entry.target}{detail_str}")


@audit_group.command("clear")
@click.option("--log", default=str(DEFAULT_LOG_PATH), show_default=True, help="Path to audit log file.")
@click.confirmation_option(prompt="Are you sure you want to clear the audit log?")
def clear_command(log: str) -> None:
    """Clear all audit log entries."""
    audit = AuditLog(Path(log))
    audit.clear()
    click.echo("Audit log cleared.")
