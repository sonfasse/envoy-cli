"""Tests for envoy.diff.formatter."""

import pytest

from envoy.diff.engine import DiffEntry, DiffResult, DiffStatus
from envoy.diff.formatter import (
    OutputFormat,
    SENSITIVE_PLACEHOLDER,
    format_plain,
    format_table,
    render,
)


def make_entry(key, status, base=None, target=None, sensitive=False):
    return DiffEntry(key=key, status=status, base_value=base, target_value=target, sensitive=sensitive)


def make_result(*entries):
    return DiffResult(entries=list(entries))


class TestFormatPlain:
    def test_added_entry(self):
        entry = make_entry("NEW_KEY", DiffStatus.ADDED, target="hello")
        output = format_plain([entry], color=False)
        assert "+ NEW_KEY=hello" in output

    def test_removed_entry(self):
        entry = make_entry("OLD_KEY", DiffStatus.REMOVED, base="bye")
        output = format_plain([entry], color=False)
        assert "- OLD_KEY=bye" in output

    def test_changed_entry_shows_arrow(self):
        entry = make_entry("KEY", DiffStatus.CHANGED, base="old", target="new")
        output = format_plain([entry], color=False)
        assert "~ KEY: old -> new" in output

    def test_unchanged_entry(self):
        entry = make_entry("STABLE", DiffStatus.UNCHANGED, base="same", target="same")
        output = format_plain([entry], color=False)
        assert "  STABLE=same" in output

    def test_sensitive_value_masked(self):
        entry = make_entry("SECRET", DiffStatus.CHANGED, base="abc", target="xyz", sensitive=True)
        output = format_plain([entry], color=False)
        assert "abc" not in output
        assert "xyz" not in output
        assert SENSITIVE_PLACEHOLDER in output

    def test_color_applied_for_added(self):
        entry = make_entry("X", DiffStatus.ADDED, target="1")
        output = format_plain([entry], color=True)
        assert "\033[32m" in output

    def test_no_color_when_disabled(self):
        entry = make_entry("X", DiffStatus.ADDED, target="1")
        output = format_plain([entry], color=False)
        assert "\033[" not in output


class TestFormatTable:
    def test_header_present(self):
        output = format_table([], color=False)
        assert "KEY" in output
        assert "STATUS" in output
        assert "BASE" in output
        assert "TARGET" in output

    def test_entry_appears_in_table(self):
        entry = make_entry("DB_HOST", DiffStatus.CHANGED, base="localhost", target="prod-db")
        output = format_table([entry], color=False)
        assert "DB_HOST" in output
        assert "changed" in output
        assert "localhost" in output
        assert "prod-db" in output

    def test_sensitive_masked_in_table(self):
        entry = make_entry("DB_PASS", DiffStatus.ADDED, target="secret", sensitive=True)
        output = format_table([entry], color=False)
        assert "secret" not in output
        assert SENSITIVE_PLACEHOLDER in output


class TestRender:
    def test_render_plain_format(self):
        result = make_result(make_entry("A", DiffStatus.ADDED, target="1"))
        output = render(result, fmt=OutputFormat.PLAIN, color=False)
        assert "+ A=1" in output

    def test_render_table_format(self):
        result = make_result(make_entry("B", DiffStatus.REMOVED, base="2"))
        output = render(result, fmt=OutputFormat.TABLE, color=False)
        assert "KEY" in output
        assert "B" in output
