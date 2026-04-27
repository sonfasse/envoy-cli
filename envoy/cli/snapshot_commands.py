"""CLI commands for managing environment snapshots."""

from __future__ import annotations

import click

from envoy.config.loader import load_config, ConfigLoadError
from envoy.snapshot.store import Snapshot, SnapshotStore, SnapshotError
from envoy.targets.registry import TargetRegistry, TargetLoadError

DEFAULT_STORE = ".envoy/snapshots.json"


@click.group("snapshot")
def snapshot_group() -> None:
    """Save and compare environment snapshots."""


@snapshot_group.command("save")
@click.argument("target")
@click.option("--registry", default="envoy.yaml", show_default=True, help="Target registry file.")
@click.option("--store", default=DEFAULT_STORE, show_default=True, help="Snapshot store path.")
@click.option("--label", default=None, help="Optional label for this snapshot.")
def save_command(target: str, registry: str, store: str, label: str | None) -> None:
    """Capture a snapshot of TARGET's current environment config."""
    try:
        reg = TargetRegistry.from_file(registry)
        t = reg.get(target)
    except (TargetLoadError, KeyError) as exc:
        raise click.ClickException(str(exc))

    try:
        env = load_config(t.resolved_path)
    except ConfigLoadError as exc:
        raise click.ClickException(str(exc))

    snap = Snapshot(target=target, env=env, label=label)
    try:
        SnapshotStore(store).save(snap)
    except SnapshotError as exc:
        raise click.ClickException(str(exc))

    label_info = f" [{label}]" if label else ""
    click.echo(f"Snapshot saved for '{target}'{label_info} ({len(env)} keys).")


@snapshot_group.command("list")
@click.argument("target")
@click.option("--store", default=DEFAULT_STORE, show_default=True, help="Snapshot store path.")
def list_command(target: str, store: str) -> None:
    """List saved snapshots for TARGET."""
    try:
        snaps = SnapshotStore(store).list_for_target(target)
    except SnapshotError as exc:
        raise click.ClickException(str(exc))

    if not snaps:
        click.echo(f"No snapshots found for '{target}'.")
        return

    for i, s in enumerate(snaps, 1):
        label = f"  label={s.label}" if s.label else ""
        click.echo(f"  {i:>3}. {s.created_at}  keys={len(s.env)}{label}")


@snapshot_group.command("clear")
@click.argument("target")
@click.option("--store", default=DEFAULT_STORE, show_default=True, help="Snapshot store path.")
@click.confirmation_option(prompt="This will delete all snapshots for the target. Continue?")
def clear_command(target: str, store: str) -> None:
    """Delete all snapshots for TARGET."""
    try:
        removed = SnapshotStore(store).clear_for_target(target)
    except SnapshotError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"Removed {removed} snapshot(s) for '{target}'.")
