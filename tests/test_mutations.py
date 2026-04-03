"""Tests for mutation generators from optimize.py."""

from optimize import (
    mutate_gate_incremental_tests,
    mutate_gate_max_cycles,
    mutate_model_routing_stronger,
    mutate_scope_threshold,
)


# Sample SKILL.md fragments containing the markers each mutation targets

SKILL_WITH_GATE_MARKER = """\
## EXECUTE
- Run `/gate` after every meaningful change -- not batch-at-end
- Keep commits atomic
"""

SKILL_WITH_ROUTING_MARKER = """\
## MODEL ROUTING
This is advisory — use your judgment. When in doubt, use the default.
"""

SKILL_WITH_SCOPE_MARKER = """\
## SCOPE
If ≤5 files AND no new external dependencies: use **LIGHT MODE**.
"""

SKILL_WITH_CYCLES_MARKER = """\
## GATE
fix, re-run, max 3 cycles
"""


class TestMutateGateIncrementalTests:
    def test_applies_when_marker_present(self):
        result = mutate_gate_incremental_tests(SKILL_WITH_GATE_MARKER)
        assert result is not None
        assert "Incremental testing" in result

    def test_returns_none_when_already_applied(self):
        already = SKILL_WITH_GATE_MARKER.replace(
            "Run `/gate`",
            "**Incremental testing**: do it\n- Run `/gate`"
        )
        result = mutate_gate_incremental_tests(already)
        assert result is None

    def test_returns_none_when_marker_missing(self):
        result = mutate_gate_incremental_tests("unrelated text")
        assert result is None

    def test_no_crash_on_empty_input(self):
        result = mutate_gate_incremental_tests("")
        assert result is None


class TestMutateModelRoutingStronger:
    def test_applies_when_marker_present(self):
        result = mutate_model_routing_stronger(SKILL_WITH_ROUTING_MARKER)
        assert result is not None
        assert "Follow this routing" in result

    def test_returns_none_when_already_applied(self):
        result = mutate_model_routing_stronger("Follow this routing for subagent tasks.")
        assert result is None

    def test_no_crash_on_empty_input(self):
        result = mutate_model_routing_stronger("")
        assert result is None


class TestMutateScopeThreshold:
    def test_applies_when_marker_present(self):
        result = mutate_scope_threshold(SKILL_WITH_SCOPE_MARKER)
        assert result is not None
        assert "≤8 files" in result

    def test_returns_none_when_already_applied(self):
        already = SKILL_WITH_SCOPE_MARKER.replace("≤5 files", "≤8 files")
        result = mutate_scope_threshold(already)
        assert result is None

    def test_no_crash_on_empty_input(self):
        result = mutate_scope_threshold("")
        assert result is None


class TestMutateGateMaxCycles:
    def test_applies_when_marker_present(self):
        result = mutate_gate_max_cycles(SKILL_WITH_CYCLES_MARKER)
        assert result is not None
        assert "max 2 cycles" in result

    def test_returns_none_when_already_applied(self):
        result = mutate_gate_max_cycles("fix, re-run, max 2 cycles. If still failing")
        assert result is None

    def test_no_crash_on_empty_input(self):
        result = mutate_gate_max_cycles("")
        assert result is None
