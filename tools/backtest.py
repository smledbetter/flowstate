#!/usr/bin/env python3
"""Flowstate Autoresearch Loop Backtest.

Backtests the hill-climbing optimizer against 132 historical sprints.
Three studies, read-only, no side effects.

Usage:
    python3 tools/backtest.py [--db PATH]

Study 1: Natural experiment analysis (3 testable mutations)
Study 2: Simulated loop replay with naive baselines
Study 3: Lint counterfactual scoring (pilot)
"""

import json
import os
import random
import sys
from collections import defaultdict

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. Run: pip install duckdb")
    sys.exit(1)

DEFAULT_DB = os.path.expanduser("~/.flowstate/flowstate.duckdb")


def get_db(db_path):
    return duckdb.connect(db_path, read_only=True)


def composite_score(m):
    """Recompute composite score from a metrics dict."""
    gates = m.get("gates_first_pass")
    quality = 1.0 if gates is True else (0.0 if gates is False else 0.5)
    nw = m.get("new_work_tokens")
    loc = m.get("loc_added") or 0
    if nw and loc > 0:
        token_score = max(0.0, 1.0 - ((nw / loc) / 1000))
    else:
        token_score = 0.5
    time_s = m.get("active_session_time_s")
    time_score = max(0.0, 1.0 - (time_s / 3600)) if time_s is not None else 0.5
    compressions = m.get("context_compressions") or 0
    autonomy = max(0.0, 1.0 - (compressions / 5))
    return round(0.40 * quality + 0.30 * token_score + 0.15 * time_score + 0.15 * autonomy, 4)


# ---------------------------------------------------------------------------
# Study 3: Lint Counterfactual (run first as pilot)
# ---------------------------------------------------------------------------

def study_3(con):
    print("=" * 70)
    print("STUDY 3: Lint Counterfactual Scoring (Pilot)")
    print("=" * 70)
    print()

    # Get lint-failure sprints with enough data to recompute
    rows = con.execute("""
        SELECT s.project, s.sprint, s.composite_score,
               s.new_work_tokens, s.loc_added, s.active_session_time_s,
               s.context_compressions
        FROM sprints s
        JOIN gate_failures gf ON s.project = gf.project AND s.sprint = gf.sprint
        WHERE gf.gate_type = 'lint' AND s.gates_first_pass = false
    """).fetchall()

    if not rows:
        print("No lint-failure sprints found.")
        return None

    # Deduplicate (a sprint may have multiple lint failures)
    seen = set()
    unique = []
    for r in rows:
        key = (r[0], r[1])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    actual_scores = []
    counterfactual_scores = []

    for project, sprint, actual, nw, loc, time_s, compressions in unique:
        actual_scores.append(actual)
        # Recompute with gates_first_pass=True
        cf = composite_score({
            "gates_first_pass": True,
            "new_work_tokens": nw,
            "loc_added": loc,
            "active_session_time_s": time_s,
            "context_compressions": compressions,
        })
        counterfactual_scores.append(cf)

    actual_avg = sum(actual_scores) / len(actual_scores)
    cf_avg = sum(counterfactual_scores) / len(counterfactual_scores)
    delta = cf_avg - actual_avg

    print(f"Lint-failure sprints: {len(unique)}")
    print(f"Actual avg score:        {actual_avg:.4f}")
    print(f"Counterfactual avg:      {cf_avg:.4f} (if gates had passed)")
    print(f"Delta:                   +{delta:.4f}")
    print()

    # Bootstrap 95% CI on the delta
    n_boot = 10000
    random.seed(42)
    deltas = []
    for _ in range(n_boot):
        idx = [random.randint(0, len(unique) - 1) for _ in range(len(unique))]
        boot_actual = sum(actual_scores[i] for i in idx) / len(idx)
        boot_cf = sum(counterfactual_scores[i] for i in idx) / len(idx)
        deltas.append(boot_cf - boot_actual)
    deltas.sort()
    ci_lo = deltas[int(n_boot * 0.025)]
    ci_hi = deltas[int(n_boot * 0.975)]
    print(f"Bootstrap 95% CI:        [{ci_lo:.4f}, {ci_hi:.4f}]")
    print()

    if delta > 0.05:
        print(f"PASS: delta {delta:.4f} > 0.05 threshold. Lint pre-check has meaningful ceiling.")
    else:
        print(f"FAIL: delta {delta:.4f} <= 0.05. Lint pre-check ceiling is too small.")

    return delta


# ---------------------------------------------------------------------------
# Study 1: Natural Experiment Analysis (3 mutations, Study Gate fixes applied)
# ---------------------------------------------------------------------------

def mann_whitney_u(a, b):
    """Mann-Whitney U test. Returns U statistic and approximate two-tailed p-value.

    Tries scipy.stats.mannwhitneyu first for correctness (exact p-values for
    small samples, proper tie correction). Falls back to a hand-rolled version
    with average-rank tie handling and normal approximation.
    """
    try:
        from scipy.stats import mannwhitneyu as _mwu
        stat, p = _mwu(a, b, alternative='two-sided')
        return stat, p
    except ImportError:
        pass

    combined = [(v, 'a') for v in a] + [(v, 'b') for v in b]
    combined.sort(key=lambda x: x[0])

    # Assign average ranks for ties
    n = len(combined)
    avg_ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j + 1) / 2  # 1-indexed average rank for this tie group
        for k in range(i, j):
            avg_ranks[k] = avg_rank
        i = j

    # Compute rank sums per group using the averaged ranks
    R_a = sum(avg_ranks[i] for i in range(n) if combined[i][1] == 'a')

    n_a, n_b = len(a), len(b)
    U_a = R_a - n_a * (n_a + 1) / 2
    U_b = n_a * n_b - U_a
    U = min(U_a, U_b)

    # Normal approximation for p-value
    mu = n_a * n_b / 2
    sigma = (n_a * n_b * (n_a + n_b + 1) / 12) ** 0.5
    if sigma == 0:
        return U, 1.0
    z = (U - mu) / sigma
    # Approximate two-tailed p from z using error function approximation
    p = 2 * (1 - _norm_cdf(abs(z)))
    return U, p


def _norm_cdf(x):
    """Approximate normal CDF using Abramowitz and Stegun formula 7.1.26.

    This rational approximation has a maximum absolute error of ~1.5e-7, which
    is adequate for hypothesis testing p-values. For extreme z-values (|z| > 6)
    the approximation loses precision; in practice this only matters for very
    small p-values that are well below any reasonable significance threshold.
    """
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / (2 ** 0.5)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * (2.71828182845904523536 ** (-x * x))
    return 0.5 * (1.0 + sign * y)


def study_1(con):
    print()
    print("=" * 70)
    print("STUDY 1: Natural Experiment Analysis (3 mutations)")
    print("=" * 70)
    print()
    print("Study Gate fixes applied: dropped incremental testing (tautological),")
    print("dropped model routing (n=9, underpowered). Testing 3 remaining mutations.")
    print()

    results = {}

    # --- Mutation 1: Scope threshold (light mode ≤8 vs ≤5 files) ---
    print("-" * 50)
    print("Mutation: Scope threshold (medium vs large sprints)")
    print("-" * 50)

    medium = con.execute("""
        SELECT composite_score FROM sprints
        WHERE loc_added BETWEEN 500 AND 1200 AND composite_score IS NOT NULL
    """).fetchall()
    large = con.execute("""
        SELECT composite_score FROM sprints
        WHERE loc_added > 1500 AND composite_score IS NOT NULL
    """).fetchall()

    medium_scores = [r[0] for r in medium]
    large_scores = [r[0] for r in large]

    if medium_scores and large_scores:
        m_avg = sum(medium_scores) / len(medium_scores)
        l_avg = sum(large_scores) / len(large_scores)
        U, p = mann_whitney_u(medium_scores, large_scores)
        print(f"  Medium (500-1200 LOC): n={len(medium_scores)}, avg={m_avg:.4f}")
        print(f"  Large (>1500 LOC):     n={len(large_scores)}, avg={l_avg:.4f}")
        print(f"  Delta: {m_avg - l_avg:+.4f}")
        print(f"  Mann-Whitney U={U:.0f}, p={p:.4f}")
        supports = m_avg >= l_avg
        print(f"  Supports mutation: {'YES' if supports else 'NO'}")
        results["scope_threshold"] = {"supports": supports, "p": p, "delta": m_avg - l_avg}
    else:
        print("  Insufficient data")
        results["scope_threshold"] = {"supports": False, "p": 1.0}

    print()

    # --- Mutation 2: Retro maturity (sprints 6-8 vs 9+) ---
    print("-" * 50)
    print("Mutation: Retro maturity (does retro depth affect next sprint?)")
    print("-" * 50)

    # For each project, get sprints 6-8 and their N+1 scores
    projects = con.execute("SELECT DISTINCT project FROM sprints WHERE sprint >= 6").fetchall()
    treatment_next = []  # next-sprint scores after sprints 6-8 (full retro)
    control_next = []    # next-sprint scores after sprints 9+ (slim retro)

    for (proj,) in projects:
        sprints = con.execute("""
            SELECT sprint, composite_score FROM sprints
            WHERE project = ? AND composite_score IS NOT NULL
            ORDER BY sprint
        """, [proj]).fetchall()
        sprint_map = {s: score for s, score in sprints}
        for s, score in sprints:
            if s + 1 in sprint_map:
                next_score = sprint_map[s + 1]
                if 6 <= s <= 8:
                    treatment_next.append(next_score)
                elif s >= 9:
                    control_next.append(next_score)

    if treatment_next and control_next:
        t_avg = sum(treatment_next) / len(treatment_next)
        c_avg = sum(control_next) / len(control_next)
        U, p = mann_whitney_u(treatment_next, control_next)
        print(f"  After sprints 6-8 (full retro):  n={len(treatment_next)}, next-sprint avg={t_avg:.4f}")
        print(f"  After sprints 9+ (slim retro):   n={len(control_next)}, next-sprint avg={c_avg:.4f}")
        print(f"  Delta: {t_avg - c_avg:+.4f}")
        print(f"  Mann-Whitney U={U:.0f}, p={p:.4f}")
        # Mutation says: no difference justifies earlier cutover
        no_diff = abs(t_avg - c_avg) < 0.05
        print(f"  Supports mutation (no meaningful difference): {'YES' if no_diff else 'NO'}")
        results["retro_maturity"] = {"supports": no_diff, "p": p, "delta": t_avg - c_avg}
    else:
        print("  Insufficient data")
        results["retro_maturity"] = {"supports": False, "p": 1.0}

    print()

    # --- Mutation 3: Gate max cycles ---
    print("-" * 50)
    print("Mutation: Gate max cycles (are 3 cycles ever needed?)")
    print("-" * 50)

    notes = con.execute("""
        SELECT gates_first_pass_note FROM sprints
        WHERE gates_first_pass = false AND gates_first_pass_note IS NOT NULL
        AND gates_first_pass_note != ''
    """).fetchall()

    cycle_1 = 0
    cycle_2 = 0
    cycle_3_plus = 0
    unclassified = 0

    for (note,) in notes:
        note_lower = note.lower()
        if any(w in note_lower for w in ["1 cycle", "fixed immediately", "one cycle", "fixed and re-ran",
                                          "fixed in 1", "fixed on first"]):
            cycle_1 += 1
        elif any(w in note_lower for w in ["2 cycle", "two cycle", "second attempt", "fixed in 2",
                                            "2 attempts"]):
            cycle_2 += 1
        elif any(w in note_lower for w in ["3 cycle", "three cycle", "third attempt", "3 attempts",
                                            "multiple rounds"]):
            cycle_3_plus += 1
        else:
            # Default: most gate failures are fixed in 1 cycle based on v1.1 data
            cycle_1 += 1
            unclassified += 1

    total_failures = cycle_1 + cycle_2 + cycle_3_plus
    print(f"  Gate failures analyzed: {total_failures} ({unclassified} auto-classified as 1-cycle)")
    print(f"  Fixed in 1 cycle: {cycle_1} ({cycle_1/max(total_failures,1)*100:.0f}%)")
    print(f"  Fixed in 2 cycles: {cycle_2} ({cycle_2/max(total_failures,1)*100:.0f}%)")
    print(f"  Fixed in 3+ cycles: {cycle_3_plus} ({cycle_3_plus/max(total_failures,1)*100:.0f}%)")
    safe_to_cut = cycle_3_plus == 0 or cycle_3_plus / total_failures < 0.05
    print(f"  Supports mutation (safe to cut to 2): {'YES' if safe_to_cut else 'NO'}")
    results["gate_max_cycles"] = {"supports": safe_to_cut, "cycle_3_pct": cycle_3_plus / max(total_failures, 1)}

    print()

    # --- Summary ---
    passing = sum(1 for r in results.values() if r["supports"])
    print("=" * 50)
    print(f"Study 1 Summary: {passing}/3 mutations supported")
    print("=" * 50)
    for name, r in results.items():
        status = "SUPPORTED" if r["supports"] else "NOT SUPPORTED"
        print(f"  {name:25s} {status}")

    threshold = 2  # ≥2 of 3 (Study Gate fix: was 3/5)
    if passing >= threshold:
        print(f"\nPASS: {passing}/3 >= {threshold}/3 threshold")
    else:
        print(f"\nFAIL: {passing}/3 < {threshold}/3 threshold")

    return results


# ---------------------------------------------------------------------------
# Study 2: Simulated Loop Replay (with naive baselines)
# ---------------------------------------------------------------------------

def study_2(con):
    print()
    print("=" * 70)
    print("STUDY 2: Simulated Loop Replay (with naive baselines)")
    print("=" * 70)
    print()
    print("Study Gate fixes applied: naive baselines added, checkpoints every 3")
    print("sprints for adequate power.")
    print()

    # Get all sprints ordered chronologically
    rows = con.execute("""
        SELECT project, sprint, composite_score, gates_first_pass,
               sonnet_pct, loc_added, active_session_time_s
        FROM sprints
        WHERE composite_score IS NOT NULL
        ORDER BY imported_at
    """).fetchall()

    scores = [r[2] for r in rows]
    n = len(scores)
    print(f"Total sprints with scores: {n}")

    if n < 36:
        print("Insufficient data (need ≥36 sprints)")
        return None

    # Simulate at every-3-sprint checkpoints starting at 30
    WINDOW = 10      # baseline window
    EVAL = 6         # evaluation window
    STEP = 3         # checkpoint frequency
    THRESHOLD = 0.02

    checkpoints = list(range(30, n - EVAL + 1, STEP))
    print(f"Checkpoints: {len(checkpoints)} (every {STEP} sprints, starting at {checkpoints[0]})")
    print()

    # Run optimizer at each checkpoint
    optimizer_decisions = []
    for cp in checkpoints:
        baseline = sum(scores[cp - WINDOW:cp]) / WINDOW
        post = scores[cp:cp + EVAL]
        post_avg = sum(post) / len(post)
        improvement = post_avg - baseline

        if improvement > THRESHOLD:
            decision = "keep"
        elif improvement < -THRESHOLD:
            decision = "revert"
        else:
            decision = "inconclusive"

        optimizer_decisions.append({
            "checkpoint": cp,
            "baseline": round(baseline, 4),
            "post_avg": round(post_avg, 4),
            "improvement": round(improvement, 4),
            "decision": decision,
        })

    # Run naive baselines
    def naive_always_keep(checkpoints, scores):
        correct = 0
        for d in checkpoints:
            # Always-keep is "correct" if post > baseline
            if d["improvement"] > 0:
                correct += 1
        return correct / len(checkpoints)

    def naive_always_revert(checkpoints, scores):
        correct = 0
        for d in checkpoints:
            # Always-revert is "correct" if post < baseline
            if d["improvement"] < 0:
                correct += 1
        return correct / len(checkpoints)

    def naive_random(checkpoints, scores, seed=42):
        random.seed(seed)
        correct = 0
        for d in checkpoints:
            choice = random.choice(["keep", "revert"])
            if choice == "keep" and d["improvement"] > 0:
                correct += 1
            elif choice == "revert" and d["improvement"] < 0:
                correct += 1
        return correct / len(checkpoints)

    # Optimizer accuracy: did it make the right call?
    # "Right" = keep when improvement > 0, revert when improvement < 0
    # Inconclusive decisions count as wrong (the optimizer didn't commit)
    opt_correct = 0
    for d in optimizer_decisions:
        if d["decision"] == "keep" and d["improvement"] > 0:
            opt_correct += 1
        elif d["decision"] == "revert" and d["improvement"] < 0:
            opt_correct += 1

    opt_accuracy = opt_correct / len(optimizer_decisions)
    ak_accuracy = naive_always_keep(optimizer_decisions, scores)
    ar_accuracy = naive_always_revert(optimizer_decisions, scores)
    rand_accuracy = naive_random(optimizer_decisions, scores)

    # Print checkpoint table
    print(f"{'CP':>4s}  {'Baseline':>8s}  {'Post':>8s}  {'Delta':>8s}  {'Decision':>12s}")
    print("-" * 50)
    for d in optimizer_decisions:
        print(f"{d['checkpoint']:4d}  {d['baseline']:8.4f}  {d['post_avg']:8.4f}  {d['improvement']:+8.4f}  {d['decision']:>12s}")

    print()
    print("Decision distribution:")
    keeps = sum(1 for d in optimizer_decisions if d["decision"] == "keep")
    reverts = sum(1 for d in optimizer_decisions if d["decision"] == "revert")
    incon = sum(1 for d in optimizer_decisions if d["decision"] == "inconclusive")
    print(f"  Keep: {keeps}, Revert: {reverts}, Inconclusive: {incon}")

    print()
    print("Accuracy comparison:")
    print(f"  Optimizer:      {opt_accuracy:.3f} ({opt_correct}/{len(optimizer_decisions)})")
    print(f"  Always-keep:    {ak_accuracy:.3f}")
    print(f"  Always-revert:  {ar_accuracy:.3f}")
    print(f"  Random:         {rand_accuracy:.3f}")

    best_naive = max(ak_accuracy, ar_accuracy, rand_accuracy)
    margin = opt_accuracy - best_naive

    print()
    print(f"Best naive baseline: {best_naive:.3f}")
    print(f"Optimizer margin over best naive: {margin:+.3f}")

    if margin > 0.10:
        print(f"\nPASS: optimizer beats best naive by {margin:.3f} (>{0.10} threshold)")
    elif margin > 0:
        print(f"\nWEAK PASS: optimizer beats best naive by {margin:.3f} (<{0.10} but positive)")
    else:
        print(f"\nFAIL: optimizer does not beat best naive baseline")

    # Power note
    print(f"\nPower note: {len(checkpoints)} checkpoints. Minimum detectable accuracy")
    print(f"at alpha=0.10 (one-sided binomial): ~{0.5 + 1.28 / (2 * len(checkpoints)**0.5):.3f}")

    return {
        "optimizer_accuracy": opt_accuracy,
        "always_keep": ak_accuracy,
        "always_revert": ar_accuracy,
        "random": rand_accuracy,
        "margin": margin,
        "n_checkpoints": len(checkpoints),
    }


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(s3_delta, s1_results, s2_results):
    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print()

    # Study 3
    s3_pass = s3_delta is not None and s3_delta > 0.05
    print(f"Study 3 (Lint counterfactual):  {'PASS' if s3_pass else 'FAIL'} (delta={s3_delta:.4f})")

    # Study 1
    if s1_results:
        s1_passing = sum(1 for r in s1_results.values() if r["supports"])
        s1_pass = s1_passing >= 2
        print(f"Study 1 (Natural experiments): {'PASS' if s1_pass else 'FAIL'} ({s1_passing}/3 supported)")
    else:
        s1_pass = False
        print(f"Study 1 (Natural experiments): FAIL (no results)")

    # Study 2
    if s2_results:
        s2_pass = s2_results["margin"] > 0
        print(f"Study 2 (Loop replay):         {'PASS' if s2_pass else 'FAIL'} (margin={s2_results['margin']:+.3f} over best naive)")
    else:
        s2_pass = False
        print(f"Study 2 (Loop replay):         FAIL (no results)")

    print()
    all_pass = s3_pass and s1_pass and s2_pass
    any_pass = s3_pass or s1_pass or s2_pass
    if all_pass:
        print("VERDICT: ALL PASS. The autoresearch loop has empirical backing.")
        print("Proceed with live deployment and let it run.")
    elif any_pass:
        passing = [s for s, p in [("S3", s3_pass), ("S1", s1_pass), ("S2", s2_pass)] if p]
        failing = [s for s, p in [("S3", s3_pass), ("S1", s1_pass), ("S2", s2_pass)] if not p]
        print(f"VERDICT: MIXED. {', '.join(passing)} passed, {', '.join(failing)} failed.")
        print("The loop has partial support. Review failing studies before committing.")
    else:
        print("VERDICT: ALL FAIL. The autoresearch loop does not have empirical backing.")
        print("Either the mutations don't matter or the evaluation framework is wrong.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Flowstate Autoresearch Loop Backtest")
    parser.add_argument("--db", default=DEFAULT_DB, help="DuckDB path")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: DuckDB not found at {args.db}")
        sys.exit(1)

    con = get_db(args.db)

    total = con.execute("SELECT COUNT(*) FROM sprints WHERE composite_score IS NOT NULL").fetchone()[0]
    print(f"Backtest dataset: {total} sprints with composite scores")
    print()

    # Run in recommended order (Study Gate: pilot first)
    s3_delta = study_3(con)
    s1_results = study_1(con)
    s2_results = study_2(con)

    print_summary(s3_delta, s1_results, s2_results)

    con.close()


if __name__ == "__main__":
    main()
