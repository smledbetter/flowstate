# Flowstate v1.2 Experiment Protocol

## Question

How much does each v1.2 feature move sprint outcomes? Exploratory study generating effect size estimates across 8 products built under 4 conditions.

## Design: 2x2 Factorial + Replicates

Two features with the strongest prior evidence, crossed:

|  | Lessons OFF | Lessons ON |
|--|-------------|------------|
| **Lint pre-check OFF** | A: v1.1 baseline | B: lessons only |
| **Lint pre-check ON** | C: lint only | D: full v1.2 bundle |

- **Lint pre-check** (backtest ceiling: +0.40 composite score on 43 lint-failure sprints)
- **Cross-project lessons** (229 lessons seeded, Bayesian confidence ranking)

Condition D is lint + lessons only — a clean 2x2 cell. A 5th condition (E: full v1.2 bundle) runs outside the factorial as a separate descriptive comparison.

### Why not test all features individually?

6 features x 2 levels = 64 cells. Not feasible. The backtest identified lint pre-check (+0.40 ceiling) and cross-project lessons (the compounding hypothesis) as the two worth isolating. Everything else is marginal by comparison.

## Products: 8 small-scope builds

Each product is built under all 4 factorial conditions (A-D) = 32 builds. Products 1-3 also get Condition E (full bundle) = 3 extra builds. Plus 2 replicates = 37 builds total. Products are the blocking factor (paired/matched design eliminates between-product variance).

### Product specifications

Each product ships in 5-7 sprints. PRDs written before the experiment starts by a separate agent session, human-reviewed for comparable scope. All products:
- Self-contained (no external API keys or services)
- Single language/stack
- Clear "done" state (all roadmap phases complete, gates passing)
- No infrastructure components (no Docker, no deploy — pure application code)

Product roster (diverse stacks, comparable scope):

| # | Product | Stack | Scope |
|---|---------|-------|-------|
| 1 | File format converter CLI | Python | Parse/validate/transform CSV/JSON/YAML, streaming, error recovery |
| 2 | Static site generator | TypeScript/Node | Markdown to HTML, templates, asset pipeline, dev server |
| 3 | Bookmark manager API | Go | REST API, SQLite, tags, full-text search, import/export |
| 4 | Personal finance TUI | Rust | Terminal UI, transaction entry, categories, monthly reports |
| 5 | Schema-driven ETL pipeline | Python | CSV/JSON intake, schema validation, transforms, output formats |
| 6 | Markdown note search | TypeScript/Node | Index markdown files, full-text + fuzzy search, CLI + TUI |
| 7 | Poll/vote system | Python/FastAPI | Create polls, vote, results, persistent state, CLI + API |
| 8 | Git stats dashboard | Go | Parse git log, contributor stats, churn analysis, HTML report |

### Replicates

Products 1 and 2 are each built twice under condition A (v1.1 baseline) to estimate within-product variance from LLM stochasticity. This adds 2 builds (34 total) and provides the noise floor: if two identical-condition builds of the same product differ by X, then treatment differences smaller than X are noise.

## Conditions detail

### Condition A: v1.1 baseline
- SKILL.md: v1.1 (no lint pre-check instruction, no gate failure memory query, no cross-project lessons section, no coverage floor, no model routing)
- Learnings: progress.md within-project only
- No DuckDB integration
- Metrics collected normally via MCP collect_metrics, imported post-build

### Condition B: lessons only
- SKILL.md: v1.1 + cross-project lessons section added to Phase 1+2
- Auto-continue injects lessons from centralized DB into subagent prompts
- Gate failure memory OFF, lint pre-check OFF, coverage floor OFF, model routing OFF
- Lesson corpus: frozen snapshot of 229 seed lessons for all builds (no cross-build accumulation — fixes Study Gate's independence concern)

### Condition C: lint pre-check only
- SKILL.md: v1.1 + lint pre-check instruction added to EXECUTE section
- No cross-project lessons, no gate failure memory, no coverage floor, no model routing
- Tests the single highest-leverage mutation in isolation

### Condition D: lint + lessons (clean interaction cell)
- SKILL.md: v1.1 + lint pre-check + cross-project lessons section
- Lesson corpus: frozen snapshot (same as B)
- NO gate failure memory, NO coverage floor, NO model routing
- Clean 2x2 cell: tests whether lint + lessons together match the additive prediction (C + B - A)

### Condition E: full v1.2 bundle (outside factorial)
- SKILL.md: v1.2 (all features active — lint pre-check, lessons, gate failure memory, coverage floor, model routing)
- Lesson corpus: frozen snapshot (same as B and D)
- Runs for products 1-3 only (not all 8 — cost control)
- Compared descriptively to conditions A and D. Cannot attribute gains to specific features beyond lint + lessons.

### Lesson corpus freezing

All conditions that use lessons (B and D) get the same frozen snapshot of 229 lessons taken before the experiment starts. No build writes new lessons back to the shared DB during the experiment. This restores independence between builds while still testing whether the seed lessons help.

After the experiment, if lessons show positive effect, we can run a follow-up with live accumulation.

## Execution

### Infrastructure

All builds run on VPS (100.87.64.104). Each build gets:
- Its own directory: `/home/dev/experiment/{product}-{condition}/`
- Its own git repo (initialized at Sprint 0)
- Its own tmux session: `exp-{product}-{condition}`
- Its own flowstate directory: `~/.flowstate/exp-{product}-{condition}/`

4 builds run concurrently (VPS has capacity for 4 Claude sessions based on prior experience). Builds are queued in waves.

### Launch protocol

Each build is launched as:
```bash
cd /home/dev/experiment/{product}-{condition}
claude -p --dangerously-skip-permissions 'go'
```

Sprint 0 (roadmap approval) is pre-approved — the PRD and roadmap are copied in before launch, marked as human-reviewed. No human intervention after launch.

### Randomization

Build order is randomized within each wave to prevent systematic ordering effects. The randomization schedule is generated and logged before the experiment starts.

### Data collection

After each build completes:
1. Import all sprint metrics via `mcp__flowstate__import_sprint` (tags each sprint with `experiment_id`)
2. Record: total sprints, total tokens, total active time, final test count, final coverage
3. For conditions B and D: count how many seed lessons appeared in sprint retros/progress files
4. For condition D: count gate failure memory queries and whether they influenced implementation

Raw session logs preserved at `~/.claude/projects/` for post-hoc analysis.

## Metrics

### Manipulation check (not a primary outcome)

**Gates-first-pass rate**: proportion of sprints where all gates passed first try. This is the direct target of lint pre-check — finding improvement here is expected by construction. Reported as diagnostic data, not as evidence of downstream benefit.

Additionally, gate failures are decomposed by type:
- **Lint-class failures**: lint/format/style errors caught at gate time
- **Non-lint failures**: test failures, build errors, coverage regressions

If lint pre-check reduces lint-class failures but not non-lint failures, the mechanism is confirmed but the scope is narrow. If it also reduces non-lint failures (e.g., by encouraging more careful code), that's a genuine finding.

### Co-primary outcomes (three metrics, all independent of treatments)

1. **Token efficiency**: new_work_tokens / loc_added, averaged per build. Lower is better. Independent of both treatments.

2. **Active session time**: mean active_session_time_s per sprint per build. Independent of both treatments.

3. **Sprints to ship**: total sprints to complete all roadmap phases. Independent of both treatments.

### Efficiency composite (secondary)

For summary reporting, an efficiency composite excluding gates:
```
efficiency = 0.50 * token_efficiency (1.0 - tokens_per_loc / 1000)
           + 0.30 * time_efficiency  (1.0 - session_seconds / 3600)
           + 0.20 * autonomy         (1.0 - compressions / 5)
```
This provides an independent test of whether treatments improve outcomes beyond their direct mechanical effect on gates.

### Lint activation instrumentation

For conditions C and D (lint pre-check active), log per sprint:
- Whether lint was run before gates (boolean)
- Whether lint found and fixed errors before gates (boolean)
- What errors were fixed (one-line summary)

This enables two analyses:
- **Intent-to-treat**: all sprints in conditions C/D vs A/B (unconditional average)
- **Treatment-on-treated**: only sprints where lint actually caught something (conditional estimate)

A null H1 result with low activation rate means "lint didn't fire" not "lint doesn't help."

### Secondary metrics
- Total tokens consumed (cost proxy)
- Final test count and coverage
- Human interventions (should be 0 for all builds)
- Lessons referenced in sprint context (conditions B and D only)

## Analysis

### Approach: exploratory, effect sizes with confidence intervals

No significance-based go/no-go. We report:

1. **Per-product paired differences** for each co-primary metric (condition X - condition A), with 95% bootstrap CIs
2. **Lint pre-check main effect**: avg of (C,D) minus avg of (A,B) — on gates rate (mechanical), token efficiency (independent), session time (independent), sprints to ship (independent)
3. **Lessons main effect**: avg of (B,D) minus avg of (A,C) — on all four co-primary metrics (all independent of lessons treatment)
4. **Bundle test (not interaction)**: Does D perform at least as well as the additive prediction (C + B - A)? This tests whether the full v1.2 bundle has synergy or interference, but cannot attribute any D-specific effect to lint x lessons interaction because D includes 3 additional features. Reported descriptively, not as a hypothesis test.
5. **Within-product replicate variance** (from products 1-2 condition A replicates) as the noise floor
6. **Individual sprint trajectories** per build (metrics over time)
7. **Lint activation analysis**: intent-to-treat vs treatment-on-treated for conditions C and D

### Noise floor check

If the two condition-A replicates of product 1 differ by more than 0.10 on any co-primary metric, then differences smaller than 0.10 between conditions are indistinguishable from LLM stochasticity. We report this threshold explicitly for each metric.

### Two-sided framing

We look for both improvement and degradation. v1.2 features add overhead (extra MCP calls, longer prompts with lessons). It is plausible that this overhead hurts small projects where the features don't have time to pay off.

### Pre-registered decision thresholds (set after Pilot 2)

Before the full experiment, we commit:
- **H1 (lint) is supported if**: the lower bound of the bootstrap CI for the lint main effect on token efficiency exceeds the noise floor from Pilot 2 replicates
- **H2 (lessons) is exploratory**: report effect size and CI regardless of width, with explicit statement that the study is not powered to confirm or reject
- **Noise floor threshold**: if Pilot 2 replicate variance exceeds 0.15 on any co-primary metric, stop and investigate

### Power note

At N=8 paired observations, bootstrap CIs have ~88-92% coverage (not 95%). We disclose this. The lessons effect (expected +0.05) is likely underpowered. The lint effect on token efficiency is the best-powered hypothesis.

### Wave scheduling

All 4 conditions of each product run in the same wave to protect within-product pairing from model version drift between waves.

## Pilot stages

### Pilot 1: Infrastructure check (2-3 hours)

Build product 1 under conditions A and D only (2 builds). Goals:
- Both builds complete autonomously (no human intervention needed)
- Metrics collect and import correctly
- Lessons appear in condition D sprint context
- Lint activation is logged in condition D sprints
- Rough timing estimate for full experiment

**Stop if:** either build fails to complete, metrics don't collect, or features don't activate. Fix infrastructure before proceeding.

### Pilot 2: Variance + effect size estimate (8-10 hours)

Build products 1-2 under all 4 conditions + Condition E for product 1 + 2 replicates of condition A (11 builds). Goals:
- Estimate within-product variance from replicates (the noise floor)
- Estimate between-condition effect sizes on co-primary metrics
- Set decision thresholds for H1 based on observed noise floor
- Confirm 8 products is enough to see signal above noise
- Refine timing and cost estimates

**Stop if:** replicate variance > 0.15 on any co-primary metric. Investigate before proceeding.

**Adjust if:** effect sizes are smaller than expected. Consider adding products 9-10.

### Full experiment (10-14 hours)

Build products 3-8 under all 4 conditions + Condition E for products 2-3 (26 builds). Analyze all 37 builds together.

## Deliverable

Blog post: "I Built 8 Products 4 Ways to Test Whether AI Agents Can Optimize Their Own Workflow"

Structure:
1. What Flowstate is (brief)
2. What v1.2 added (autolearning, lint pre-check, the hill-climbing loop)
3. The experiment: 2x2 factorial, 8 products, 34 builds, ~200 sprints
4. What we measured (4 co-primary metrics, why no single composite)
5. Results by feature: lint pre-check effect (with activation rates), lessons effect, full bundle
6. The noise floor: how much LLM stochasticity matters (replicate data)
7. What Condition D tells us (and what it can't tell us — the bundling limitation)
8. Honest assessment: which features earned their complexity?

All four outcomes (strong positive, weak positive, null, negative) are publishable. The design limitations (N=8, bootstrap coverage, H2 power) are disclosed in the post, not hidden.

## Limitations (pre-registered)

- **Condition D is lint + lessons only.** The interaction effect tests additivity, not synergy with other v1.2 features. Condition E (full bundle, products 1-3 only) provides descriptive comparison but cannot attribute gains.
- **N=8 is exploratory.** Effect size estimates are the primary deliverable, not p-values. A powered confirmatory follow-up would require N based on the variance observed here.
- **Bootstrap CIs at N=8 have ~88-92% coverage**, not 95%. Disclosed in all reporting.
- **H2 (lessons) is likely underpowered.** Designated exploratory. We report the estimate regardless.
- **Single practitioner.** Results may not generalize to multi-human or multi-agent teams.
- **Small products (5-7 sprints).** Features that compound over longer projects may show larger effects at scale.
- **Lesson corpus is frozen.** The accumulation hypothesis (lessons improve as they grow) is not tested here.
- **Lint activation is heterogeneous.** Products with clean-code agents receive near-zero lint treatment. Intent-to-treat and treatment-on-treated analyses address this.
