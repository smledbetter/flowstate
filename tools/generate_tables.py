#!/usr/bin/env python3
"""Generate markdown tables from sprints.json.

Usage:
    python3 generate_tables.py sprint <project> <sprint-number>
    python3 generate_tables.py compare <project> <sprint-numbers...>
    python3 generate_tables.py cross-project
    python3 generate_tables.py tokens-per-loc
    python3 generate_tables.py efficiency-by-type
    python3 generate_tables.py eval-effectiveness
    python3 generate_tables.py hypotheses <project> <sprint-number>

All output goes to stdout as markdown tables. Copy-paste into RESULTS.md.
"""

import json
import os
import sys


def load_data(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sprints.json")
    with open(path) as f:
        return json.load(f)


def find_sprint(data, project, sprint_num):
    for s in data["sprints"]:
        if s["project"] == project and s["sprint"] == sprint_num:
            return s
    return None


def fmt_bool(val, note=None):
    if val is None:
        return "---"
    s = "yes" if val else "no"
    if note:
        s += f" ({note})"
    return s


def fmt_val(val, suffix=""):
    if val is None:
        return "---"
    return f"{val}{suffix}"


def fmt_pct(val):
    if val is None:
        return "---"
    return f"{val}%"


def fmt_tests(s):
    m = s["metrics"]
    total = m.get("tests_total")
    added = m.get("tests_added")
    if total is None:
        return "---"
    if added is not None:
        return f"{total} (+{added})"
    note = m.get("tests_note")
    if note:
        return note
    return str(total)


def sprint_table(data, project, sprint_num):
    s = find_sprint(data, project, sprint_num)
    if not s:
        print(f"Sprint not found: {project} {sprint_num}", file=sys.stderr)
        sys.exit(1)
    m = s["metrics"]
    rows = [
        ("Active session time", m["active_session_time_display"]),
        ("Total tokens", m["total_tokens_display"]),
        ("Opus % (tokens)", fmt_pct(m["opus_pct"])),
        ("Sonnet % (tokens)", fmt_pct(m["sonnet_pct"])),
        ("Haiku % (tokens)", fmt_pct(m["haiku_pct"])),
        (
            "Subagents",
            fmt_val(
                m["subagents"],
                f" ({m['subagent_note']})" if m.get("subagent_note") else "",
            ),
        ),
        ("API calls", fmt_val(m["api_calls"])),
        ("Tests", fmt_tests(s)),
        ("Coverage", fmt_pct(m.get("coverage_pct"))),
        ("Lint errors", fmt_val(m.get("lint_errors"))),
        (
            "Gates first pass",
            fmt_bool(m["gates_first_pass"], m.get("gates_first_pass_note")),
        ),
    ]
    if m.get("loc_added") is not None:
        prefix = "~" if m.get("loc_added_approx") else ""
        loc_str = f"{prefix}{m['loc_added']:,}"
        if m.get("loc_note"):
            loc_str += f" ({m['loc_note']})"
        rows.append(
            ("Rust LOC" if project == "dappled-shade" else "Insertions", loc_str)
        )
    if m.get("task_type"):
        rows.append(("Task type", m["task_type"]))
    if m.get("rework_rate") is not None:
        rows.append(("Rework rate", str(m["rework_rate"])))

    print("| Metric | Value |")
    print("|--------|-------|")
    for label, val in rows:
        print(f"| {label} | {val} |")


def compare_table(data, project, sprint_nums):
    sprints = []
    for n in sprint_nums:
        s = find_sprint(data, project, n)
        if not s:
            print(f"Sprint not found: {project} {n}", file=sys.stderr)
            sys.exit(1)
        sprints.append(s)

    # Metric rows to show
    metric_keys = [
        ("Active session time", lambda m: m["active_session_time_display"]),
        ("Total tokens", lambda m: m["total_tokens_display"]),
        ("New-work tokens", lambda m: m.get("new_work_tokens_display", "---")),
        ("Opus % (tokens)", lambda m: fmt_pct(m["opus_pct"])),
        ("Sonnet % (tokens)", lambda m: fmt_pct(m["sonnet_pct"])),
        ("Haiku % (tokens)", lambda m: fmt_pct(m["haiku_pct"])),
        (
            "Subagents",
            lambda m: fmt_val(
                m["subagents"],
                f" ({m['subagent_note']})" if m.get("subagent_note") else "",
            ),
        ),
        ("API calls", lambda m: fmt_val(m["api_calls"])),
        ("Tests", lambda s_obj: fmt_tests(s_obj)),
        ("Coverage", lambda m: fmt_pct(m.get("coverage_pct"))),
        ("Lint errors", lambda m: fmt_val(m.get("lint_errors"))),
        (
            "Gates first pass",
            lambda m: fmt_bool(m["gates_first_pass"], m.get("gates_first_pass_note")),
        ),
        (
            "Insertions",
            lambda m: (
                f"{'~' if m.get('loc_added_approx') else ''}{m['loc_added']:,}"
                if m.get("loc_added") is not None
                else "---"
            ),
        ),
    ]

    # Header
    headers = ["Metric"] + [f"Sprint {s['sprint']}" for s in sprints]
    if len(sprints) >= 2:
        headers.append(f"Delta (S{sprints[-2]['sprint']}->S{sprints[-1]['sprint']})")
    sep = ["-" * max(6, len(h)) for h in headers]

    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(sep) + " |")

    for label, getter in metric_keys:
        vals = []
        for s in sprints:
            # Tests row needs the full sprint object, not just metrics
            if label == "Tests":
                vals.append(getter(s))
            else:
                vals.append(getter(s["metrics"]))
        row = [label] + vals
        if len(sprints) >= 2:
            row.append("")  # Delta left empty — editorial content
        print("| " + " | ".join(str(v) for v in row) + " |")


def cross_project_table(data):
    # Build order dynamically: all sprints grouped by project, sorted by sprint number
    by_project = {}
    for s in data["sprints"]:
        by_project.setdefault(s["project"], []).append(s)
    # Sort each project's sprints by number
    for proj in by_project:
        by_project[proj].sort(key=lambda s: s["sprint"])
    # Project display order: uluka first, then dappled-shade, then any others alphabetically
    project_order = []
    for p in ["uluka", "dappled-shade"]:
        if p in by_project:
            project_order.append(p)
    for p in sorted(by_project.keys()):
        if p not in project_order:
            project_order.append(p)
    sprints = []
    for proj in project_order:
        sprints.extend(by_project[proj])

    headers = [""] + [s["label"] for s in sprints] + ["Trend"]
    sep = ["-" * max(3, len(h)) for h in headers]

    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(s + "--" for s in sep) + "|")

    rows = [
        ("Active session time", lambda m: m["active_session_time_display"]),
        ("Total tokens", lambda m: m["total_tokens_display"]),
        ("New-work tokens", lambda m: m.get("new_work_tokens_display", "---")),
        ("Opus % (tokens)", lambda m: fmt_pct(m["opus_pct"])),
        ("Sonnet % (tokens)", lambda m: fmt_pct(m["sonnet_pct"])),
        ("Haiku % (tokens)", lambda m: fmt_pct(m["haiku_pct"])),
        (
            "Subagents",
            lambda m: fmt_val(
                m["subagents"],
                f" ({m['subagent_note']})" if m.get("subagent_note") else "",
            ),
        ),
        ("API calls", lambda m: fmt_val(m["api_calls"])),
        (
            "Gates 1st pass",
            lambda m: fmt_bool(m["gates_first_pass"], m.get("gates_first_pass_note")),
        ),
        ("H7 compliance", None),  # special
        ("Tokens/LOC (new-work)", None),  # special
        ("Task type", lambda m: fmt_val(m.get("task_type"))),
        ("Rework rate", lambda m: fmt_val(m.get("rework_rate"))),
    ]

    for label, getter in rows:
        vals = []
        for s in sprints:
            if label == "H7 compliance":
                # Extract from hypotheses
                h7 = next((h for h in s["hypotheses"] if h["id"] == "H7"), None)
                if h7:
                    ev = h7["evidence"]
                    # Try to extract X/5 pattern
                    import re

                    match = re.search(r"(\d+(?:\.\d+)?/5)", ev)
                    vals.append(match.group(1) if match else h7["result"])
                else:
                    vals.append("---")
            elif label == "Tokens/LOC (new-work)":
                m = s["metrics"]
                nw = m.get("new_work_tokens")
                loc = m.get("loc_added")
                if nw and loc and loc > 0:
                    vals.append(f"~{nw // loc}")
                else:
                    vals.append("---")
            else:
                vals.append(getter(s["metrics"]))
        row = [label] + vals + [""]  # Empty trend column (editorial)
        print("| " + " | ".join(str(v) for v in row) + " |")


def tokens_per_loc_table(data):
    headers = [
        "Sprint",
        "Total Tokens",
        "New-work Tokens",
        "LOC Added",
        "Tokens/LOC (total)",
        "Tokens/LOC (new-work)",
    ]
    sep = ["-" * len(h) for h in headers]

    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(sep) + " |")

    for s in data["sprints"]:
        m = s["metrics"]
        loc = m.get("loc_added")
        total = m.get("total_tokens")
        new_work = m.get("new_work_tokens")

        loc_str = f"{'~' if m.get('loc_added_approx') else ''}{loc:,}" if loc else "---"
        tloc = f"~{total // loc:,}" if total and loc and loc > 0 else "---"
        nwloc = f"~{new_work // loc}" if new_work and loc and loc > 0 else "---"

        print(
            f"| {s['label']} | {m['total_tokens_display']} | {m.get('new_work_tokens_display', '---')} | {loc_str} | {tloc} | {nwloc} |"
        )


def hypotheses_table(data, project, sprint_num):
    s = find_sprint(data, project, sprint_num)
    if not s:
        print(f"Sprint not found: {project} {sprint_num}", file=sys.stderr)
        sys.exit(1)

    print("| # | Hypothesis | Result | Evidence |")
    print("|---|-----------|--------|----------|")
    for h in s["hypotheses"]:
        result = h["result"].replace("_", " ").title()
        # Keep "Partially Confirmed" readable
        if h["result"] == "partially_confirmed":
            result = "Partially confirmed"
        elif h["result"] == "confirmed":
            result = "Confirmed"
        elif h["result"] == "inconclusive":
            result = "Inconclusive"
        elif h["result"] == "falsified":
            result = "Falsified"
        print(f"| {h['id']} | {h['name']} | {result} | {h['evidence']} |")


def efficiency_by_type_table(data):
    """Group sprints by task_type and show avg tokens/LOC per type."""
    from collections import defaultdict

    by_type = defaultdict(list)
    for s in data["sprints"]:
        tt = s["metrics"].get("task_type")
        if not tt:
            continue
        m = s["metrics"]
        nw = m.get("new_work_tokens")
        loc = m.get("loc_added")
        if nw and loc and loc > 0:
            by_type[tt].append({"label": s["label"], "nw": nw, "loc": loc})

    if not by_type:
        print("No sprints with task_type data yet.")
        return

    headers = ["Task Type", "Sprints", "Avg Tokens/LOC (new-work)", "Range"]
    sep = ["-" * len(h) for h in headers]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(sep) + " |")

    for tt in sorted(by_type.keys()):
        entries = by_type[tt]
        ratios = [e["nw"] // e["loc"] for e in entries]
        avg = sum(ratios) // len(ratios)
        lo, hi = min(ratios), max(ratios)
        labels = ", ".join(e["label"] for e in entries)
        range_str = f"{lo}-{hi}" if lo != hi else str(lo)
        print(f"| {tt} | {len(entries)} ({labels}) | ~{avg} | {range_str} |")


def eval_effectiveness_table(data):
    """Show eval tool effectiveness across sprints."""
    # Only include sprints that have at least one eval field
    sprints = []
    for s in data["sprints"]:
        m = s["metrics"]
        has_eval = any(
            m.get(f) is not None
            for f in [
                "judge_score",
                "rework_rate",
                "coderabbit_issues",
                "mutation_score_pct",
            ]
        )
        if has_eval:
            sprints.append(s)

    if not sprints:
        print("No sprints with eval data yet.")
        return

    headers = [
        "Sprint",
        "Judge Avg",
        "Blocked?",
        "Rework Rate",
        "CR (valid/total)",
        "Mutation %",
    ]
    sep = ["-" * len(h) for h in headers]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(sep) + " |")

    for s in sprints:
        m = s["metrics"]
        # Judge
        js = m.get("judge_score")
        judge_avg = f"{sum(js) / len(js):.1f}" if js else "---"
        jb = m.get("judge_blocked")
        blocked = "yes" if jb else ("no" if jb is not None else "---")
        # Rework
        rw = m.get("rework_rate")
        rework = str(rw) if rw is not None else "---"
        # CodeRabbit
        cri = m.get("coderabbit_issues")
        criv = m.get("coderabbit_issues_valid")
        if cri is not None:
            cr = f"{criv if criv is not None else '?'}/{cri}"
        else:
            cr = "---"
        # Mutation
        msp = m.get("mutation_score_pct")
        mutation = f"{msp}%" if msp is not None else "---"

        print(
            f"| {s['label']} | {judge_avg} | {blocked} | {rework} | {cr} | {mutation} |"
        )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    data = load_data()

    if cmd == "sprint":
        if len(sys.argv) < 4:
            print(
                "Usage: generate_tables.py sprint <project> <sprint-number>",
                file=sys.stderr,
            )
            sys.exit(1)
        sprint_table(data, sys.argv[2], int(sys.argv[3]))

    elif cmd == "compare":
        if len(sys.argv) < 5:
            print(
                "Usage: generate_tables.py compare <project> <sprint-numbers...>",
                file=sys.stderr,
            )
            sys.exit(1)
        sprint_nums = [int(x) for x in sys.argv[3:]]
        compare_table(data, sys.argv[2], sprint_nums)

    elif cmd == "cross-project":
        cross_project_table(data)

    elif cmd == "tokens-per-loc":
        tokens_per_loc_table(data)

    elif cmd == "efficiency-by-type":
        efficiency_by_type_table(data)

    elif cmd == "eval-effectiveness":
        eval_effectiveness_table(data)

    elif cmd == "hypotheses":
        if len(sys.argv) < 4:
            print(
                "Usage: generate_tables.py hypotheses <project> <sprint-number>",
                file=sys.stderr,
            )
            sys.exit(1)
        hypotheses_table(data, sys.argv[2], int(sys.argv[3]))

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
