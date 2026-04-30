"""CLI commands for validating environment config targets."""

import sys
from typing import Optional

import click

from envoy.targets.registry import TargetRegistry, TargetLoadError
from envoy.validate.checker import validate_all_targets, validate_target, ValidationError


@click.group(name="validate")
def validate_group():
    """Validate environment config targets against rules."""


@validate_group.command(name="check")
@click.option("--targets", "targets_file", default="targets.json", show_default=True,
              help="Path to targets registry file.")
@click.option("--require", "required_keys", multiple=True, metavar="KEY",
              help="Keys that must be present and non-empty.")
@click.option("--schema", "schema_keys", multiple=True, metavar="KEY",
              help="Allowed keys; extras are flagged as unknown.")
@click.option("--target", "target_name", default=None,
              help="Validate a single named target only.")
@click.option("--strict", is_flag=True, default=False,
              help="Exit non-zero if any unknown keys are found.")
def check_command(
    targets_file: str,
    required_keys: tuple,
    schema_keys: tuple,
    target_name: Optional[str],
    strict: bool,
):
    """Check targets for missing, empty, or unknown keys."""
    try:
        registry = TargetRegistry.from_file(targets_file)
    except (TargetLoadError, FileNotFoundError) as exc:
        click.echo(f"Error loading targets: {exc}", err=True)
        sys.exit(1)

    if target_name:
        target = registry.get(target_name)
        if target is None:
            click.echo(f"Unknown target: '{target_name}'", err=True)
            sys.exit(1)
        targets = [target]
    else:
        targets = registry.all()

    req = list(required_keys) or None
    schema = list(schema_keys) or None

    try:
        results = validate_all_targets(targets, required_keys=req, schema_keys=schema)
    except ValidationError as exc:
        click.echo(f"Validation error: {exc}", err=True)
        sys.exit(1)

    all_valid = True
    for result in results:
        click.echo(result.summary())
        if not result.is_valid:
            all_valid = False
        if strict and result.unknown_keys:
            all_valid = False

    if not all_valid:
        sys.exit(1)
