#!/usr/bin/env python3
"""Automated test suite for the Flowstate sprint data pipeline.

Tests the three trust boundaries:
  1. collect.sh  -- synthetic JSONL session logs with known values
  2. import_sprint.py -- validate_entry() and normalize_result() unit tests
  3. import_sprint.py -- import_from_file() integration tests
  4. generate_tables.py -- smoke tests for table generation

Run:
    python3 tools/test_pipeline.py
    python3 tools/test_pipeline.py -v
"""

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

# Add tools/ to path so we can import directly
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

from import_sprint import normalize_result, validate_entry

COLLECT_SH = os.path.join(REPO_ROOT, "tier-1", "collect.sh")


# ---------------------------------------------------------------------------
# Helpers for building synthetic JSONL session logs
# ---------------------------------------------------------------------------


def make_timestamp(base, offset_seconds):
    """Return ISO timestamp string offset from base datetime."""
    dt = base + timedelta(seconds=offset_seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "+00:00"


def make_assistant_message(
    msg_id,
    timestamp,
    model,
    input_tokens,
    output_tokens,
    cache_read=0,
    cache_creation=0,
    content_blocks=None,
):
    """Build a single assistant JSONL line."""
    msg = {
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "id": msg_id,
            "model": model,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_creation,
            },
            "content": content_blocks or [{"type": "text", "text": "ok"}],
        },
    }
    return json.dumps(msg)


def make_human_message(timestamp):
    """Build a human message JSONL line."""
    return json.dumps(
        {"type": "human", "timestamp": timestamp, "message": {"role": "user"}}
    )


def make_task_spawn_content():
    """Content blocks that include a Task tool_use (subagent spawn)."""
    return [
        {"type": "text", "text": "launching agent"},
        {"type": "tool_use", "name": "Task", "id": "tu_1", "input": {"prompt": "test"}},
    ]


def make_edit_content(file_path):
    """Content blocks with an Edit tool_use."""
    return [
        {
            "type": "tool_use",
            "name": "Edit",
            "id": "tu_e1",
            "input": {"file_path": file_path, "old_string": "a", "new_string": "b"},
        },
    ]


def make_write_content(file_path):
    """Content blocks with a Write tool_use."""
    return [
        {
            "type": "tool_use",
            "name": "Write",
            "id": "tu_w1",
            "input": {"file_path": file_path, "content": "hello"},
        },
    ]


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def build_fixture_session(tmpdir):
    """Create a synthetic JSONL session with known, assertable values.

    Layout:
      - 10 unique assistant messages (after dedup)
      - 2 duplicate messages (same ID, later timestamp -- should be deduped)
      - 1 subagent log with 3 messages
      - Gaps: two 30s (active), one 120s (idle), one 300s (idle)
      - Models: 5 opus, 3 sonnet, 2 haiku (parent) + 3 opus (subagent)
      - 1 Task tool_use block in message 6

    Returns dict with expected values for assertions.
    """
    base = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    # --- Parent session ---
    # Gaps between consecutive messages (in seconds):
    #   msg1->msg2: 30s  (active)
    #   msg2->msg3: 30s  (active)
    #   msg3->msg4: 120s (idle)
    #   msg4->msg5: 20s  (active)
    #   msg5->msg6: 10s  (active)
    #   msg6->msg7: 300s (idle)
    #   msg7->msg8: 15s  (active)
    #   msg8->msg9: 25s  (active)
    #   msg9->msg10: 5s  (active)
    # Plus 2 duplicates of msg2 and msg5 at later timestamps (gaps irrelevant -- deduped)

    offsets = [0, 30, 60, 180, 200, 210, 510, 525, 550, 555]
    # Duplicate messages at offsets 570 and 580 also add parent timestamps.
    # All parent timestamps sorted: 0,30,60,180,200,210,510,525,550,555,570,580
    # Gaps <=60s: 30+30 + 20+10 + 15+25+5+15+10 = 160s
    expected_active_s = 160

    models = [
        "claude-opus-4-20250514",  # msg1
        "claude-opus-4-20250514",  # msg2
        "claude-opus-4-20250514",  # msg3
        "claude-opus-4-20250514",  # msg4
        "claude-opus-4-20250514",  # msg5
        "claude-sonnet-4-20250514",  # msg6 (has Task spawn)
        "claude-sonnet-4-20250514",  # msg7
        "claude-sonnet-4-20250514",  # msg8
        "claude-haiku-4-20250514",  # msg9
        "claude-haiku-4-20250514",  # msg10
    ]

    # Token counts per message: (input, output, cache_read, cache_creation)
    token_counts = [
        (1000, 200, 500, 100),  # msg1
        (1100, 250, 600, 150),  # msg2
        (1200, 300, 700, 200),  # msg3
        (1300, 350, 800, 250),  # msg4
        (1400, 400, 900, 300),  # msg5
        (1500, 450, 1000, 350),  # msg6
        (1600, 500, 1100, 400),  # msg7
        (1700, 550, 1200, 450),  # msg8
        (1800, 600, 1300, 500),  # msg9
        (2000, 700, 1400, 600),  # msg10
    ]

    # Subagent tokens
    sub_token_counts = [
        (800, 150, 400, 80),  # sub_msg1
        (900, 180, 450, 90),  # sub_msg2
        (1000, 200, 500, 100),  # sub_msg3
    ]

    # Build parent log lines
    # Add Edit/Write tool_use blocks for rework rate testing:
    #   msg3: Edit /src/foo.ts
    #   msg4: Edit /src/foo.ts  (same file -- rework)
    #   msg5: Write /src/bar.ts
    #   msg8: Edit /src/foo.ts  (third time -- more rework)
    # Expected: 4 total edits / 2 unique files = rework_rate 2.0
    edit_content_map = {
        2: make_edit_content("/src/foo.ts"),  # msg3 (index 2)
        3: make_edit_content("/src/foo.ts"),  # msg4 (index 3)
        4: make_write_content("/src/bar.ts"),  # msg5 (index 4)
        7: make_edit_content("/src/foo.ts"),  # msg8 (index 7)
    }

    session_id = "test-session-abc123"
    lines = []
    for i, (offset, model, tokens) in enumerate(zip(offsets, models, token_counts)):
        ts = make_timestamp(base, offset)
        msg_id = f"msg_{i + 1:03d}"
        if i == 5:
            content = make_task_spawn_content()
        elif i in edit_content_map:
            content = edit_content_map[i]
        else:
            content = None
        lines.append(
            make_assistant_message(msg_id, ts, model, *tokens, content_blocks=content)
        )

    # Add 2 duplicates: msg_002 at +570s, msg_005 at +580s
    # These have the same msg ID, so they should be deduped (later timestamp overwrites)
    lines.append(
        make_assistant_message(
            "msg_002", make_timestamp(base, 570), models[1], *token_counts[1]
        )
    )
    lines.append(
        make_assistant_message(
            "msg_005", make_timestamp(base, 580), models[4], *token_counts[4]
        )
    )

    # Write parent session
    session_dir = tmpdir
    parent_log = os.path.join(session_dir, f"{session_id}.jsonl")
    with open(parent_log, "w") as f:
        f.write("\n".join(lines) + "\n")

    # Build subagent log
    sub_session_id = "sub-agent-def456"
    sub_dir = os.path.join(session_dir, session_id, "subagents")
    os.makedirs(sub_dir)

    sub_lines = []
    sub_base = base + timedelta(seconds=215)  # starts after msg6 spawns it
    sub_offsets = [0, 10, 20]
    for i, (offset, tokens) in enumerate(zip(sub_offsets, sub_token_counts)):
        ts = make_timestamp(sub_base, offset)
        msg_id = f"sub_msg_{i + 1:03d}"
        sub_lines.append(
            make_assistant_message(msg_id, ts, "claude-opus-4-20250514", *tokens)
        )

    sub_log = os.path.join(sub_dir, f"{sub_session_id}.jsonl")
    with open(sub_log, "w") as f:
        f.write("\n".join(sub_lines) + "\n")

    # --- Compute expected totals ---
    # 10 unique parent messages + 3 subagent messages = 13 API calls
    expected_api_calls = 13

    # Parent totals (10 unique messages)
    p_input = sum(t[0] for t in token_counts)
    p_output = sum(t[1] for t in token_counts)
    p_cache_read = sum(t[2] for t in token_counts)
    p_cache_creation = sum(t[3] for t in token_counts)

    # Subagent totals
    s_input = sum(t[0] for t in sub_token_counts)
    s_output = sum(t[1] for t in sub_token_counts)
    s_cache_read = sum(t[2] for t in sub_token_counts)
    s_cache_creation = sum(t[3] for t in sub_token_counts)

    total_tokens = (
        p_input
        + p_output
        + p_cache_read
        + p_cache_creation
        + s_input
        + s_output
        + s_cache_read
        + s_cache_creation
    )
    new_work_tokens = p_output + p_cache_creation + s_output + s_cache_creation
    cache_hit_pct = round((p_cache_read + s_cache_read) / total_tokens * 100, 1)

    # Model percentages
    # Opus: msg1-5 (parent) + msg1-3 (subagent) = 8 messages
    opus_tokens = sum(t[0] + t[1] + t[2] + t[3] for t in token_counts[:5]) + sum(
        t[0] + t[1] + t[2] + t[3] for t in sub_token_counts
    )
    # Sonnet: msg6-8 = 3 messages
    sonnet_tokens = sum(t[0] + t[1] + t[2] + t[3] for t in token_counts[5:8])
    # Haiku: msg9-10 = 2 messages
    haiku_tokens = sum(t[0] + t[1] + t[2] + t[3] for t in token_counts[8:10])

    opus_pct = round(opus_tokens / total_tokens * 100, 1)
    sonnet_pct = round(sonnet_tokens / total_tokens * 100, 1)
    haiku_pct = round(haiku_tokens / total_tokens * 100, 1)

    return {
        "session_id": session_id,
        "log_dir": session_dir,
        "expected": {
            "active_session_time_s": expected_active_s,
            "total_tokens": total_tokens,
            "new_work_tokens": new_work_tokens,
            "cache_hit_rate_pct": cache_hit_pct,
            "api_calls": expected_api_calls,
            "subagents": 1,
            "opus_pct": opus_pct,
            "sonnet_pct": sonnet_pct,
            "haiku_pct": haiku_pct,
            "rework_rate": 2.0,  # 4 edits / 2 unique files
        },
        # For --after test: filter excludes events with timestamp < after_ts.
        # after_ts = offset 60 (msg3's timestamp). Events AT offset 60 pass (not strictly less).
        # Passing parent events: msg3(60), msg4(180), msg5(200), msg6(210), msg7(510),
        #   msg8(525), msg9(550), msg10(555), dup_msg2(570), dup_msg5(580) = 10 unique lines
        # But msg2 and msg5 are deduped by ID -> 9 unique parent msgs + 3 sub = 12
        "after_ts": make_timestamp(base, 60),
        "after_expected": {
            "api_calls": 12,
        },
    }


# ---------------------------------------------------------------------------
# Helpers for import tests
# ---------------------------------------------------------------------------


def make_valid_entry():
    """Return a minimal valid sprint entry for import testing."""
    return {
        "project": "test-project",
        "sprint": 99,
        "label": "Test S99",
        "phase": "Phase 99: Testing",
        "metrics": {
            "active_session_time_s": 600,
            "active_session_time_display": "10m 0s",
            "total_tokens": 5000000,
            "total_tokens_display": "5.0M",
            "new_work_tokens": 200000,
            "new_work_tokens_display": "200K",
            "opus_pct": 70.0,
            "sonnet_pct": 25.0,
            "haiku_pct": 5.0,
            "subagents": 2,
            "api_calls": 100,
            "tests_total": 50,
            "tests_added": 10,
            "coverage_pct": 65.0,
            "lint_errors": 0,
            "gates_first_pass": True,
            "gates_first_pass_note": None,
            "loc_added": 500,
        },
        "hypotheses": [
            {
                "id": "H1",
                "name": "3-phase sprint works across project types",
                "result": "confirmed",
                "evidence": "Test evidence",
            },
            {
                "id": "H5",
                "name": "Gates catch real issues",
                "result": "partially_confirmed",
                "evidence": "More test evidence",
            },
        ],
    }


# ===========================================================================
# Test Classes
# ===========================================================================


class TestCollectSh(unittest.TestCase):
    """Test collect.sh against synthetic JSONL session logs."""

    @classmethod
    def setUpClass(cls):
        """Build the fixture once for all tests in this class."""
        cls.tmpdir = tempfile.mkdtemp(prefix="flowstate-test-")
        cls.fixture = build_fixture_session(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _run_collect(self, extra_args=None):
        """Run collect.sh --json against the fixture, return parsed JSON."""
        # collect.sh auto-detects logs from PROJECT_SLUG derived from cwd.
        # We override by setting up the expected directory structure and running
        # from a temp "project" directory whose slug maps to our fixture log dir.
        #
        # Simpler approach: we patch the script's project detection by creating a
        # symlink-based structure. But even simpler: we call the Python section
        # directly since collect.sh is a thin bash wrapper around an inline Python script.
        #
        # Actually, the cleanest way: create a directory whose `pwd | sed 's|/|-|g; s| |-|g'`
        # maps to our tmpdir name under ~/.claude/projects/, then run from there.
        # That's fragile. Instead, let's create the expected directory structure.

        # The script expects logs at $HOME/.claude/projects/$PROJECT_SLUG/
        # where PROJECT_SLUG is derived from cwd. We'll create a fake project dir
        # and point its slug at our fixture.

        fake_project = os.path.join(self.tmpdir, "fake-project")
        os.makedirs(fake_project, exist_ok=True)

        # collect.sh computes slug from `pwd` which returns the realpath on macOS
        # (e.g., /private/var/folders/... not /var/folders/...)
        real_fake_project = os.path.realpath(fake_project)
        slug = real_fake_project.replace("/", "-").replace(" ", "-")
        claude_projects = os.path.join(os.path.expanduser("~"), ".claude", "projects")
        slug_dir = os.path.join(claude_projects, slug)

        # Create a symlink from the expected slug dir to our fixture log dir
        created_symlink = False
        try:
            if not os.path.exists(slug_dir):
                os.symlink(self.fixture["log_dir"], slug_dir)
                created_symlink = True

            cmd = ["bash", COLLECT_SH, "--json"]
            if extra_args:
                cmd.extend(extra_args)
            cmd.append(self.fixture["session_id"])

            result = subprocess.run(
                cmd,
                cwd=fake_project,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.fail(
                    f"collect.sh failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
                )

            return json.loads(result.stdout)
        finally:
            if created_symlink and os.path.islink(slug_dir):
                os.unlink(slug_dir)

    def test_active_session_time(self):
        data = self._run_collect()
        self.assertEqual(
            data["active_session_time_s"],
            self.fixture["expected"]["active_session_time_s"],
        )

    def test_total_tokens(self):
        data = self._run_collect()
        self.assertEqual(data["total_tokens"], self.fixture["expected"]["total_tokens"])

    def test_new_work_tokens(self):
        data = self._run_collect()
        self.assertEqual(
            data["new_work_tokens"], self.fixture["expected"]["new_work_tokens"]
        )

    def test_api_calls_deduped(self):
        """Duplicate messages (same ID) should not inflate API call count."""
        data = self._run_collect()
        self.assertEqual(data["api_calls"], self.fixture["expected"]["api_calls"])

    def test_subagent_count(self):
        data = self._run_collect()
        self.assertEqual(data["subagents"], self.fixture["expected"]["subagents"])

    def test_model_percentages(self):
        data = self._run_collect()
        self.assertAlmostEqual(
            data["opus_pct"], self.fixture["expected"]["opus_pct"], places=1
        )
        self.assertAlmostEqual(
            data["sonnet_pct"], self.fixture["expected"]["sonnet_pct"], places=1
        )
        self.assertAlmostEqual(
            data["haiku_pct"], self.fixture["expected"]["haiku_pct"], places=1
        )

    def test_cache_hit_rate(self):
        data = self._run_collect()
        self.assertAlmostEqual(
            data["cache_hit_rate_pct"],
            self.fixture["expected"]["cache_hit_rate_pct"],
            places=1,
        )

    def test_rework_rate(self):
        data = self._run_collect()
        self.assertEqual(data["rework_rate"], self.fixture["expected"]["rework_rate"])

    def test_after_filter(self):
        """--after should exclude messages before the boundary."""
        data = self._run_collect(["--after", self.fixture["after_ts"]])
        self.assertEqual(data["api_calls"], self.fixture["after_expected"]["api_calls"])
        # Tokens should be less than unfiltered
        unfiltered = self._run_collect()
        self.assertLess(data["total_tokens"], unfiltered["total_tokens"])


class TestNormalizeResult(unittest.TestCase):
    """Unit tests for normalize_result()."""

    def test_confirmed(self):
        self.assertEqual(normalize_result("confirmed"), "confirmed")

    def test_confirmed_case_insensitive(self):
        self.assertEqual(normalize_result("Confirmed"), "confirmed")

    def test_supported_maps_to_confirmed(self):
        self.assertEqual(normalize_result("supported"), "confirmed")

    def test_partially_confirmed(self):
        self.assertEqual(normalize_result("partially_confirmed"), "partially_confirmed")

    def test_mostly_maps_to_partial(self):
        self.assertEqual(normalize_result("mostly"), "partially_confirmed")

    def test_fraction_2_5(self):
        self.assertEqual(normalize_result("2/5"), "partially_confirmed")

    def test_fraction_3_5(self):
        self.assertEqual(normalize_result("3/5"), "partially_confirmed")

    def test_inconclusive(self):
        self.assertEqual(normalize_result("inconclusive"), "inconclusive")

    def test_falsified(self):
        self.assertEqual(normalize_result("falsified"), "falsified")

    def test_rejected_maps_to_falsified(self):
        self.assertEqual(normalize_result("rejected"), "falsified")

    def test_unknown_returns_none(self):
        self.assertIsNone(normalize_result("yolo"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(normalize_result(""))


class TestValidateEntry(unittest.TestCase):
    """Unit tests for validate_entry()."""

    def test_valid_entry_no_errors(self):
        entry = make_valid_entry()
        errors, warnings = validate_entry(entry)
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_valid_entry_may_have_warnings(self):
        """Valid entry with correct data should produce 0 errors (warnings ok)."""
        entry = make_valid_entry()
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    # --- Type errors ---

    def test_string_int_field_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["tests_total"] = "lots"
        errors, _ = validate_entry(entry)
        self.assertTrue(any("tests_total" in e for e in errors))

    def test_float_for_int_field_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["active_session_time_s"] = 12.5
        errors, _ = validate_entry(entry)
        # 12.5 is a float but field expects int. However validate_entry checks
        # isinstance(val, int) -- float 12.5 is not int.
        self.assertTrue(any("active_session_time_s" in e for e in errors))

    def test_string_bool_field_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["gates_first_pass"] = "yes"
        errors, _ = validate_entry(entry)
        self.assertTrue(any("gates_first_pass" in e for e in errors))

    def test_negative_loc_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["loc_added"] = -10
        errors, _ = validate_entry(entry)
        self.assertTrue(any("loc_added" in e for e in errors))

    # --- Range errors ---

    def test_model_pcts_not_100(self):
        entry = make_valid_entry()
        entry["metrics"]["opus_pct"] = 50.0
        entry["metrics"]["sonnet_pct"] = 10.0
        entry["metrics"]["haiku_pct"] = 5.0
        errors, _ = validate_entry(entry)
        self.assertTrue(any("percentages" in e.lower() or "65" in e for e in errors))

    def test_new_work_exceeds_total(self):
        entry = make_valid_entry()
        entry["metrics"]["new_work_tokens"] = 6000000
        entry["metrics"]["total_tokens"] = 5000000
        errors, _ = validate_entry(entry)
        self.assertTrue(any("exceeds" in e for e in errors))

    def test_coverage_over_100(self):
        entry = make_valid_entry()
        entry["metrics"]["coverage_pct"] = 150.0
        errors, _ = validate_entry(entry)
        self.assertTrue(any("coverage_pct" in e for e in errors))

    # --- Hypothesis auto-corrections ---

    def test_wrong_hypothesis_name_auto_corrected(self):
        entry = make_valid_entry()
        entry["hypotheses"][0]["name"] = "wrong name for H1"
        errors, warnings = validate_entry(entry)
        self.assertEqual(len(errors), 0)
        self.assertTrue(any("auto-corrected" in w and "H1" in w for w in warnings))
        self.assertEqual(
            entry["hypotheses"][0]["name"], "3-phase sprint works across project types"
        )

    def test_supported_result_auto_corrected(self):
        entry = make_valid_entry()
        entry["hypotheses"][0]["result"] = "supported"
        errors, warnings = validate_entry(entry)
        self.assertEqual(len(errors), 0)
        self.assertTrue(any("auto-corrected" in w for w in warnings))
        self.assertEqual(entry["hypotheses"][0]["result"], "confirmed")

    def test_unknown_hypothesis_id_warns(self):
        entry = make_valid_entry()
        entry["hypotheses"].append(
            {
                "id": "H99",
                "name": "fake hypothesis",
                "result": "confirmed",
                "evidence": "none",
            }
        )
        errors, warnings = validate_entry(entry)
        self.assertEqual(len(errors), 0)
        self.assertTrue(any("H99" in w and "unknown" in w.lower() for w in warnings))

    def test_invalid_result_after_normalization_errors(self):
        entry = make_valid_entry()
        entry["hypotheses"][0]["result"] = "yolo"
        errors, _ = validate_entry(entry)
        self.assertTrue(
            any("invalid result" in e.lower() and "H1" in e for e in errors)
        )

    # --- Normalizations ---

    def test_empty_gates_note_normalized_to_null(self):
        entry = make_valid_entry()
        entry["metrics"]["gates_first_pass"] = True
        entry["metrics"]["gates_first_pass_note"] = ""
        errors, warnings = validate_entry(entry)
        self.assertIsNone(entry["metrics"]["gates_first_pass_note"])
        self.assertTrue(any("normalized" in w for w in warnings))

    # --- Null-allowed fields ---

    def test_null_coverage_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["coverage_pct"] = None
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    def test_null_tests_total_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["tests_total"] = None
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    def test_null_lint_errors_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["lint_errors"] = None
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    # --- Eval fields ---

    def test_valid_task_type_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["task_type"] = "feature"
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    def test_invalid_task_type_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["task_type"] = "yolo"
        errors, _ = validate_entry(entry)
        self.assertTrue(any("task_type" in e for e in errors))

    def test_null_task_type_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["task_type"] = None
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    def test_valid_rework_rate_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["rework_rate"] = 2.5
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    def test_rework_rate_below_range_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["rework_rate"] = 0.5
        errors, _ = validate_entry(entry)
        self.assertTrue(any("rework_rate" in e for e in errors))

    def test_valid_judge_score_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["judge_score"] = [4, 5, 3, 5, 4]
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    def test_judge_score_wrong_length_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["judge_score"] = [4, 5, 3]
        errors, _ = validate_entry(entry)
        self.assertTrue(any("judge_score" in e for e in errors))

    def test_judge_score_out_of_range_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["judge_score"] = [4, 5, 6, 5, 4]
        errors, _ = validate_entry(entry)
        self.assertTrue(any("judge_score" in e for e in errors))

    def test_null_judge_score_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["judge_score"] = None
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    def test_valid_coderabbit_issues_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["coderabbit_issues"] = 3
        entry["metrics"]["coderabbit_issues_valid"] = 2
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    def test_coderabbit_issues_string_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["coderabbit_issues"] = "many"
        errors, _ = validate_entry(entry)
        self.assertTrue(any("coderabbit_issues" in e for e in errors))

    def test_valid_mutation_score_accepted(self):
        entry = make_valid_entry()
        entry["metrics"]["mutation_score_pct"] = 85.5
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)

    def test_mutation_score_over_100_rejected(self):
        entry = make_valid_entry()
        entry["metrics"]["mutation_score_pct"] = 150.0
        errors, _ = validate_entry(entry)
        self.assertTrue(any("mutation_score_pct" in e for e in errors))

    def test_no_eval_fields_backwards_compat(self):
        """Entries without any eval fields should still validate cleanly."""
        entry = make_valid_entry()
        # Don't add any eval fields -- should pass
        errors, _ = validate_entry(entry)
        self.assertEqual(len(errors), 0)


class TestImportEndToEnd(unittest.TestCase):
    """Integration tests for import_from_file()."""

    def setUp(self):
        """Create a temp directory with sprints.json and hypotheses.json."""
        self.tmpdir = tempfile.mkdtemp(prefix="flowstate-import-test-")
        self.original_repo_root = __import__("import_sprint").REPO_ROOT

        # Create minimal sprints.json
        sprints_path = os.path.join(self.tmpdir, "sprints.json")
        with open(sprints_path, "w") as f:
            json.dump({"_note": "test", "sprints": []}, f)

        # Copy hypotheses.json from repo
        hypo_src = os.path.join(REPO_ROOT, "hypotheses.json")
        hypo_dst = os.path.join(self.tmpdir, "hypotheses.json")
        shutil.copy2(hypo_src, hypo_dst)

        # Create imports/ directory
        os.makedirs(os.path.join(self.tmpdir, "imports"), exist_ok=True)

        # Monkey-patch REPO_ROOT in import_sprint module
        import import_sprint

        import_sprint.REPO_ROOT = self.tmpdir

    def tearDown(self):
        import import_sprint

        import_sprint.REPO_ROOT = self.original_repo_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_import_json(self, entry, filename="test-import.json"):
        path = os.path.join(self.tmpdir, filename)
        with open(path, "w") as f:
            json.dump(entry, f, indent=2)
        return path

    def _load_sprints(self):
        with open(os.path.join(self.tmpdir, "sprints.json")) as f:
            return json.load(f)

    def test_valid_import_appends(self):
        import import_sprint

        entry = make_valid_entry()
        path = self._write_import_json(entry)
        import_sprint.import_from_file(path)
        data = self._load_sprints()
        self.assertEqual(len(data["sprints"]), 1)
        self.assertEqual(data["sprints"][0]["project"], "test-project")
        self.assertEqual(data["sprints"][0]["sprint"], 99)

    def test_duplicate_sprint_blocked(self):
        import import_sprint

        entry = make_valid_entry()
        path = self._write_import_json(entry)
        import_sprint.import_from_file(path)

        # Second import of same project+sprint should sys.exit
        path2 = self._write_import_json(entry, "dup.json")
        with self.assertRaises(SystemExit) as ctx:
            import_sprint.import_from_file(path2)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_required_fields_exits(self):
        import import_sprint

        entry = make_valid_entry()
        del entry["label"]  # remove required field
        path = self._write_import_json(entry)
        with self.assertRaises(SystemExit) as ctx:
            import_sprint.import_from_file(path)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_required_metrics_exits(self):
        import import_sprint

        entry = make_valid_entry()
        del entry["metrics"]["total_tokens"]
        path = self._write_import_json(entry)
        with self.assertRaises(SystemExit) as ctx:
            import_sprint.import_from_file(path)
        self.assertEqual(ctx.exception.code, 1)

    def test_archive_created(self):
        import import_sprint

        entry = make_valid_entry()
        path = self._write_import_json(entry)
        import_sprint.import_from_file(path)
        archive = os.path.join(
            self.tmpdir, "imports", "test-project-sprint-99-import.json"
        )
        self.assertTrue(os.path.exists(archive))

    def test_dry_run_does_not_write(self):
        import import_sprint

        entry = make_valid_entry()
        path = self._write_import_json(entry)
        import_sprint.import_from_file(path, dry_run=True)
        data = self._load_sprints()
        self.assertEqual(len(data["sprints"]), 0)

    def test_type_error_blocks_import(self):
        import import_sprint

        entry = make_valid_entry()
        entry["metrics"]["total_tokens"] = "many"
        path = self._write_import_json(entry)
        with self.assertRaises(SystemExit) as ctx:
            import_sprint.import_from_file(path)
        self.assertEqual(ctx.exception.code, 1)
        # sprints.json should be unchanged
        data = self._load_sprints()
        self.assertEqual(len(data["sprints"]), 0)


class TestGenerateTables(unittest.TestCase):
    """Smoke tests for generate_tables.py commands."""

    def _run_generate(self, args):
        """Run generate_tables.py with args, return (returncode, stdout, stderr)."""
        cmd = [sys.executable, os.path.join(TOOLS_DIR, "generate_tables.py")] + args
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=REPO_ROOT
        )
        return result.returncode, result.stdout, result.stderr

    def test_cross_project_runs(self):
        rc, out, err = self._run_generate(["cross-project"])
        self.assertEqual(rc, 0, f"stderr: {err}")
        self.assertIn("|", out)
        self.assertIn("Active session time", out)

    def test_tokens_per_loc_runs(self):
        rc, out, err = self._run_generate(["tokens-per-loc"])
        self.assertEqual(rc, 0, f"stderr: {err}")
        self.assertIn("|", out)
        self.assertIn("LOC", out)

    def test_sprint_table_runs(self):
        rc, out, err = self._run_generate(["sprint", "uluka", "0"])
        self.assertEqual(rc, 0, f"stderr: {err}")
        self.assertIn("|", out)
        self.assertIn("Active session time", out)

    def test_hypotheses_table_runs(self):
        rc, out, err = self._run_generate(["hypotheses", "uluka", "0"])
        self.assertEqual(rc, 0, f"stderr: {err}")
        self.assertIn("|", out)
        self.assertIn("Hypothesis", out)

    def test_compare_table_runs(self):
        rc, out, err = self._run_generate(["compare", "uluka", "0", "1", "2"])
        self.assertEqual(rc, 0, f"stderr: {err}")
        self.assertIn("|", out)
        self.assertIn("Sprint", out)

    def test_efficiency_by_type_runs(self):
        rc, out, err = self._run_generate(["efficiency-by-type"])
        self.assertEqual(rc, 0, f"stderr: {err}")
        # No task_type data yet, so should print the "no data" message
        self.assertIn("No sprints with task_type data yet", out)

    def test_eval_effectiveness_runs(self):
        rc, out, err = self._run_generate(["eval-effectiveness"])
        self.assertEqual(rc, 0, f"stderr: {err}")
        # No eval data yet, so should print the "no data" message
        self.assertIn("No sprints with eval data yet", out)

    def test_nonexistent_sprint_fails(self):
        rc, _, err = self._run_generate(["sprint", "uluka", "999"])
        self.assertNotEqual(rc, 0)

    def test_no_args_fails(self):
        rc, _, _ = self._run_generate([])
        self.assertNotEqual(rc, 0)


class TestGateScripts(unittest.TestCase):
    """Smoke tests for the gate scripts (deps_check, sast_check, deadcode_check)."""

    def _run_script(self, script_name, args=None, cwd=None):
        """Run a gate script and return (returncode, stdout, stderr)."""
        script = os.path.join(REPO_ROOT, "tools", script_name)
        cmd = ["bash", script]
        if args:
            cmd.extend(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd or tempfile.mkdtemp(),
        )
        return result.returncode, result.stdout, result.stderr

    def test_deps_check_no_lockfile(self):
        """deps_check should exit 2 when no lockfile is found."""
        rc, out, _ = self._run_script("deps_check.sh")
        self.assertEqual(rc, 2)

    def test_deps_check_json_no_lockfile(self):
        """deps_check --json should return skipped status when no lockfile."""
        rc, out, _ = self._run_script("deps_check.sh", ["--json"])
        self.assertEqual(rc, 2)
        data = json.loads(out)
        self.assertEqual(data["status"], "skipped")

    def test_sast_check_no_semgrep(self):
        """sast_check should exit 2 when semgrep is not installed (or handle gracefully)."""
        rc, out, _ = self._run_script("sast_check.sh", ["--json"])
        # Either semgrep is installed (rc 0) or not (rc 2)
        self.assertIn(rc, [0, 2])
        if rc == 2:
            data = json.loads(out)
            self.assertEqual(data["status"], "skipped")

    def test_deadcode_check_no_project(self):
        """deadcode_check should exit 2 when no project type detected."""
        rc, out, _ = self._run_script("deadcode_check.sh")
        self.assertEqual(rc, 2)

    def test_deadcode_check_json_no_project(self):
        """deadcode_check --json should return skipped status."""
        rc, out, _ = self._run_script("deadcode_check.sh", ["--json"])
        self.assertEqual(rc, 2)
        data = json.loads(out)
        self.assertEqual(data["status"], "skipped")

    def test_deps_check_no_changes(self):
        """deps_check in a git repo with package.json but no diff should pass."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Init a git repo with a package.json
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "test"],
                cwd=tmpdir,
                capture_output=True,
            )
            pkg = os.path.join(tmpdir, "package.json")
            lock = os.path.join(tmpdir, "package-lock.json")
            with open(pkg, "w") as f:
                json.dump({"dependencies": {"express": "^4.0.0"}}, f)
            with open(lock, "w") as f:
                json.dump({}, f)
            subprocess.run(["git", "add", "-A"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"], cwd=tmpdir, capture_output=True
            )
            rc, out, _ = self._run_script("deps_check.sh", cwd=tmpdir)
            self.assertEqual(rc, 0)
            self.assertIn("No new dependencies", out)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
