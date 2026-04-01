#!/usr/bin/env python3
"""Migrate sprints.json to DuckDB and create the v1.2 schema.

Usage:
    python3 tools/migrate_to_duckdb.py [--db PATH] [--append-only]

Options:
    --db PATH       DuckDB file path (default: ~/.flowstate/flowstate.duckdb)
    --append-only   Only insert sprints not already in the DB (skip schema recreation)
"""

import json
import os
import re
import sys

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. Run: pip install duckdb")
    sys.exit(1)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.expanduser("~/.flowstate/flowstate.duckdb")
SPRINTS_JSON = os.path.join(REPO_ROOT, "sprints.json")


# --- Composite Score ---


def composite_score(m):
    """Compute composite score from sprint metrics. Returns 0-1, higher is better."""
    # Quality (0.40): gates first pass
    gates = m.get("gates_first_pass")
    quality = 1.0 if gates is True else (0.0 if gates is False else 0.5)

    # Token efficiency (0.30): tokens/LOC, 1000 t/LOC = 0
    nw = m.get("new_work_tokens")
    loc = m.get("loc_added") or 0
    if nw and loc > 0:
        tokens_per_loc = nw / loc
        token_score = max(0.0, 1.0 - (tokens_per_loc / 1000))
    else:
        token_score = 0.5  # unknown

    # Time (0.15): session time, 3600s = 0
    time_s = m.get("active_session_time_s")
    if time_s is not None:
        time_score = max(0.0, 1.0 - (time_s / 3600))
    else:
        time_score = 0.5  # unknown

    # Autonomy (0.15): context compressions as proxy
    compressions = m.get("context_compressions") or 0
    autonomy = max(0.0, 1.0 - (compressions / 5))

    return round(
        0.40 * quality + 0.30 * token_score + 0.15 * time_score + 0.15 * autonomy,
        4,
    )


# --- Schema ---


SCHEMA_SQL = """
-- Sequences
CREATE SEQUENCE IF NOT EXISTS sprint_seq START 1;
CREATE SEQUENCE IF NOT EXISTS lesson_seq START 1;
CREATE SEQUENCE IF NOT EXISTS gf_seq START 1;

-- Sprints
CREATE TABLE IF NOT EXISTS sprints (
    id                      INTEGER PRIMARY KEY DEFAULT (nextval('sprint_seq')),
    project                 VARCHAR NOT NULL,
    sprint                  INTEGER NOT NULL,
    label                   VARCHAR NOT NULL,
    phase                   VARCHAR NOT NULL,
    -- timing
    active_session_time_s   INTEGER,
    active_session_time_display VARCHAR,
    -- tokens
    total_tokens            BIGINT,
    total_tokens_display    VARCHAR,
    new_work_tokens         BIGINT,
    new_work_tokens_display VARCHAR,
    cache_hit_rate_pct      DOUBLE,
    opus_pct                DOUBLE,
    sonnet_pct              DOUBLE,
    haiku_pct               DOUBLE,
    -- delegation
    subagents               INTEGER,
    api_calls               INTEGER,
    delegation_ratio_pct    DOUBLE,
    orchestrator_tokens     BIGINT,
    subagent_tokens         BIGINT,
    context_compressions    INTEGER,
    -- quality
    tests_total             INTEGER,
    tests_added             INTEGER,
    coverage_pct            DOUBLE,
    lint_errors             INTEGER,
    gates_first_pass        BOOLEAN,
    gates_first_pass_note   VARCHAR,
    loc_added               INTEGER,
    loc_added_approx        BOOLEAN DEFAULT FALSE,
    -- eval
    task_type               VARCHAR,
    rework_rate             DOUBLE,
    judge_score             VARCHAR,
    judge_blocked           BOOLEAN,
    judge_block_reason      VARCHAR,
    coderabbit_issues       INTEGER,
    coderabbit_issues_valid INTEGER,
    mutation_score_pct      DOUBLE,
    -- v1.2
    composite_score         DOUBLE,
    experiment_id           VARCHAR,
    -- hypotheses stored as JSON string
    hypotheses              VARCHAR,
    -- metadata
    imported_at             TIMESTAMP DEFAULT current_timestamp,
    UNIQUE(project, sprint)
);

-- Lessons (cross-project autolearning)
CREATE TABLE IF NOT EXISTS lessons (
    id              INTEGER PRIMARY KEY DEFAULT (nextval('lesson_seq')),
    text            VARCHAR NOT NULL,
    category        VARCHAR NOT NULL,
    source_project  VARCHAR NOT NULL,
    source_sprint   INTEGER NOT NULL,
    times_applied   INTEGER DEFAULT 0,
    times_helped    INTEGER DEFAULT 0,
    confidence      DOUBLE DEFAULT 0.5,
    status          VARCHAR DEFAULT 'active',
    superseded_by   INTEGER,
    created_at      TIMESTAMP DEFAULT current_timestamp,
    last_applied_at TIMESTAMP
);

-- Gate failures
CREATE TABLE IF NOT EXISTS gate_failures (
    id              INTEGER PRIMARY KEY DEFAULT (nextval('gf_seq')),
    project         VARCHAR NOT NULL,
    sprint          INTEGER NOT NULL,
    gate_type       VARCHAR NOT NULL,
    error_summary   VARCHAR NOT NULL,
    error_detail    VARCHAR,
    fix_applied     VARCHAR,
    created_at      TIMESTAMP DEFAULT current_timestamp
);

-- Experiments (hill-climbing)
CREATE TABLE IF NOT EXISTS experiments (
    id              VARCHAR PRIMARY KEY,
    hypothesis      VARCHAR NOT NULL,
    mutation_type   VARCHAR NOT NULL,
    mutation_diff   VARCHAR NOT NULL,
    baseline_score  DOUBLE NOT NULL,
    result_score    DOUBLE,
    status          VARCHAR DEFAULT 'running',
    sprints_tested  INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT current_timestamp,
    completed_at    TIMESTAMP
);

-- Analytics view
CREATE OR REPLACE VIEW sprint_analytics AS
SELECT
    *,
    CASE WHEN loc_added > 0 AND new_work_tokens IS NOT NULL
         THEN new_work_tokens::DOUBLE / loc_added
         ELSE NULL
    END AS tokens_per_loc,
    CASE WHEN active_session_time_s IS NOT NULL
         THEN active_session_time_s / 60.0
         ELSE NULL
    END AS active_minutes,
    AVG(composite_score) OVER (
        PARTITION BY project ORDER BY sprint
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS rolling_score_5
FROM sprints;
"""


def classify_gate_failure(note):
    """Parse gates_first_pass_note into (gate_type, error_summary)."""
    if not note:
        return None, None
    note_lower = note.lower()
    if any(w in note_lower for w in ["lint", "ruff", "mypy", "biome", "swiftlint",
                                      "eslint", "clippy", "golangci", "unused import",
                                      "line_length", "identifier_name", "type_body_length"]):
        return "lint", note[:200]
    if any(w in note_lower for w in ["test fail", "assertion", "expect", "typeerror",
                                      "compile error", "build fail"]):
        return "test", note[:200]
    if "coverage" in note_lower:
        return "coverage", note[:200]
    if "build" in note_lower:
        return "build", note[:200]
    return "test", note[:200]  # default to test


def create_schema(con, drop_existing=False):
    """Create the v1.2 schema."""
    if drop_existing:
        con.execute("DROP VIEW IF EXISTS sprint_analytics")
        con.execute("DROP TABLE IF EXISTS experiments")
        con.execute("DROP TABLE IF EXISTS gate_failures")
        con.execute("DROP TABLE IF EXISTS lessons")
        con.execute("DROP TABLE IF EXISTS sprints")
        con.execute("DROP SEQUENCE IF EXISTS sprint_seq")
        con.execute("DROP SEQUENCE IF EXISTS lesson_seq")
        con.execute("DROP SEQUENCE IF EXISTS gf_seq")
    con.execute(SCHEMA_SQL)


def insert_sprint(con, entry):
    """Insert a single sprint entry from sprints.json format."""
    m = entry.get("metrics", {})
    score = composite_score(m)
    hyp = json.dumps(entry.get("hypotheses", []))

    # Handle judge_score which can be array or null
    judge = m.get("judge_score")
    if isinstance(judge, list):
        judge = json.dumps(judge)
    elif judge is not None:
        judge = str(judge)

    con.execute(
        """INSERT INTO sprints (
            project, sprint, label, phase,
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
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (project, sprint) DO NOTHING""",
        [
            entry["project"], entry["sprint"], entry["label"], entry["phase"],
            m.get("active_session_time_s"), m.get("active_session_time_display"),
            m.get("total_tokens"), m.get("total_tokens_display"),
            m.get("new_work_tokens"), m.get("new_work_tokens_display"),
            m.get("cache_hit_rate_pct"), m.get("opus_pct"), m.get("sonnet_pct"), m.get("haiku_pct"),
            m.get("subagents"), m.get("api_calls"), m.get("delegation_ratio_pct"),
            m.get("orchestrator_tokens"), m.get("subagent_tokens"), m.get("context_compressions"),
            m.get("tests_total"), m.get("tests_added"), m.get("coverage_pct"), m.get("lint_errors"),
            m.get("gates_first_pass"), m.get("gates_first_pass_note"),
            m.get("loc_added"), m.get("loc_added_approx", False),
            m.get("task_type"), m.get("rework_rate"),
            judge, m.get("judge_blocked"), m.get("judge_block_reason"),
            m.get("coderabbit_issues"), m.get("coderabbit_issues_valid"), m.get("mutation_score_pct"),
            score, hyp,
        ],
    )


def backfill_gate_failures(con):
    """Extract gate failures from gates_first_pass_note for failed sprints."""
    rows = con.execute(
        """SELECT project, sprint, gates_first_pass_note
           FROM sprints
           WHERE gates_first_pass = false
             AND gates_first_pass_note IS NOT NULL
             AND gates_first_pass_note != ''"""
    ).fetchall()
    count = 0
    for project, sprint, note in rows:
        gate_type, summary = classify_gate_failure(note)
        if gate_type and summary:
            con.execute(
                """INSERT INTO gate_failures (project, sprint, gate_type, error_summary, error_detail)
                   VALUES (?, ?, ?, ?, ?)""",
                [project, sprint, gate_type, summary, note[:2000]],
            )
            count += 1
    return count


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Migrate sprints.json to DuckDB")
    parser.add_argument("--db", default=DEFAULT_DB, help="DuckDB file path")
    parser.add_argument("--append-only", action="store_true",
                        help="Only insert new sprints, don't recreate schema")
    args = parser.parse_args()

    db_path = os.path.expanduser(args.db)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if not os.path.exists(SPRINTS_JSON):
        print(f"ERROR: {SPRINTS_JSON} not found.")
        sys.exit(1)

    with open(SPRINTS_JSON) as f:
        data = json.load(f)

    sprints = [s for s in data["sprints"] if not s.get("example")]
    print(f"Found {len(sprints)} sprints in sprints.json")

    con = duckdb.connect(db_path)

    if args.append_only:
        create_schema(con, drop_existing=False)
    else:
        create_schema(con, drop_existing=True)

    inserted = 0
    for entry in sprints:
        try:
            insert_sprint(con, entry)
            inserted += 1
        except Exception as e:
            print(f"  WARN: {entry['project']} S{entry['sprint']}: {e}")

    # Back-fill gate failures
    gf_count = backfill_gate_failures(con)

    con.close()

    # Verify
    con = duckdb.connect(db_path, read_only=True)
    total = con.execute("SELECT COUNT(*) FROM sprints").fetchone()[0]
    projects = con.execute("SELECT COUNT(DISTINCT project) FROM sprints").fetchone()[0]
    gf_total = con.execute("SELECT COUNT(*) FROM gate_failures").fetchone()[0]
    avg_score = con.execute("SELECT ROUND(AVG(composite_score), 4) FROM sprints").fetchone()[0]

    print(f"\nMigration complete: {db_path}")
    print(f"  Sprints: {total} ({projects} projects)")
    print(f"  Gate failures back-filled: {gf_total}")
    print(f"  Avg composite score: {avg_score}")

    # Show per-project scores
    rows = con.execute(
        """SELECT project, COUNT(*) as n,
                  ROUND(AVG(composite_score), 3) as avg_score,
                  ROUND(MIN(composite_score), 3) as min_score,
                  ROUND(MAX(composite_score), 3) as max_score
           FROM sprints GROUP BY project ORDER BY n DESC"""
    ).fetchall()
    print(f"\n  {'Project':<25s} {'N':>3s}  {'Avg':>5s}  {'Min':>5s}  {'Max':>5s}")
    for row in rows:
        print(f"  {row[0]:<25s} {row[1]:3d}  {row[2]:5.3f}  {row[3]:5.3f}  {row[4]:5.3f}")

    con.close()


if __name__ == "__main__":
    main()
