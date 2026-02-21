#!/usr/bin/env python3
"""Import a completed sprint's metrics into sprints.json.

Usage:
    python3 import_sprint.py --from [--dry-run] <import-json>
    python3 import_sprint.py <project> <sprint-number>

Examples:
    python3 import_sprint.py --from ~/.flowstate/uluka/metrics/sprint-6-import.json
    python3 import_sprint.py --from --dry-run ~/.flowstate/uluka/metrics/sprint-7-import.json
    python3 import_sprint.py uluka 4

The --from mode reads a complete import JSON written by the sprint agent during
Phase 3. No interactive prompts needed. Validates types, ranges, and hypotheses
against hypotheses.json before importing.

The --dry-run flag (with --from) validates and previews without writing.

The <project> <sprint-number> mode reads collect.sh output and the retro, then
prompts interactively for fields that collect.sh can't know (tests, coverage, etc.).
"""

import json
import os
import re
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_FIELDS = ["project", "sprint", "label", "phase", "metrics", "hypotheses"]
REQUIRED_METRICS = [
    "active_session_time_s",
    "active_session_time_display",
    "total_tokens",
    "total_tokens_display",
    "new_work_tokens",
    "new_work_tokens_display",
    "opus_pct",
    "sonnet_pct",
    "haiku_pct",
    "subagents",
    "api_calls",
    "tests_total",
    "tests_added",
    "coverage_pct",
    "lint_errors",
    "gates_first_pass",
    "loc_added",
]


# --- Validation ---


def load_hypothesis_registry():
    """Load hypotheses.json from the repo root."""
    path = os.path.join(REPO_ROOT, "hypotheses.json")
    if not os.path.exists(path):
        print(f"WARNING: {path} not found. Skipping hypothesis validation.")
        return None
    with open(path) as f:
        return json.load(f)


def normalize_result(raw):
    """Normalize a hypothesis result value to a canonical form."""
    raw_lower = raw.lower().strip()
    if "confirm" in raw_lower and "partial" not in raw_lower:
        return "confirmed"
    if "partial" in raw_lower or "mostly" in raw_lower:
        return "partially_confirmed"
    if "inconclusive" in raw_lower:
        return "inconclusive"
    if "falsif" in raw_lower or "reject" in raw_lower:
        return "falsified"
    if raw_lower == "supported":
        return "confirmed"
    # Patterns like "2/5", "3/5" -> partially_confirmed
    if re.match(r"^\d+/\d+$", raw_lower):
        return "partially_confirmed"
    return None


def validate_entry(entry):
    """Validate a sprint entry for types, ranges, and hypothesis correctness.

    Returns (errors, warnings) where errors are fatal and warnings are auto-corrections.
    Modifies entry in-place for auto-corrections.
    """
    errors = []
    warnings = []
    m = entry.get("metrics", {})

    # --- Type and range checks ---

    def check_type(field, value, expected_types, label=None):
        label = label or field
        if not isinstance(value, expected_types):
            # Allow int where float is expected
            if expected_types == float and isinstance(value, int):
                return True
            errors.append(
                f"{label}: expected {expected_types.__name__ if isinstance(expected_types, type) else str(expected_types)}, "
                f"got {type(value).__name__} ({value!r})"
            )
            return False
        return True

    def check_range(field, value, low, high, label=None):
        label = label or field
        if value is not None and isinstance(value, (int, float)):
            if not (low <= value <= high):
                errors.append(f"{label}: {value} out of range [{low}, {high}]")
                return False
        return True

    # Top-level fields
    if not isinstance(entry.get("project"), str) or not entry["project"]:
        errors.append("project: must be a non-empty string")
    if not isinstance(entry.get("sprint"), int):
        errors.append(
            f"sprint: must be an integer, got {type(entry.get('sprint')).__name__}"
        )
    if not isinstance(entry.get("label"), str) or not entry["label"]:
        errors.append("label: must be a non-empty string")
    if not isinstance(entry.get("phase"), str) or not entry["phase"]:
        errors.append("phase: must be a non-empty string")
    if not isinstance(entry.get("hypotheses"), list):
        errors.append("hypotheses: must be a list")

    # Integer metrics
    for field in [
        "active_session_time_s",
        "total_tokens",
        "new_work_tokens",
        "subagents",
        "api_calls",
        "loc_added",
    ]:
        val = m.get(field)
        if val is not None and not isinstance(val, int):
            errors.append(
                f"metrics.{field}: must be int, got {type(val).__name__} ({val!r})"
            )

    # tests_total and tests_added: int or null
    for field in ["tests_total", "tests_added"]:
        val = m.get(field)
        if val is not None and not isinstance(val, int):
            errors.append(
                f"metrics.{field}: must be int or null, got {type(val).__name__} ({val!r})"
            )

    # lint_errors: int or null
    val = m.get("lint_errors")
    if val is not None and not isinstance(val, int):
        errors.append(
            f"metrics.lint_errors: must be int or null, got {type(val).__name__} ({val!r})"
        )

    # Float/int metrics (percentages)
    for field in ["opus_pct", "sonnet_pct", "haiku_pct"]:
        val = m.get(field)
        if val is not None and not isinstance(val, (int, float)):
            errors.append(
                f"metrics.{field}: must be numeric, got {type(val).__name__} ({val!r})"
            )
        check_range(field, val, 0, 100, f"metrics.{field}")

    # coverage_pct: float/int or null
    val = m.get("coverage_pct")
    if val is not None and not isinstance(val, (int, float)):
        errors.append(
            f"metrics.coverage_pct: must be numeric or null, got {type(val).__name__} ({val!r})"
        )
    if val is not None:
        check_range("coverage_pct", val, 0, 100, "metrics.coverage_pct")

    # gates_first_pass: bool or null (null for planning-only sprints)
    val = m.get("gates_first_pass")
    if val is not None and not isinstance(val, bool):
        errors.append(
            f"metrics.gates_first_pass: must be bool or null, got {type(val).__name__} ({val!r})"
        )

    # Range checks for positive integers
    check_range(
        "active_session_time_s",
        m.get("active_session_time_s"),
        0,
        36000,
        "metrics.active_session_time_s",
    )
    check_range(
        "total_tokens", m.get("total_tokens"), 1, 100_000_000, "metrics.total_tokens"
    )
    check_range("api_calls", m.get("api_calls"), 1, 5000, "metrics.api_calls")
    check_range("loc_added", m.get("loc_added"), 0, 100_000, "metrics.loc_added")

    # new_work_tokens should not exceed total_tokens
    nw = m.get("new_work_tokens")
    tt = m.get("total_tokens")
    if isinstance(nw, int) and isinstance(tt, int) and nw > tt:
        errors.append(f"metrics.new_work_tokens ({nw}) exceeds total_tokens ({tt})")

    # Model percentages should sum to ~100%
    opus = m.get("opus_pct", 0)
    sonnet = m.get("sonnet_pct", 0)
    haiku = m.get("haiku_pct", 0)
    if all(isinstance(v, (int, float)) for v in [opus, sonnet, haiku]):
        total_pct = opus + sonnet + haiku
        if not (99.0 <= total_pct <= 101.0):
            errors.append(f"Model percentages sum to {total_pct:.1f}%, expected ~100%")

    # --- Normalizations ---

    # --- Optional eval fields ---

    # task_type: string enum or null
    task_type = m.get("task_type")
    valid_task_types = {
        "feature",
        "bugfix",
        "refactor",
        "infra",
        "planning",
        "hardening",
    }
    if task_type is not None:
        if not isinstance(task_type, str):
            errors.append(
                f"metrics.task_type: must be string or null, got {type(task_type).__name__}"
            )
        elif task_type not in valid_task_types:
            errors.append(
                f"metrics.task_type: '{task_type}' not in {sorted(valid_task_types)}"
            )

    # rework_rate: float or null, range [1.0, 50.0]
    rw = m.get("rework_rate")
    if rw is not None:
        if not isinstance(rw, (int, float)):
            errors.append(
                f"metrics.rework_rate: must be numeric or null, got {type(rw).__name__}"
            )
        else:
            check_range("rework_rate", rw, 1.0, 50.0, "metrics.rework_rate")

    # judge_score: list of 5 ints (1-5) or null
    js = m.get("judge_score")
    if js is not None:
        if not isinstance(js, list) or len(js) != 5:
            errors.append("metrics.judge_score: must be a list of 5 integers or null")
        else:
            for i, v in enumerate(js):
                if not isinstance(v, int) or not (1 <= v <= 5):
                    errors.append(
                        f"metrics.judge_score[{i}]: must be int 1-5, got {v!r}"
                    )

    # judge_blocked: bool or null
    jb = m.get("judge_blocked")
    if jb is not None and not isinstance(jb, bool):
        errors.append(
            f"metrics.judge_blocked: must be bool or null, got {type(jb).__name__}"
        )

    # judge_block_reason: string or null
    jbr = m.get("judge_block_reason")
    if jbr is not None and not isinstance(jbr, str):
        errors.append(
            f"metrics.judge_block_reason: must be string or null, got {type(jbr).__name__}"
        )

    # coderabbit_issues: int or null
    cri = m.get("coderabbit_issues")
    if cri is not None and not isinstance(cri, int):
        errors.append(
            f"metrics.coderabbit_issues: must be int or null, got {type(cri).__name__}"
        )

    # coderabbit_issues_valid: int or null
    criv = m.get("coderabbit_issues_valid")
    if criv is not None and not isinstance(criv, int):
        errors.append(
            f"metrics.coderabbit_issues_valid: must be int or null, got {type(criv).__name__}"
        )

    # mutation_score_pct: float or null, range [0, 100]
    msp = m.get("mutation_score_pct")
    if msp is not None:
        if not isinstance(msp, (int, float)):
            errors.append(
                f"metrics.mutation_score_pct: must be numeric or null, got {type(msp).__name__}"
            )
        else:
            check_range("mutation_score_pct", msp, 0, 100, "metrics.mutation_score_pct")

    # delegation_ratio_pct: float or null, range [0, 100]
    drp = m.get("delegation_ratio_pct")
    if drp is not None:
        if not isinstance(drp, (int, float)):
            errors.append(
                f"metrics.delegation_ratio_pct: must be numeric or null, got {type(drp).__name__}"
            )
        else:
            check_range("delegation_ratio_pct", drp, 0, 100, "metrics.delegation_ratio_pct")

    # orchestrator_tokens: int or null
    ot = m.get("orchestrator_tokens")
    if ot is not None and not isinstance(ot, int):
        errors.append(
            f"metrics.orchestrator_tokens: must be int or null, got {type(ot).__name__}"
        )

    # subagent_tokens: int or null
    st = m.get("subagent_tokens")
    if st is not None and not isinstance(st, int):
        errors.append(
            f"metrics.subagent_tokens: must be int or null, got {type(st).__name__}"
        )

    # context_compressions: int or null, range [0, 50]
    cc_count = m.get("context_compressions")
    if cc_count is not None:
        if not isinstance(cc_count, int):
            errors.append(
                f"metrics.context_compressions: must be int or null, got {type(cc_count).__name__}"
            )
        else:
            check_range("context_compressions", cc_count, 0, 50, "metrics.context_compressions")

    # --- Normalizations ---

    # gates_first_pass_note: normalize "" to null when gates passed
    note = m.get("gates_first_pass_note")
    if m.get("gates_first_pass") is True and note == "":
        m["gates_first_pass_note"] = None
        warnings.append(
            "metrics.gates_first_pass_note: normalized '' to null (gates passed)"
        )

    # --- Hypothesis validation ---

    registry = load_hypothesis_registry()
    if registry and isinstance(entry.get("hypotheses"), list):
        valid_results = set(registry.get("valid_results", []))
        canonical = registry.get("hypotheses", {})

        for h in entry["hypotheses"]:
            hid = h.get("id", "?")

            # ID must exist in registry (allow H3_control as historical)
            if hid not in canonical and hid != "H3_control":
                warnings.append(f"hypothesis {hid}: not in registry (unknown ID)")

            # Name auto-correction
            if hid in canonical:
                expected_name = canonical[hid]
                actual_name = h.get("name", "")
                if actual_name != expected_name:
                    warnings.append(
                        f"hypothesis {hid}: name '{actual_name}' -> '{expected_name}' (auto-corrected)"
                    )
                    h["name"] = expected_name

            # Result normalization
            result = h.get("result", "")
            if result not in valid_results:
                normalized = normalize_result(result)
                if normalized:
                    warnings.append(
                        f"hypothesis {hid}: result '{result}' -> '{normalized}' (auto-corrected)"
                    )
                    h["result"] = normalized
                else:
                    errors.append(
                        f"hypothesis {hid}: invalid result '{result}'. "
                        f"Valid: {', '.join(sorted(valid_results))}"
                    )

    return errors, warnings


# --- File I/O ---


def load_sprints_json():
    sprints_path = os.path.join(REPO_ROOT, "sprints.json")
    with open(sprints_path) as f:
        data = json.load(f)
    return sprints_path, data


def check_duplicate(data, project, sprint_num):
    for s in data["sprints"]:
        if s["project"] == project and s["sprint"] == sprint_num:
            print(
                f"ERROR: {project} sprint {sprint_num} already exists in sprints.json."
            )
            sys.exit(1)


def save_sprints_json(sprints_path, data):
    with open(sprints_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def archive_import_json(source_path, entry):
    """Copy import JSON to imports/ for audit trail."""
    archive_dir = os.path.join(REPO_ROOT, "imports")
    os.makedirs(archive_dir, exist_ok=True)
    archive_name = f"{entry['project']}-sprint-{entry['sprint']}-import.json"
    archive_path = os.path.join(archive_dir, archive_name)
    shutil.copy2(source_path, archive_path)
    return archive_name


# --- Import modes ---


def import_from_file(path, dry_run=False):
    """Non-interactive import from a complete JSON file."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        sys.exit(1)

    with open(path) as f:
        entry = json.load(f)

    # Validate required fields
    missing = [f for f in REQUIRED_FIELDS if f not in entry]
    if missing:
        print(f"ERROR: Import JSON missing required fields: {', '.join(missing)}")
        sys.exit(1)

    missing_metrics = [f for f in REQUIRED_METRICS if f not in entry["metrics"]]
    if missing_metrics:
        print(
            f"ERROR: Import JSON metrics missing required fields: {', '.join(missing_metrics)}"
        )
        sys.exit(1)

    # Run full validation (type, range, hypothesis)
    errors, warnings = validate_entry(entry)

    # Print warnings
    for w in warnings:
        print(f"  WARNING: {w}")

    # Print errors and bail if any
    if errors:
        print()
        for e in errors:
            print(f"  ERROR: {e}")
        print(f"\n  {len(errors)} error(s) found. Import aborted.")
        sys.exit(1)

    if dry_run:
        m = entry["metrics"]
        print(f"\n  DRY RUN — would import:")
        print(f"    Project: {entry['project']}")
        print(f"    Sprint:  {entry['sprint']}")
        print(f"    Label:   {entry['label']}")
        print(f"    Phase:   {entry['phase']}")
        print(f"    Active:  {m['active_session_time_display']}")
        print(
            f"    Tokens:  {m['total_tokens_display']} total, {m['new_work_tokens_display']} new-work"
        )
        print(f"    Tests:   {m['tests_total']} (+{m.get('tests_added', '?')})")
        print(f"    LOC:     {m['loc_added']}")
        print(
            f"    Gates:   {'N/A' if m['gates_first_pass'] is None else 'first pass' if m['gates_first_pass'] else 'needed fixes'}"
        )
        print(f"    Hypotheses: {len(entry['hypotheses'])}")
        # Eval fields
        if m.get("task_type"):
            print(f"    Task type: {m['task_type']}")
        if m.get("rework_rate") is not None:
            print(f"    Rework rate: {m['rework_rate']}")
        js = m.get("judge_score")
        if js is not None:
            avg = sum(js) / len(js)
            print(f"    Judge score: {js} (avg {avg:.1f})")
            print(f"    Judge blocked: {m.get('judge_blocked', False)}")
            if m.get("judge_block_reason"):
                print(f"    Judge reason: {m['judge_block_reason']}")
        cri = m.get("coderabbit_issues")
        if cri is not None:
            criv = m.get("coderabbit_issues_valid", "?")
            print(f"    CodeRabbit: {criv}/{cri} valid")
        if m.get("mutation_score_pct") is not None:
            print(f"    Mutation score: {m['mutation_score_pct']}%")
        if m.get("delegation_ratio_pct") is not None:
            print(f"    Delegation ratio: {m['delegation_ratio_pct']}%")
        if m.get("context_compressions") is not None:
            print(f"    Context compressions: {m['context_compressions']}")
        if warnings:
            print(f"    Auto-corrections: {len(warnings)}")
        print(f"\n  Validation passed. Run without --dry-run to import.")
        return

    sprints_path, data = load_sprints_json()

    # Clear example data on first real import
    if data["sprints"] and all(s.get("example") for s in data["sprints"]):
        print("  Cleared example data from sprints.json.")
        data["sprints"] = []
        if "_example_data" in data:
            del data["_example_data"]

    check_duplicate(data, entry["project"], entry["sprint"])

    data["sprints"].append(entry)
    save_sprints_json(sprints_path, data)

    # Archive the import JSON
    archive_name = archive_import_json(path, entry)

    label = entry["label"]
    print(
        f"\n  Imported {label} to sprints.json ({len(data['sprints'])} total sprints)."
    )
    print(f"  Source: {path}")
    print(f"  Archived: imports/{archive_name}")
    if warnings:
        print(f"  Auto-corrections applied: {len(warnings)}")
    print(f"\n  Next steps:")
    print(f"    1. Review: cat sprints.json | python3 -m json.tool | tail -50")
    print(f"    2. Update RESULTS.md with sprint notes")


def load_json_report(project, sprint_num):
    path = os.path.expanduser(
        f"~/.flowstate/{project}/metrics/sprint-{sprint_num}-report.json"
    )
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        print(f"  Did the project agent run: collect.sh --json <session-id>?")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def parse_hypotheses(project, sprint_num):
    path = os.path.expanduser(
        f"~/.flowstate/{project}/retrospectives/sprint-{sprint_num}.md"
    )
    if not os.path.exists(path):
        print(f"WARNING: {path} not found. Skipping hypothesis parsing.")
        return []

    with open(path) as f:
        content = f.read()

    hypotheses = []
    in_table = False
    header_cols = []

    for line in content.split("\n"):
        stripped = line.strip()

        if (
            not in_table
            and "|" in stripped
            and "Hypothesis" in stripped
            and "Result" in stripped
        ):
            header_cols = [c.strip() for c in stripped.split("|")]
            in_table = True
            continue

        if in_table and re.match(r"^\|[\s\-|]+\|$", stripped):
            continue

        if in_table and stripped.startswith("|") and stripped.endswith("|"):
            cols = [c.strip() for c in stripped.split("|")]

            id_idx = None
            name_idx = None
            result_idx = None
            evidence_idx = None

            for i, h in enumerate(header_cols):
                if h == "#":
                    id_idx = i
                elif h == "Hypothesis":
                    name_idx = i
                elif h == "Result":
                    result_idx = i
                elif h == "Evidence":
                    evidence_idx = i

            if id_idx is not None and len(cols) > max(
                filter(None, [id_idx, name_idx, result_idx, evidence_idx])
            ):
                h_id = cols[id_idx].strip("*").strip()
                if not h_id or h_id == "NEW":
                    continue

                result_raw = (
                    cols[result_idx].strip("*").strip().lower() if result_idx else ""
                )
                normalized = normalize_result(result_raw)
                result = normalized if normalized else result_raw

                hypotheses.append(
                    {
                        "id": h_id,
                        "name": cols[name_idx].strip("*").strip() if name_idx else "",
                        "result": result,
                        "evidence": cols[evidence_idx].strip() if evidence_idx else "",
                    }
                )
        elif in_table and not stripped.startswith("|"):
            break

    return hypotheses


def prompt_field(name, description, default=None, type_fn=str):
    prompt_str = f"  {name}"
    if description:
        prompt_str += f" ({description})"
    if default is not None:
        prompt_str += f" [{default}]"
    prompt_str += ": "

    val = input(prompt_str).strip()
    if not val and default is not None:
        return default
    if not val:
        return None
    return type_fn(val)


def prompt_bool(name, description, default=None):
    prompt_str = f"  {name}"
    if description:
        prompt_str += f" ({description})"
    if default is not None:
        prompt_str += f" [{'y' if default else 'n'}]"
    prompt_str += " (y/n): "

    val = input(prompt_str).strip().lower()
    if not val and default is not None:
        return default
    return val in ("y", "yes", "true", "1")


def interactive_import(project, sprint_num):
    """Original interactive import mode."""
    sprints_path, data = load_sprints_json()
    check_duplicate(data, project, sprint_num)

    print(f"\nImporting {project} sprint {sprint_num}...")
    json_report = load_json_report(project, sprint_num)

    print(f"\n  Automated metrics from collect.sh:")
    print(f"    Active time: {json_report['active_session_time_display']}")
    print(f"    Total tokens: {json_report['total_tokens_display']}")
    print(f"    New-work tokens: {json_report['new_work_tokens_display']}")
    print(
        f"    Model mix: {json_report['opus_pct']}% opus, {json_report['sonnet_pct']}% sonnet, {json_report['haiku_pct']}% haiku"
    )
    print(
        f"    Subagents: {json_report['subagents']}, API calls: {json_report['api_calls']}"
    )

    hypotheses = parse_hypotheses(project, sprint_num)
    if hypotheses:
        print(f"\n  Parsed {len(hypotheses)} hypotheses from retro:")
        for h in hypotheses:
            print(f"    {h['id']}: {h['result']}")

    print(f"\n  Enter fields not available from collect.sh:")
    label = prompt_field("label", "e.g., 'Uluka S4' or 'DS S2'")
    phase = prompt_field("phase", "e.g., 'Phase 17: Claude Code Hook Integration'")
    tests_total = prompt_field(
        "tests_total", "total test count after sprint", type_fn=int
    )
    tests_added = prompt_field(
        "tests_added", "tests added this sprint, or blank", type_fn=int
    )
    coverage_pct = prompt_field("coverage_pct", "e.g., 70.22", type_fn=float)
    lint_errors = prompt_field(
        "lint_errors", "lint error count after sprint", type_fn=int
    )
    gates_first_pass = prompt_bool(
        "gates_first_pass", "did all gates pass on first try?"
    )
    gates_note = None
    if not gates_first_pass:
        gates_note = prompt_field("gates_first_pass_note", "what failed?")
    loc_added = prompt_field("loc_added", "lines of code added", type_fn=int)
    loc_approx = prompt_bool("loc_added_approx", "is LOC approximate?", default=False)

    entry = {
        "project": project,
        "sprint": sprint_num,
        "label": label,
        "phase": phase,
        "metrics": {
            "active_session_time_s": json_report["active_session_time_s"],
            "active_session_time_display": json_report["active_session_time_display"],
            "total_tokens": json_report["total_tokens"],
            "total_tokens_display": json_report["total_tokens_display"],
            "new_work_tokens": json_report["new_work_tokens"],
            "new_work_tokens_display": json_report["new_work_tokens_display"],
            "cache_hit_rate_pct": json_report.get("cache_hit_rate_pct"),
            "delegation_ratio_pct": json_report.get("delegation_ratio_pct"),
            "orchestrator_tokens": json_report.get("orchestrator_tokens"),
            "subagent_tokens": json_report.get("subagent_tokens"),
            "context_compressions": json_report.get("context_compressions"),
            "opus_pct": json_report["opus_pct"],
            "sonnet_pct": json_report["sonnet_pct"],
            "haiku_pct": json_report["haiku_pct"],
            "subagents": json_report["subagents"],
            "subagent_note": json_report.get("subagent_note"),
            "api_calls": json_report["api_calls"],
            "tests_total": tests_total,
            "tests_added": tests_added,
            "coverage_pct": coverage_pct,
            "lint_errors": lint_errors,
            "gates_first_pass": gates_first_pass,
            "gates_first_pass_note": gates_note,
            "loc_added": loc_added,
            "loc_added_approx": loc_approx,
        },
        "hypotheses": hypotheses,
    }

    # Validate
    errors, warnings = validate_entry(entry)
    for w in warnings:
        print(f"  WARNING: {w}")
    if errors:
        print()
        for e in errors:
            print(f"  ERROR: {e}")
        print(f"\n  {len(errors)} validation error(s). Fix and retry.")
        sys.exit(1)

    data["sprints"].append(entry)
    save_sprints_json(sprints_path, data)

    print(f"\n  Added {label} to sprints.json ({len(data['sprints'])} total sprints).")
    print(f"\n  Next steps:")
    print(f"    1. Review: cat sprints.json | python3 -m json.tool | tail -50")
    print(f"    2. Update RESULTS.md with sprint notes")


def main():
    args = sys.argv[1:]

    # --from mode
    if args and args[0] == "--from":
        args = args[1:]
        dry_run = False
        if args and args[0] == "--dry-run":
            dry_run = True
            args = args[1:]
        if not args:
            print("ERROR: --from requires a path to an import JSON file.")
            print()
            print("Usage:")
            print("  python3 import_sprint.py --from [--dry-run] <import-json>")
            sys.exit(1)
        import_from_file(args[0], dry_run=dry_run)
        return

    # Interactive mode
    if len(args) == 2 and args[0] != "--from":
        project = args[0]
        sprint_num = int(args[1])
        interactive_import(project, sprint_num)
        return

    print("Usage:")
    print("  python3 import_sprint.py --from [--dry-run] <import-json>")
    print("  python3 import_sprint.py <project> <sprint-number>")
    print()
    print("Examples:")
    print(
        "  python3 import_sprint.py --from ~/.flowstate/uluka/metrics/sprint-6-import.json"
    )
    print(
        "  python3 import_sprint.py --from --dry-run ~/.flowstate/uluka/metrics/sprint-7-import.json"
    )
    print("  python3 import_sprint.py uluka 4")
    sys.exit(1)


if __name__ == "__main__":
    main()
