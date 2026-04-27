"""Tests for the diff engine module."""

import pytest
from envoy.diff.engine import DiffStatus, diff_configs


BASE = {
    "APP_NAME": "myapp",
    "DEBUG": "false",
    "DATABASE_URL": "postgres://localhost/dev",
    "SECRET_KEY": "dev-secret",
}

TARGET = {
    "APP_NAME": "myapp",
    "DEBUG": "true",
    "DATABASE_URL": "postgres://prod-host/prod",
    "NEW_RELIC_KEY": "abc123",
}


def test_changed_keys_detected():
    result = diff_configs(BASE, TARGET)
    changed_keys = {e.key for e in result.changed}
    assert "DEBUG" in changed_keys
    assert "DATABASE_URL" in changed_keys


def test_added_keys_detected():
    result = diff_configs(BASE, TARGET)
    added_keys = {e.key for e in result.added}
    assert "NEW_RELIC_KEY" in added_keys


def test_removed_keys_detected():
    result = diff_configs(BASE, TARGET)
    removed_keys = {e.key for e in result.removed}
    assert "SECRET_KEY" in removed_keys


def test_unchanged_excluded_by_default():
    result = diff_configs(BASE, TARGET)
    assert result.unchanged == []


def test_unchanged_included_when_requested():
    result = diff_configs(BASE, TARGET, include_unchanged=True)
    unchanged_keys = {e.key for e in result.unchanged}
    assert "APP_NAME" in unchanged_keys


def test_has_differences_true():
    result = diff_configs(BASE, TARGET)
    assert result.has_differences is True


def test_has_differences_false_for_identical():
    result = diff_configs(BASE, BASE)
    assert result.has_differences is False


def test_diff_result_names():
    result = diff_configs(BASE, TARGET, base_name="staging", target_name="production")
    assert result.base_name == "staging"
    assert result.target_name == "production"


def test_sensitive_key_detection():
    result = diff_configs(BASE, TARGET)
    removed = {e.key: e for e in result.removed}
    assert removed["SECRET_KEY"].is_sensitive is True


def test_non_sensitive_key():
    result = diff_configs(BASE, TARGET)
    changed = {e.key: e for e in result.changed}
    assert changed["DEBUG"].is_sensitive is False


def test_empty_configs():
    result = diff_configs({}, {})
    assert result.entries == []
    assert result.has_differences is False


def test_base_values_preserved_on_changed_entry():
    result = diff_configs(BASE, TARGET)
    changed = {e.key: e for e in result.changed}
    assert changed["DEBUG"].base_value == "false"
    assert changed["DEBUG"].target_value == "true"
