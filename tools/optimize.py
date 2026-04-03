#!/usr/bin/env python3
"""Flowstate Hill-Climbing Optimizer.

Automatically proposes, applies, tests, and evaluates process mutations
to improve sprint outcomes. Inspired by Karpathy's autoresearch.

Usage:
    python3 tools/optimize.py propose [--db PATH]
    python3 tools/optimize.py evaluate [--db PATH]
    python3 tools/optimize.py revert [--db PATH]
    python3 tools/optimize.py status [--db PATH]

Commands:
    propose   - Analyze data, propose a mutation, apply it to SKILL.md + deploy
    evaluate  - Check running experiments, keep/revert based on results
    revert    - Force-revert the running experiment
    status    - Show current experiment state and score trends

The optimizer modifies SKILL.md and deploys to all projects. Normal sprint
work generates composite scores that feed back into evaluation.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. Run: pip install duckdb")
    sys.exit(1)

DEFAULT_DB = os.path.expanduser("~/.flowstate/flowstate.duckdb")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_PATH = os.path.join(REPO_ROOT, "skills", "flowstate", "SKILL.md")
BACKUP_DIR = os.path.join(REPO_ROOT, ".optimize-backups")
IMPROVEMENT_THRESHOLD = 0.02
MAX_SPRINTS_PER_EXPERIMENT = 6
MIN_SPRINTS_PER_EXPERIMENT = 3


def get_db(db_path, read_only=False):
    return duckdb.connect(db_path, read_only=read_only)


# --- File operations ---


def backup_skill():
    """Save a backup of the current SKILL.md before mutation."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup = os.path.join(BACKUP_DIR, f"SKILL-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md")
    shutil.copy2(SKILL_PATH, backup)
    return backup


def restore_skill(backup_path):
    """Restore SKILL.md from backup."""
    shutil.copy2(backup_path, SKILL_PATH)


def read_skill():
    with open(SKILL_PATH) as f:
        return f.read()


def write_skill(content):
    with open(SKILL_PATH, "w") as f:
        f.write(content)


def deploy_skill():
    """Copy SKILL.md to all local and VPS projects that have it."""
    deployed = []

    # Local projects
    sites_dir = Path.home() / "Sites"
    if sites_dir.is_dir():
        for project_dir in sites_dir.iterdir():
            skill_target = project_dir / ".claude" / "skills" / "flowstate" / "SKILL.md"
            if skill_target.exists():
                shutil.copy2(SKILL_PATH, str(skill_target))
                deployed.append(project_dir.name)

    # VPS projects (best-effort)
    vps_host = os.environ.get("FLOWSTATE_VPS_HOST", "100.87.64.104")
    ssh_key = os.environ.get("FLOWSTATE_VPS_SSH_KEY", os.path.expanduser("~/.ssh/claude-dev-droplet"))
    if os.path.exists(ssh_key):
        try:
            # Copy to VPS temp
            subprocess.run(
                ["scp", "-i", ssh_key, SKILL_PATH, f"dev@{vps_host}:/tmp/SKILL-optimized.md"],
                capture_output=True, timeout=10,
            )
            # Deploy to all VPS projects
            result = subprocess.run(
                ["ssh", "-i", ssh_key, "-o", "ConnectTimeout=5", f"dev@{vps_host}",
                 "for f in /home/dev/projects/*/.claude/skills/flowstate/SKILL.md; do "
                 "[ -f \"$f\" ] && cp /tmp/SKILL-optimized.md \"$f\" && "
                 "echo $(basename $(dirname $(dirname $(dirname \"$f\")))); done"],
                capture_output=True, text=True, timeout=15,
            )
            vps_projects = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
            deployed.extend([f"vps:{p}" for p in vps_projects])
        except (subprocess.SubprocessError, OSError) as e:
            print(f"VPS deploy skipped: {e}", file=sys.stderr)

    return deployed


# --- Analysis ---


def get_baseline_score(con, last_n=10):
    row = con.execute(
        "SELECT AVG(composite_score) FROM (SELECT composite_score FROM sprints ORDER BY imported_at DESC LIMIT ?)",
        [last_n],
    ).fetchone()
    return round(row[0], 4) if row[0] else None


def get_top_gate_failures(con, limit=5):
    return con.execute(
        """SELECT gate_type, error_summary, COUNT(*) as freq
           FROM gate_failures GROUP BY gate_type, error_summary
           ORDER BY freq DESC LIMIT ?""",
        [limit],
    ).fetchall()


def get_worst_sprints(con, limit=5):
    return con.execute(
        """SELECT project, sprint, composite_score, gates_first_pass, task_type,
                  gates_first_pass_note
           FROM sprints WHERE composite_score IS NOT NULL
           ORDER BY composite_score ASC LIMIT ?""",
        [limit],
    ).fetchall()


def get_score_by_task_type(con):
    return con.execute(
        """SELECT task_type, COUNT(*) n, ROUND(AVG(composite_score), 4) avg_score
           FROM sprints WHERE task_type IS NOT NULL
           GROUP BY task_type ORDER BY avg_score ASC"""
    ).fetchall()


def get_running_experiment(con):
    row = con.execute(
        "SELECT * FROM experiments WHERE status = 'running' LIMIT 1"
    ).fetchone()
    if row:
        cols = [d[0] for d in con.description]
        return dict(zip(cols, row))
    return None


# --- Mutation generators (return actual text transformations) ---


def mutate_gate_incremental_tests(skill_text):
    """Add 'run tests after each source file change' to EXECUTE section."""
    marker = "- Run `/gate` after every meaningful change -- not batch-at-end"
    replacement = (
        "- **Incremental testing**: After modifying each source file, run the test suite for that module immediately. "
        "Do not wait for gate time to discover test failures.\n"
        "- Run `/gate` after every meaningful change -- not batch-at-end"
    )
    if "Incremental testing" in skill_text:
        return None  # already applied
    if marker not in skill_text:
        return None  # can't find insertion point
    return skill_text.replace(marker, replacement)


def mutate_model_routing_stronger(skill_text):
    """Strengthen model routing from advisory to directive."""
    old = "This is advisory — use your judgment. When in doubt, use the default."
    new = (
        "Follow this routing for subagent tasks. Opus for decisions, Sonnet for mechanical work. "
        "This saves ~40% on token costs for test generation and lint fixes with no measured quality impact."
    )
    if old not in skill_text:
        return None
    return skill_text.replace(old, new)


def mutate_scope_threshold(skill_text):
    """Raise light mode threshold from 5 files to 8 files."""
    old = "If ≤5 files AND no new external dependencies: use **LIGHT MODE**."
    new = "If ≤8 files AND no new external dependencies: use **LIGHT MODE**."
    if old not in skill_text:
        return None
    return skill_text.replace(old, new)


def mutate_retro_maturity(skill_text):
    """Lower full retro threshold from sprint 8 to sprint 5."""
    old = "**Sprints 1-8 (establishing)** — full retro:"
    new = "**Sprints 1-5 (establishing)** — full retro:"
    if old not in skill_text:
        return None
    new_text = skill_text.replace(old, new)
    old2 = "**Sprints 9+ (mature)** — slim retro:"
    new2 = "**Sprints 6+ (mature)** — slim retro:"
    if old2 in new_text:
        new_text = new_text.replace(old2, new2)
    return new_text


def mutate_gate_max_cycles(skill_text):
    """Reduce gate fix cycles from 3 to 2 to force cleaner first passes."""
    old = "fix, re-run, max 3 cycles"
    new = "fix, re-run, max 2 cycles. If still failing after 2, log the pattern and ask: is the gate too strict or the code too sloppy?"
    if old not in skill_text:
        return None
    return skill_text.replace(old, new)


# Map of mutation type → list of (generator_fn, hypothesis, mutation_type)
MUTATIONS = [
    {
        "fn": mutate_gate_incremental_tests,
        "hypothesis": "Running tests after each file change (not just at gate time) catches failures earlier, reducing gate rework",
        "mutation_type": "process",
    },
    {
        "fn": mutate_model_routing_stronger,
        "hypothesis": "Making model routing directive (not advisory) increases Sonnet usage for mechanical tasks, reducing token cost without quality loss",
        "mutation_type": "model_routing",
    },
    {
        "fn": mutate_scope_threshold,
        "hypothesis": "Raising light mode threshold from 5 to 8 files reduces planning overhead for medium sprints without losing quality",
        "mutation_type": "process",
    },
    # retro maturity mutation REMOVED — backtest Study 1 showed sprints after
    # full retros (6-8) score LOWER than after slim retros (9+), p=0.078.
    # The data does not support earlier cutover.
    {
        "fn": mutate_gate_max_cycles,
        "hypothesis": "Limiting gate fix cycles to 2 (from 3) forces cleaner first passes and surfaces chronic gate issues faster",
        "mutation_type": "gate_config",
    },
]


def propose_mutation(con):
    """Analyze sprint data and select the highest-priority applicable mutation.

    Scores each candidate mutation against gate failure frequency, Sonnet usage
    patterns, and general process priority. Returns the best candidate as a dict
    with hypothesis, mutation_type, fn, and new_text, or None if no mutations
    are applicable (all already applied or insertion points missing).
    """
    skill_text = read_skill()
    failures = get_top_gate_failures(con)
    task_scores = get_score_by_task_type(con)

    # Score each candidate mutation based on data signals
    candidates = []
    for m in MUTATIONS:
        new_text = m["fn"](skill_text)
        if new_text is None:
            continue  # already applied or can't find insertion point

        # Compute a priority score based on data relevance
        priority = 0

        if m["mutation_type"] == "gate_config" and failures:
            lint_freq = sum(f[2] for f in failures if f[0] == "lint")
            test_freq = sum(f[2] for f in failures if f[0] == "test")
            priority = lint_freq + test_freq

        elif m["mutation_type"] == "model_routing":
            # Check if Sonnet sprints score well
            row = con.execute(
                "SELECT COUNT(*), AVG(composite_score) FROM sprints WHERE sonnet_pct > 20"
            ).fetchone()
            if row[0] > 3 and row[1] and row[1] > 0.6:
                priority = row[0]

        elif m["mutation_type"] == "process":
            # General process improvements get medium priority
            priority = 5

        candidates.append({
            **m,
            "new_text": new_text,
            "priority": priority,
        })

    if not candidates:
        return None

    # Pick highest priority
    best = max(candidates, key=lambda c: c["priority"])
    return {
        "hypothesis": best["hypothesis"],
        "mutation_type": best["mutation_type"],
        "fn": best["fn"],
        "new_text": best["new_text"],
    }


# --- Experiment lifecycle ---


def create_experiment(con, mutation, backup_path, deployed):
    """Create experiment record and apply the mutation."""
    baseline = get_baseline_score(con)
    if baseline is None:
        print("ERROR: No baseline score available")
        return None

    exp_id = f"exp-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Store the backup path in mutation_diff so we can revert
    diff_info = json.dumps({
        "backup": backup_path,
        "deployed_to": deployed,
        "description": mutation["hypothesis"],
    })

    con.execute(
        """INSERT INTO experiments (id, hypothesis, mutation_type, mutation_diff, baseline_score)
           VALUES (?, ?, ?, ?, ?)""",
        [exp_id, mutation["hypothesis"], mutation["mutation_type"], diff_info, baseline],
    )

    return {"id": exp_id, "baseline_score": baseline}


def evaluate_experiment(con, experiment):
    """Evaluate a running experiment against its baseline score.

    Compares average composite scores of sprints completed since the experiment
    started to the pre-experiment baseline. Returns a status dict: 'kept' if
    improvement exceeds threshold, 'revert' if regression detected or max
    sprints reached without clear signal, 'running' if more data needed.
    """
    exp_id = experiment["id"]
    baseline = experiment["baseline_score"]
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
            "message": f"Need {MIN_SPRINTS_PER_EXPERIMENT - sprints_tested} more sprints",
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
            "message": f"Kept: +{improvement:.3f} over {sprints_tested} sprints. Mutation is now permanent.",
        }

    if improvement < -IMPROVEMENT_THRESHOLD:
        return {
            "status": "revert",
            "sprints_tested": sprints_tested,
            "improvement": round(improvement, 4),
            "message": f"Regression: {improvement:.3f} over {sprints_tested} sprints. Reverting.",
        }

    if sprints_tested >= MAX_SPRINTS_PER_EXPERIMENT:
        return {
            "status": "revert",
            "sprints_tested": sprints_tested,
            "improvement": round(improvement, 4),
            "message": f"Inconclusive after {sprints_tested} sprints ({improvement:+.3f}). Reverting.",
        }

    return {
        "status": "running",
        "sprints_tested": sprints_tested,
        "improvement": round(improvement, 4),
        "message": f"Running: {improvement:+.3f} over {sprints_tested} sprints. Need more data.",
    }


def revert_experiment(con, experiment):
    """Revert an experiment by restoring SKILL.md from backup."""
    exp_id = experiment["id"]
    diff_info = json.loads(experiment["mutation_diff"])
    backup_path = diff_info.get("backup")

    if backup_path and os.path.exists(backup_path):
        restore_skill(backup_path)
        deployed = deploy_skill()
        con.execute(
            "UPDATE experiments SET status = 'reverted', completed_at = current_timestamp WHERE id = ?",
            [exp_id],
        )
        return {"reverted": True, "backup": backup_path, "deployed_to": deployed}
    else:
        con.execute(
            "UPDATE experiments SET status = 'reverted', completed_at = current_timestamp WHERE id = ?",
            [exp_id],
        )
        return {"reverted": True, "warning": "Backup not found — SKILL.md not restored. Manual revert needed."}


# --- Commands ---


def cmd_propose(db_path):
    """Analyze data, propose and apply a mutation."""
    con = get_db(db_path)

    running = get_running_experiment(con)
    if running:
        print(f"Experiment already running: {running['id']}")
        print(f"  Hypothesis: {running['hypothesis']}")
        print(f"  Baseline: {running['baseline_score']}")
        print(f"  Sprints tested: {running['sprints_tested']}")
        print(f"\nRun 'evaluate' first.")
        con.close()
        return

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
            print(f"    {project} S{sprint}: {score:.3f} ({'pass' if gates else 'fail'}, {task_type})")

    mutation = propose_mutation(con)
    if not mutation:
        print("\nNo applicable mutations. All have been applied or data is insufficient.")
        con.close()
        return

    print(f"\nProposed mutation:")
    print(f"  Type: {mutation['mutation_type']}")
    print(f"  Hypothesis: {mutation['hypothesis']}")

    # Apply it
    print(f"\nApplying...")
    backup_path = backup_skill()
    write_skill(mutation["new_text"])
    deployed = deploy_skill()

    print(f"  Backup: {backup_path}")
    print(f"  SKILL.md: modified")
    print(f"  Deployed to: {', '.join(deployed) if deployed else '(none)'}")

    experiment = create_experiment(con, mutation, backup_path, deployed)
    if experiment:
        print(f"\n  Experiment: {experiment['id']}")
        print(f"  Baseline: {experiment['baseline_score']}")
        print(f"  Run {MIN_SPRINTS_PER_EXPERIMENT}-{MAX_SPRINTS_PER_EXPERIMENT} sprints, then 'evaluate'.")

    con.close()


def cmd_evaluate(db_path):
    """Evaluate the running experiment, auto-revert if needed."""
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

    if result["status"] == "revert":
        print(f"\nReverting...")
        r = revert_experiment(con, running)
        if r.get("deployed_to"):
            print(f"  Restored SKILL.md from backup")
            print(f"  Deployed to: {', '.join(r['deployed_to'])}")
        elif r.get("warning"):
            print(f"  WARNING: {r['warning']}")

    elif result["status"] == "kept":
        # Clean up backup since mutation is permanent
        diff_info = json.loads(running["mutation_diff"])
        backup = diff_info.get("backup")
        if backup and os.path.exists(backup):
            os.remove(backup)
            print(f"  Cleaned up backup (mutation is permanent)")

    con.close()


def cmd_revert(db_path):
    """Force-revert the running experiment."""
    con = get_db(db_path)

    running = get_running_experiment(con)
    if not running:
        print("No running experiment to revert.")
        con.close()
        return

    print(f"Force-reverting: {running['id']}")
    r = revert_experiment(con, running)
    if r.get("deployed_to"):
        print(f"  Restored SKILL.md from backup")
        print(f"  Deployed to: {', '.join(r['deployed_to'])}")
    elif r.get("warning"):
        print(f"  WARNING: {r['warning']}")
    print("  Done.")

    con.close()


def cmd_status(db_path):
    """Show optimizer status."""
    con = get_db(db_path, read_only=True)

    baseline = get_baseline_score(con)
    print(f"Current baseline (last 10 sprints): {baseline}")

    running = get_running_experiment(con)
    if running:
        print(f"\nRunning experiment: {running['id']}")
        print(f"  Type: {running['mutation_type']}")
        print(f"  Hypothesis: {running['hypothesis'][:100]}")
        print(f"  Baseline: {running['baseline_score']}")
        print(f"  Sprints tested: {running['sprints_tested']}")
    else:
        print("\nNo running experiment.")

    # Available mutations
    skill_text = read_skill()
    available = [m for m in MUTATIONS if m["fn"](skill_text) is not None]
    print(f"\nAvailable mutations: {len(available)}/{len(MUTATIONS)}")
    for m in available:
        print(f"  [{m['mutation_type']}] {m['hypothesis'][:80]}")

    # Past experiments
    rows = con.execute(
        """SELECT id, status, mutation_type, baseline_score, result_score, sprints_tested, hypothesis
           FROM experiments WHERE status != 'running'
           ORDER BY completed_at DESC LIMIT 10"""
    ).fetchall()
    if rows:
        print(f"\nPast experiments:")
        for eid, status, mtype, base, result, tested, hyp in rows:
            improvement = (result - base) if result else 0
            print(f"  {eid}: {status} ({mtype}) {improvement:+.3f} over {tested}s — {hyp[:60]}")

    # Score trend
    rows = con.execute(
        """SELECT project, sprint, composite_score
           FROM sprints ORDER BY imported_at DESC LIMIT 10"""
    ).fetchall()
    if rows:
        print(f"\nRecent scores:")
        for project, sprint, score in rows:
            bar = "#" * int(score * 20) if score else ""
            print(f"  {project:20s} S{sprint:2d}  {score:.3f}  {bar}")

    con.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Flowstate Hill-Climbing Optimizer")
    parser.add_argument("command", choices=["propose", "evaluate", "revert", "status"],
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
    elif args.command == "revert":
        cmd_revert(args.db)
    elif args.command == "status":
        cmd_status(args.db)


if __name__ == "__main__":
    main()
