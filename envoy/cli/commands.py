"""CLI command definitions for envoy-cli."""

import sys
from pathlib import Path

import click

from envoy.config.loader import load_config, ConfigLoadError
from envoy.diff.engine import compute_diff
from envoy.diff.formatter import format_diff, OutputFormat
from envoy.targets.registry import TargetRegistry, TargetLoadError


@click.group()
@click.version_option(version="0.1.0", prog_name="envoy")
def cli() -> None:
    """envoy — manage and diff environment variable configs across deployment targets."""


@cli.command("diff")
@click.argument("source")
@click.argument("target")
@click.option(
    "--registry",
    "registry_path",
    default="targets.json",
    show_default=True,
    help="Path to the targets registry JSON file.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=OutputFormat.PLAIN.value,
    show_default=True,
    help="Output format for the diff.",
)
@click.option(
    "--show-unchanged",
    is_flag=True,
    default=False,
    help="Include unchanged keys in the output.",
)
def diff_command(
    source: str,
    target: str,
    registry_path: str,
    output_format: str,
    show_unchanged: bool,
) -> None:
    """Diff environment configs between SOURCE and TARGET deployment targets."""
    try:
        registry = TargetRegistry.from_file(Path(registry_path))
    except (TargetLoadError, FileNotFoundError) as exc:
        click.echo(f"Error loading registry: {exc}", err=True)
        sys.exit(1)

    try:
        src_target = registry.get(source)
        tgt_target = registry.get(target)
    except KeyError as exc:
        click.echo(f"Unknown target: {exc}", err=True)
        sys.exit(1)

    try:
        src_config = load_config(src_target.resolved_path)
        tgt_config = load_config(tgt_target.resolved_path)
    except ConfigLoadError as exc:
        click.echo(f"Error loading config: {exc}", err=True)
        sys.exit(1)

    fmt = OutputFormat(output_format)
    result = compute_diff(src_config, tgt_config, include_unchanged=show_unchanged)
    output = format_diff(result, fmt)

    if output:
        click.echo(output)
    else:
        click.echo("No differences found.")


@cli.command("list")
@click.option(
    "--registry",
    "registry_path",
    default="targets.json",
    show_default=True,
    help="Path to the targets registry JSON file.",
)
def list_command(registry_path: str) -> None:
    """List all registered deployment targets."""
    try:
        registry = TargetRegistry.from_file(Path(registry_path))
    except (TargetLoadError, FileNotFoundError) as exc:
        click.echo(f"Error loading registry: {exc}", err=True)
        sys.exit(1)

    targets = registry.all()
    if not targets:
        click.echo("No targets registered.")
        return

    for t in targets:
        click.echo(f"  {t.name:<20} {t.config_path}")
