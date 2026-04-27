"""CLI commands for diffing snapshots."""

from __future__ import annotations

import click
from pathlib import Path

from envoy.snapshot.store import SnapshotStore
from envoy.snapshot.diff import SnapshotDiffError, diff_snapshots
from envoy.diff.formatter import OutputFormat, format_diff


DEFAULT_STORE = Path.home() / ".envoy" / "snapshots.json"


@click.group(name="snapshot-diff")
def snapshot_diff_group() -> None:
    """Commands for comparing stored snapshots."""


@snapshot_diff_group.command(name="compare")
@click.argument("label_a")
@click.argument("label_b")
@click.option(
    "--store",
    "store_path",
    default=str(DEFAULT_STORE),
    show_default=True,
    help="Path to snapshot store file.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=OutputFormat.PLAIN.value,
    show_default=True,
    help="Output format.",
)
@click.option(
    "--all",
    "include_unchanged",
    is_flag=True,
    default=False,
    help="Include unchanged keys in output.",
)
def compare_command(
    label_a: str,
    label_b: str,
    store_path: str,
    output_format: str,
    include_unchanged: bool,
) -> None:
    """Compare two snapshots by label and display the diff."""
    store = SnapshotStore(Path(store_path))
    fmt = OutputFormat(output_format)

    try:
        result = diff_snapshots(
            store, label_a, label_b, include_unchanged=include_unchanged
        )
    except SnapshotDiffError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.entries:
        click.echo("No differences found.")
        return

    click.echo(format_diff(result, fmt))
