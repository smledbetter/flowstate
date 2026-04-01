#!/usr/bin/env python3
"""Export DuckDB sprint data to JSON for the static dashboard.

Usage:
    python3 tools/export_dashboard.py [--db PATH] [--out PATH]

Writes a JSON file compatible with the dashboard's SprintsData type.
If DuckDB is not available, falls back to sprints.json.
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.expanduser("~/.flowstate/flowstate.duckdb")
DEFAULT_OUT = os.path.join(REPO_ROOT, "dashboard", "src", "data", "sprints-export.json")


def export_from_duckdb(db_path):
    """Export all sprints from DuckDB as a sprints.json-compatible structure."""
    import duckdb

    con = duckdb.connect(db_path, read_only=True)

    rows = con.execute(
        """SELECT project, sprint, label, phase,
                  active_session_time_s, active_session_time_display,
                  total_tokens, total_tokens_display,
                  new_work_tokens, new_work_tokens_display,
                  cache_hit_rate_pct, opus_pct, sonnet_pct, haiku_pct,
                  subagents, api_calls, delegation_ratio_pct,
                  orchestrator_tokens, subagent_tokens, context_compressions,
                  tests_total, tests_added, coverage_pct, lint_errors,
                  gates_first_pass, gates_first_pass_note,
                  loc_added, loc_added_approx,
                  task_type, rework_rate,
                  judge_score, judge_blocked, judge_block_reason,
                  coderabbit_issues, coderabbit_issues_valid, mutation_score_pct,
                  composite_score, hypotheses
           FROM sprints ORDER BY project, sprint"""
    ).fetchall()

    cols = [
        "project", "sprint", "label", "phase",
        "active_session_time_s", "active_session_time_display",
        "total_tokens", "total_tokens_display",
        "new_work_tokens", "new_work_tokens_display",
        "cache_hit_rate_pct", "opus_pct", "sonnet_pct", "haiku_pct",
        "subagents", "api_calls", "delegation_ratio_pct",
        "orchestrator_tokens", "subagent_tokens", "context_compressions",
        "tests_total", "tests_added", "coverage_pct", "lint_errors",
        "gates_first_pass", "gates_first_pass_note",
        "loc_added", "loc_added_approx",
        "task_type", "rework_rate",
        "judge_score", "judge_blocked", "judge_block_reason",
        "coderabbit_issues", "coderabbit_issues_valid", "mutation_score_pct",
        "composite_score", "hypotheses",
    ]

    sprints = []
    for row in rows:
        entry = dict(zip(cols, row))
        # Separate metrics from top-level fields
        top_keys = {"project", "sprint", "label", "phase", "composite_score", "hypotheses"}
        metrics = {k: v for k, v in entry.items() if k not in top_keys}
        sprint = {
            "project": entry["project"],
            "sprint": entry["sprint"],
            "label": entry["label"],
            "phase": entry["phase"],
            "metrics": metrics,
            "composite_score": entry["composite_score"],
            "hypotheses": json.loads(entry["hypotheses"]) if entry["hypotheses"] else [],
        }
        sprints.append(sprint)

    con.close()
    return {
        "_note": f"Exported from DuckDB. {len(sprints)} sprints.",
        "sprints": sprints,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Export DuckDB to dashboard JSON")
    parser.add_argument("--db", default=DEFAULT_DB, help="DuckDB file path")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output JSON path")
    args = parser.parse_args()

    db_path = os.path.expanduser(args.db)

    if os.path.exists(db_path):
        try:
            data = export_from_duckdb(db_path)
            print(f"Exported {len(data['sprints'])} sprints from DuckDB")
        except Exception as e:
            print(f"DuckDB export failed ({e}), falling back to sprints.json")
            with open(os.path.join(REPO_ROOT, "sprints.json")) as f:
                data = json.load(f)
    else:
        print(f"DuckDB not found at {db_path}, falling back to sprints.json")
        with open(os.path.join(REPO_ROOT, "sprints.json")) as f:
            data = json.load(f)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"Written to {args.out}")


if __name__ == "__main__":
    main()
