"""CLI commands for exporting environment configs."""

from __future__ import annotations

from pathlib import Path

import click

from envoy.config.loader import load_config, ConfigLoadError
from envoy.export.writer import ExportFormat, ExportError, export
from envoy.targets.registry import TargetRegistry, TargetLoadError


@click.group(name="export")
def export_group() -> None:
    """Export environment configs to different file formats."""


@export_group.command(name="run")
@click.argument("target")
@click.option(
    "--format", "fmt",
    type=click.Choice([f.value for f in ExportFormat], case_sensitive=False),
    default=ExportFormat.ENV.value,
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write output to this file instead of stdout.",
)
@click.option(
    "--targets-file",
    type=click.Path(exists=True, dir_okay=False),
    default="targets.json",
    show_default=True,
    help="Path to targets registry file.",
)
def run_command(target: str, fmt: str, output: str | None, targets_file: str) -> None:
    """Export a target's environment config to ENV, JSON, or YAML."""
    try:
        registry = TargetRegistry.load(Path(targets_file))
        tgt = registry.get(target)
    except (TargetLoadError, KeyError) as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        data = load_config(tgt.resolved_path)
    except ConfigLoadError as exc:
        raise click.ClickException(str(exc)) from exc

    output_path = Path(output) if output else None

    try:
        content = export(data, ExportFormat(fmt), output_path)
    except ExportError as exc:
        raise click.ClickException(str(exc)) from exc

    if output_path is None:
        click.echo(content, nl=False)
    else:
        click.echo(f"Exported {len(data)} variable(s) to {output_path} [{fmt}]")
