#!/usr/bin/env python3
"""Flowstate Hill-Climbing Optimizer.

Automatically proposes, tests, and evaluates process mutations to improve
sprint outcomes. Inspired by Karpathy's autoresearch.

Usage:
    python3 tools/optimize.py propose [--db PATH]
    python3 tools/optimize.py evaluate [--db PATH]
    python3 tools/optimize.py status [--db PATH]

Commands:
    propose   - Analyze data, propose a mutation, create experiment branch
    evaluate  - Check running experiments, keep/revert based on results
    status    - Show current experiment state and score trends

The optimizer does NOT run sprints itself. It proposes mutations, and normal
sprint work generates the composite scores that feed back into evaluation.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. Run: pip install duckdb")
    sys.exit(1)

DEFAULT_DB = os.path.expanduser("~/.flowstate/flowstate.duckdb")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMPROVEMENT_THRESHOLD = 0.02  # 2% improvement to keep
MAX_SPRINTS_PER_EXPERIMENT = 6
MIN_SPRINTS_PER_EXPERIMENT = 3


def get_db(db_path, read_only=False):
    return duckdb.connect(db_path, read_only=read_only)


# --- Analysis ---


def get_baseline_score(con, last_n=10):
    """Get the baseline composite score (avg of last N sprints)."""
    row = con.execute(
        "SELECT AVG(composite_score) FROM (SELECT composite_score FROM sprints ORDER BY imported_at DESC LIMIT ?)",
        [last_n],
    ).fetchone()
    return round(row[0], 4) if row[0] else None


def get_top_gate_failures(con, limit=5):
    """Get most frequent gate failure patterns."""
    return con.execute(
        """SELECT gate_type, error_summary, COUNT(*) as freq
           FROM gate_failures
           GROUP BY gate_type, error_summary
           ORDER BY freq DESC LIMIT ?""",
        [limit],
    ).fetchall()


def get_worst_sprints(con, limit=5):
    """Get sprints with lowest composite scores."""
    return con.execute(
        """SELECT project, sprint, composite_score, gates_first_pass, task_type,
                  gates_first_pass_note
           FROM sprints
           WHERE composite_score IS NOT NULL
           ORDER BY composite_score ASC LIMIT ?""",
        [limit],
    ).fetchall()


def get_score_by_task_type(con):
    """Get avg composite score by task type."""
    return con.execute(
        """SELECT task_type, COUNT(*) n, ROUND(AVG(composite_score), 4) avg_score
           FROM sprints WHERE task_type IS NOT NULL
           GROUP BY task_type ORDER BY avg_score ASC"""
    ).fetchall()


def get_running_experiment(con):
    """Get the currently running experiment, if any."""
    row = con.execute(
        "SELECT * FROM experiments WHERE status = 'running' LIMIT 1"
    ).fetchone()
    if row:
        cols = [d[0] for d in con.description]
        return dict(zip(cols, row))
    return None


# --- Mutation Proposals ---


def propose_gate_mutation(con):
    """Propose a gate-related mutation based on failure patterns."""
    failures = get_top_gate_failures(con)
    if not failures:
        return None

    top = failures[0]
    gate_type, summary, freq = top

    if gate_type == "lint" and freq >= 3:
        return {
            "hypothesis": f"Adding lint pre-check instruction will reduce lint gate failures (currently {freq} occurrences of: {summary[:80]})",
            "mutation_type": "gate_config",
            "mutation_diff": "Lint pre-check is already in SKILL.md v1.2. This experiment tracks whether it reduces failures in practice.",
        }

    if gate_type == "test" and freq >= 3:
        return {
            "hypothesis": f"Adding 'run tests after each file change' instruction will catch test failures earlier (currently {freq} test failures)",
            "mutation_type": "process",
            "mutation_diff": "Add to EXECUTE section: 'Run the test suite after modifying each source file, not just at gate time.'",
        }

    return None


def propose_model_routing(con):
    """Propose a model routing change."""
    # Check if any projects use Sonnet successfully
    row = con.execute(
        """SELECT COUNT(*) as n, AVG(composite_score) as avg_score
           FROM sprints WHERE sonnet_pct > 20"""
    ).fetchone()

    if row[0] > 0 and row[1] and row[1] > 0.6:
        return {
            "hypothesis": f"Using Sonnet for mechanical subtasks (lint fixes, test generation) saves tokens without quality loss. {row[0]} sprints with >20% Sonnet avg score: {row[1]:.3f}",
            "mutation_type": "model_routing",
            "mutation_diff": "Set model routing: lint_fixes=sonnet, test_generation=sonnet, retro_writing=sonnet. Keep planning/architecture on opus.",
        }
    return None


def propose_score_weight_change(con):
    """Propose adjusting composite score weights."""
    # Check if quality weight is too dominant
    rows = con.execute(
        """SELECT
            AVG(CASE WHEN gates_first_pass THEN composite_score ELSE NULL END) as pass_avg,
            AVG(CASE WHEN NOT gates_first_pass THEN composite_score ELSE NULL END) as fail_avg,
            COUNT(CASE WHEN gates_first_pass THEN 1 END) as pass_n,
            COUNT(CASE WHEN NOT gates_first_pass THEN 1 END) as fail_n
           FROM sprints WHERE gates_first_pass IS NOT NULL"""
    ).fetchone()

    if rows and rows[0] and rows[1]:
        gap = rows[0] - rows[1]
        if gap > 0.4:
            return {
                "hypothesis": f"Quality weight (0.40) creates too large a gap between pass ({rows[0]:.3f}, n={rows[2]}) and fail ({rows[1]:.3f}, n={rows[3]}). Reduce to 0.30, increase token efficiency to 0.35.",
                "mutation_type": "score_weights",
                "mutation_diff": "Change composite_score weights: quality 0.40->0.30, token_efficiency 0.30->0.35, time 0.15->0.20, autonomy 0.15->0.15",
            }
    return None


def propose_mutation(con):
    """Propose the best mutation based on current data analysis."""
    # Priority order: gate failures first, then model routing, then weights
    proposals = [
        propose_gate_mutation(con),
        propose_model_routing(con),
        propose_score_weight_change(con),
    ]
    for p in proposals:
        if p:
            return p
    return None


# --- Experiment Lifecycle ---


def create_experiment(con, mutation):
    """Create a new experiment in the DB."""
    baseline = get_baseline_score(con)
    if baseline is None:
        print("ERROR: No baseline score available (no sprints in DB)")
        return None

    exp_id = f"exp-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    con.execute(
        """INSERT INTO experiments (id, hypothesis, mutation_type, mutation_diff, baseline_score)
           VALUES (?, ?, ?, ?, ?)""",
        [exp_id, mutation["hypothesis"], mutation["mutation_type"],
         mutation["mutation_diff"], baseline],
    )

    return {
        "id": exp_id,
        "baseline_score": baseline,
        **mutation,
    }


def evaluate_experiment(con, experiment):
    """Evaluate a running experiment against recent sprint scores."""
    exp_id = experiment["id"]
    baseline = experiment["baseline_score"]

    # Get sprints since experiment was created
    created_at = experiment["created_at"]
    rows = con.execute(
        """SELECT composite_score FROM sprints
           WHERE imported_at > ? AND composite_score IS NOT NULL
           ORDER BY imported_at""",
        [created_at],
    ).fetchall()

    sprints_tested = len(rows)
    if sprints_tested == 0:
        return {"status": "waiting", "sprints_tested": 0, "message": "No new sprints since experiment started"}

    avg_score = sum(r[0] for r in rows) / sprints_tested
    improvement = avg_score - baseline

    # Update sprints_tested count
    con.execute(
        "UPDATE experiments SET sprints_tested = ?, result_score = ? WHERE id = ?",
        [sprints_tested, round(avg_score, 4), exp_id],
    )

    if sprints_tested < MIN_SPRINTS_PER_EXPERIMENT:
        return {
            "status": "running",
            "sprints_tested": sprints_tested,
            "current_score": round(avg_score, 4),
            "baseline": baseline,
            "improvement": round(improvement, 4),
            "message": f"Need {MIN_SPRINTS_PER_EXPERIMENT - sprints_tested} more sprints for evaluation",
        }

    if improvement > IMPROVEMENT_THRESHOLD:
        con.execute(
            "UPDATE experiments SET status = 'kept', completed_at = current_timestamp WHERE id = ?",
            [exp_id],
        )
        return {
            "status": "kept",
            "sprints_tested": sprints_tested,
            "improvement": round(improvement, 4),
            "message": f"Experiment kept: +{improvement:.3f} improvement over {sprints_tested} sprints",
        }

    if improvement < -IMPROVEMENT_THRESHOLD:
        con.execute(
            "UPDATE experiments SET status = 'reverted', completed_at = current_timestamp WHERE id = ?",
            [exp_id],
        )
        return {
            "status": "reverted",
            "sprints_tested": sprints_tested,
            "improvement": round(improvement, 4),
            "message": f"Experiment reverted: {improvement:.3f} regression over {sprints_tested} sprints",
        }

    if sprints_tested >= MAX_SPRINTS_PER_EXPERIMENT:
        con.execute(
            "UPDATE experiments SET status = 'inconclusive', completed_at = current_timestamp WHERE id = ?",
            [exp_id],
        )
        return {
            "status": "inconclusive",
            "sprints_tested": sprints_tested,
            "improvement": round(improvement, 4),
            "message": f"Inconclusive after {sprints_tested} sprints ({improvement:+.3f}). Reverted.",
        }

    return {
        "status": "running",
        "sprints_tested": sprints_tested,
        "improvement": round(improvement, 4),
        "message": f"Running: {improvement:+.3f} over {sprints_tested} sprints. Need more data.",
    }


# --- Commands ---


def cmd_propose(db_path):
    """Propose a new experiment."""
    con = get_db(db_path)

    # Check for running experiment
    running = get_running_experiment(con)
    if running:
        print(f"Experiment already running: {running['id']}")
        print(f"  Hypothesis: {running['hypothesis']}")
        print(f"  Type: {running['mutation_type']}")
        print(f"  Baseline: {running['baseline_score']}")
        print(f"\nRun 'evaluate' to check its status.")
        con.close()
        return

    # Analyze and propose
    print("Analyzing sprint data...")
    baseline = get_baseline_score(con)
    print(f"  Baseline score (last 10): {baseline}")

    failures = get_top_gate_failures(con)
    if failures:
        print(f"  Top gate failures:")
        for gt, summary, freq in failures[:3]:
            print(f"    [{gt}] {summary[:60]} (x{freq})")

    worst = get_worst_sprints(con, 3)
    if worst:
        print(f"  Worst sprints:")
        for project, sprint, score, gates, task_type, note in worst:
            print(f"    {project} S{sprint}: {score:.3f} (gates={'pass' if gates else 'fail'}, {task_type})")

    task_scores = get_score_by_task_type(con)
    if task_scores:
        print(f"  Score by task type:")
        for tt, n, avg in task_scores:
            print(f"    {tt}: {avg:.3f} (n={n})")

    mutation = propose_mutation(con)
    if not mutation:
        print("\nNo mutation to propose. System is performing well or data is insufficient.")
        con.close()
        return

    print(f"\nProposed experiment:")
    print(f"  Type: {mutation['mutation_type']}")
    print(f"  Hypothesis: {mutation['hypothesis']}")
    print(f"  Change: {mutation['mutation_diff']}")

    experiment = create_experiment(con, mutation)
    if experiment:
        print(f"\n  Created: {experiment['id']}")
        print(f"  Baseline: {experiment['baseline_score']}")
        print(f"  Run {MIN_SPRINTS_PER_EXPERIMENT}-{MAX_SPRINTS_PER_EXPERIMENT} sprints, then 'evaluate'.")

    con.close()


def cmd_evaluate(db_path):
    """Evaluate the running experiment."""
    con = get_db(db_path)

    running = get_running_experiment(con)
    if not running:
        print("No running experiment. Run 'propose' to start one.")
        con.close()
        return

    print(f"Evaluating: {running['id']}")
    print(f"  Hypothesis: {running['hypothesis']}")
    print(f"  Baseline: {running['baseline_score']}")

    result = evaluate_experiment(con, running)
    print(f"\n  Status: {result['status']}")
    print(f"  Sprints tested: {result['sprints_tested']}")
    if "improvement" in result:
        print(f"  Improvement: {result['improvement']:+.4f}")
    print(f"  {result['message']}")

    con.close()


def cmd_status(db_path):
    """Show optimizer status."""
    con = get_db(db_path, read_only=True)

    baseline = get_baseline_score(con)
    print(f"Current baseline (last 10 sprints): {baseline}")

    # Running experiment
    running = get_running_experiment(con)
    if running:
        print(f"\nRunning experiment: {running['id']}")
        print(f"  Type: {running['mutation_type']}")
        print(f"  Hypothesis: {running['hypothesis'][:100]}")
        print(f"  Baseline: {running['baseline_score']}")
        print(f"  Sprints tested: {running['sprints_tested']}")
    else:
        print("\nNo running experiment.")

    # Past experiments
    rows = con.execute(
        """SELECT id, status, mutation_type, baseline_score, result_score, sprints_tested
           FROM experiments WHERE status != 'running'
           ORDER BY completed_at DESC LIMIT 10"""
    ).fetchall()
    if rows:
        print(f"\nPast experiments:")
        for eid, status, mtype, base, result, tested in rows:
            improvement = (result - base) if result else 0
            print(f"  {eid}: {status} ({mtype}) {improvement:+.3f} over {tested} sprints")

    # Score trend
    rows = con.execute(
        """SELECT project, sprint, composite_score
           FROM sprints ORDER BY imported_at DESC LIMIT 20"""
    ).fetchall()
    if rows:
        print(f"\nRecent scores:")
        for project, sprint, score in rows[:10]:
            bar = "#" * int(score * 20) if score else ""
            print(f"  {project:20s} S{sprint:2d}  {score:.3f}  {bar}")

    con.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Flowstate Hill-Climbing Optimizer")
    parser.add_argument("command", choices=["propose", "evaluate", "status"],
                        help="Command to run")
    parser.add_argument("--db", default=DEFAULT_DB, help="DuckDB file path")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: DuckDB not found at {args.db}. Run migrate_to_duckdb.py first.")
        sys.exit(1)

    if args.command == "propose":
        cmd_propose(args.db)
    elif args.command == "evaluate":
        cmd_evaluate(args.db)
    elif args.command == "status":
        cmd_status(args.db)


if __name__ == "__main__":
    main()
