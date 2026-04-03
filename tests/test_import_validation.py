"""Tests for validate_entry from import_sprint.py."""

import copy
from import_sprint import validate_entry


def _valid_entry():
    """Return a minimal valid sprint entry for testing."""
    return {
        "project": "test-project",
        "sprint": 1,
        "label": "Test S1",
        "phase": "Phase 1: Initial",
        "metrics": {
            "active_session_time_s": 1800,
            "active_session_time_display": "30m",
            "total_tokens": 500000,
            "total_tokens_display": "500k",
            "new_work_tokens": 300000,
            "new_work_tokens_display": "300k",
            "opus_pct": 80,
            "sonnet_pct": 15,
            "haiku_pct": 5,
            "subagents": 3,
            "api_calls": 150,
            "tests_total": 42,
            "tests_added": 10,
            "coverage_pct": 72.5,
            "lint_errors": 0,
            "gates_first_pass": True,
            "loc_added": 350,
        },
        "hypotheses": [],
    }


class TestValidEntryPasses:
    """A complete valid entry should produce no errors."""

    def test_valid_complete_entry(self):
        entry = _valid_entry()
        errors, warnings = validate_entry(entry)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_valid_with_null_optionals(self):
        entry = _valid_entry()
        entry["metrics"]["tests_total"] = None
        entry["metrics"]["tests_added"] = None
        entry["metrics"]["coverage_pct"] = None
        entry["metrics"]["lint_errors"] = None
        entry["metrics"]["gates_first_pass"] = None
        errors, warnings = validate_entry(entry)
        assert errors == [], f"Expected no errors, got: {errors}"


class TestMissingRequiredFields:
    """Missing required fields should produce errors."""

    def test_missing_project(self):
        entry = _valid_entry()
        del entry["project"]
        errors, _ = validate_entry(entry)
        assert any("project" in e for e in errors)

    def test_empty_project(self):
        entry = _valid_entry()
        entry["project"] = ""
        errors, _ = validate_entry(entry)
        assert any("project" in e for e in errors)

    def test_wrong_type_sprint(self):
        entry = _valid_entry()
        entry["sprint"] = "1"
        errors, _ = validate_entry(entry)
        assert any("sprint" in e for e in errors)

    def test_missing_label(self):
        entry = _valid_entry()
        entry["label"] = ""
        errors, _ = validate_entry(entry)
        assert any("label" in e for e in errors)

    def test_hypotheses_not_list(self):
        entry = _valid_entry()
        entry["hypotheses"] = "none"
        errors, _ = validate_entry(entry)
        assert any("hypotheses" in e for e in errors)


class TestOutOfRangeValues:
    """Out-of-range metrics should produce errors."""

    def test_coverage_over_100(self):
        entry = _valid_entry()
        entry["metrics"]["coverage_pct"] = 105.0
        errors, _ = validate_entry(entry)
        assert any("coverage_pct" in e for e in errors)

    def test_coverage_negative(self):
        entry = _valid_entry()
        entry["metrics"]["coverage_pct"] = -5.0
        errors, _ = validate_entry(entry)
        assert any("coverage_pct" in e for e in errors)

    def test_opus_pct_over_100(self):
        entry = _valid_entry()
        entry["metrics"]["opus_pct"] = 110
        # Also fix the sum so we isolate the range error
        entry["metrics"]["sonnet_pct"] = 0
        entry["metrics"]["haiku_pct"] = 0
        errors, _ = validate_entry(entry)
        assert any("opus_pct" in e for e in errors)

    def test_model_pct_sum_wrong(self):
        entry = _valid_entry()
        entry["metrics"]["opus_pct"] = 50
        entry["metrics"]["sonnet_pct"] = 10
        entry["metrics"]["haiku_pct"] = 5
        errors, _ = validate_entry(entry)
        assert any("percentages sum" in e for e in errors)

    def test_new_work_exceeds_total(self):
        entry = _valid_entry()
        entry["metrics"]["new_work_tokens"] = 600000
        entry["metrics"]["total_tokens"] = 500000
        errors, _ = validate_entry(entry)
        assert any("exceeds" in e for e in errors)

    def test_session_time_over_10h(self):
        entry = _valid_entry()
        entry["metrics"]["active_session_time_s"] = 40000
        errors, _ = validate_entry(entry)
        assert any("active_session_time_s" in e for e in errors)
