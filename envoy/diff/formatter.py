"""Formatters for rendering diff results to the terminal."""

from enum import Enum
from typing import List

from envoy.diff.engine import DiffEntry, DiffResult, DiffStatus

SENSITIVE_PLACEHOLDER = "***"


class OutputFormat(str, Enum):
    TABLE = "table"
    PLAIN = "plain"


def _mask(value: str, sensitive: bool) -> str:
    return SENSITIVE_PLACEHOLDER if sensitive else value


def _status_symbol(status: DiffStatus) -> str:
    symbols = {
        DiffStatus.ADDED: "+",
        DiffStatus.REMOVED: "-",
        DiffStatus.CHANGED: "~",
        DiffStatus.UNCHANGED: " ",
    }
    return symbols[status]


def _status_color(status: DiffStatus) -> str:
    colors = {
        DiffStatus.ADDED: "\033[32m",
        DiffStatus.REMOVED: "\033[31m",
        DiffStatus.CHANGED: "\033[33m",
        DiffStatus.UNCHANGED: "",
    }
    return colors[status]


RESET = "\033[0m"


def format_plain(entries: List[DiffEntry], color: bool = True) -> str:
    lines = []
    for entry in entries:
        symbol = _status_symbol(entry.status)
        base = _mask(entry.base_value or "", entry.sensitive)
        target = _mask(entry.target_value or "", entry.sensitive)

        if entry.status == DiffStatus.CHANGED:
            line = f"{symbol} {entry.key}: {base} -> {target}"
        elif entry.status == DiffStatus.ADDED:
            line = f"{symbol} {entry.key}={target}"
        elif entry.status == DiffStatus.REMOVED:
            line = f"{symbol} {entry.key}={base}"
        else:
            line = f"{symbol} {entry.key}={base}"

        if color and entry.status != DiffStatus.UNCHANGED:
            line = f"{_status_color(entry.status)}{line}{RESET}"

        lines.append(line)
    return "\n".join(lines)


def format_table(entries: List[DiffEntry], color: bool = True) -> str:
    header = f"{'KEY':<30} {'STATUS':<10} {'BASE':<20} {'TARGET':<20}"
    separator = "-" * len(header)
    lines = [header, separator]

    for entry in entries:
        base = _mask(entry.base_value or "", entry.sensitive)
        target = _mask(entry.target_value or "", entry.sensitive)
        row = f"{entry.key:<30} {entry.status.value:<10} {base:<20} {target:<20}"

        if color and entry.status != DiffStatus.UNCHANGED:
            row = f"{_status_color(entry.status)}{row}{RESET}"

        lines.append(row)
    return "\n".join(lines)


def render(result: DiffResult, fmt: OutputFormat = OutputFormat.PLAIN, color: bool = True) -> str:
    entries = result.entries
    if fmt == OutputFormat.TABLE:
        return format_table(entries, color=color)
    return format_plain(entries, color=color)
