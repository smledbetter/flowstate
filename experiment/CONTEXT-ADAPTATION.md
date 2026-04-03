# Experiment: Sprint-Over-Sprint Context Adaptation

## Status: PROPOSED (not yet designed)

Depends on: results from the v1.2 2x2 factorial experiment (PROTOCOL.md).

## Motivation

The v1.2 experiment tests two instruction-level mutations (lint pre-check, cross-project lessons) on small 5-7 sprint products. Early data suggests effects are null or small — the noise floor from LLM stochasticity may swamp prompt-level interventions at that scale.

Most real Flowstate projects run ~20 sprints. At that timescale, the dominant source of waste shifts from "did the agent follow instructions" to "did the agent get better at working in this codebase over time." A sprint-18 agent with a fresh context window is no more fluent in the codebase than a sprint-2 agent unless the context loading actively improves.

This experiment tests whether **adapting what gets loaded into each sprint's context window** produces stronger effects than the instruction-level mutations tested in v1.2.

## Hypothesis

Over 20-sprint projects, structured context adaptation will produce a measurable downward slope in tokens-per-LOC (the learning curve) that flat context loading does not. The effect will be larger than any v1.2 instruction-level mutation.

## The Problem With Current Context Loading

Each sprint subagent gets the same context recipe regardless of project maturity:

1. SKILL.md (full workflow instructions)
2. PRD.md (full product spec)
3. docs/ROADMAP.md
4. Previous sprint baseline
5. progress.md (accumulated learnings, grows linearly)
6. Previous sprint retro
7. flowstate.config.md
8. All skill files

By sprint 15, the agent already knows the framework, the conventions, the test patterns. But it still reads the full PRD, the full SKILL.md, and a progress.md that's now 3000+ words of accumulated text. Meanwhile, the context budget it actually needs — the 3-5 source files relevant to this phase — competes with all that boilerplate.

## Proposed Interventions (Three Mutations)

### Mutation 1: Learning Distillation

**Current behavior:** progress.md grows by appending new learnings every sprint. Never pruned.

**Mutation:** Every 5 sprints, distill accumulated learnings into a compact, ranked project-specific skill file at `.claude/skills/project-learnings.md`. Cap at 30 rules. Each rule gets a confidence score based on how many sprints it was relevant to. Low-confidence rules get dropped at next distillation.

**What the optimizer can tune:**
- Distillation frequency (every 3, 5, or 7 sprints)
- Max rules (20, 30, 50)
- Confidence threshold for pruning
- Whether distillation replaces progress.md learnings section or supplements it

**Mechanism:** Reduces noise in context. A ranked, pruned list of 30 rules is more actionable than 100 unstructured paragraphs.

### Mutation 2: Maturity-Aware Context Loading

**Current behavior:** Sprint 2 and sprint 18 read the same files in the same order.

**Mutation:** After sprint N (configurable, default 5), change the context loading recipe:
- PRD.md: skip (agent already internalized it; roadmap has the remaining scope)
- SKILL.md: load a slim version that omits Sprint 0 setup, decision batching boilerplate, and test labeling definitions (the agent knows these by now)
- Add: pre-load the source files that will be modified this sprint (inferred from roadmap phase description + git log of recent changes)
- Add: load the last gate failure log if gates failed last sprint

**What the optimizer can tune:**
- The sprint number where maturity mode activates (3, 5, 8)
- Which sections of SKILL.md to trim
- How many source files to pre-load (0, 3, 5)
- Whether to include git diff summary of last sprint

**Mechanism:** Frees context budget for the actual work. Replaces "read everything" with "read what matters for this sprint."

### Mutation 3: Codebase Map Injection

**Current behavior:** The agent discovers the codebase structure by reading files during Phase 1.

**Mutation:** Generate a codebase map after each sprint (file tree + one-line description of each module + dependency graph). Inject it into the sprint subagent prompt. The map is regenerated each sprint so it stays current.

**What the optimizer can tune:**
- Map format (tree only, tree + descriptions, tree + descriptions + dependency edges)
- Map scope (all files, source only, source + test)
- Whether to include LOC counts per file
- Max map size (lines)

**Mechanism:** The agent spends significant early-sprint time orienting ("what files exist, what do they do, what depends on what"). A pre-built map eliminates this exploration overhead entirely.

## Primary Metric: Learning Curve Slope

**Definition:** For each project, compute tokens-per-LOC at each sprint. Fit a simple linear regression. The slope is the learning curve — negative means the agent is getting more efficient over time.

**Why this metric:** Composite score is too noisy for this question. Tokens-per-LOC directly measures "how much work did the agent waste per unit of output." A mutation that helps the agent work more fluently in a familiar codebase should show up as a steeper negative slope.

**Secondary metrics:**
- Time-to-first-gate-pass per sprint (does the agent get faster at writing code that passes gates?)
- Context compressions per sprint (does better context loading reduce the need for compressions?)
- Rework rate per sprint (does the agent rewrite less code as the project matures?)

## Design Options

### Option A: Within-Project A/B (Simplest)

Run 4 projects to ~20 sprints each. For each project:
- Sprints 1-10: flat context loading (control)
- Sprints 11-20: adapted context loading (treatment)

Compare learning curve slope in the two halves. Simple, but confounded by project maturity (later sprints may be inherently different regardless of treatment).

### Option B: Matched-Pair Crossover

Run 4 products, each built twice:
- Build 1: flat context for all 20 sprints
- Build 2: adapted context for all 20 sprints

Compare learning curves between matched builds. Stronger design but 2x the cost (8 full builds, ~160 sprints).

### Option C: Staggered Activation

Run 4 products, each built once. Randomly assign each product an activation sprint (5, 8, 10, or 12) where adapted context turns on. Compare pre-activation and post-activation slopes within each product, using the variable activation point to separate treatment effect from maturity effect.

Lower cost than Option B, better controlled than Option A.

## Prerequisites

Before running this experiment:

1. **Finish the v1.2 experiment.** The noise floor data from the replicates is needed to set decision thresholds here.
2. **Implement the learning curve metric.** Add tokens-per-LOC slope calculation to the MCP tools or a standalone script.
3. **Build the context adaptation machinery.** The mutations above require changes to Auto-Continue (the subagent launch prompt) and possibly a new tool for codebase map generation.
4. **Decide on the SKILL.md slim version.** This needs to be written and validated before the experiment — it's not something the optimizer should generate on the fly.

## Relationship to the Optimizer

These mutations are designed to fit the existing hill-climbing optimizer infrastructure:
- Each mutation modifies a specific, identifiable part of the workflow
- Each can be proposed, applied, and reverted
- Each has a clear metric to evaluate against
- The evaluation window is longer (10-20 sprints, not 3-6) — the optimizer's `MAX_SPRINTS_PER_EXPERIMENT` would need to increase for this class of mutation

The optimizer itself would need a new category of mutation: `context_loading` alongside the existing `process`, `gate_config`, and `model_routing` types.

## Expected Outcomes

**Optimistic:** Adapted context loading produces a 15-25% steeper learning curve (tokens-per-LOC drops faster over sprints). This would mean sprint 15 is meaningfully cheaper than sprint 5, compounding across all projects.

**Realistic:** Mutation 1 (learning distillation) shows a small effect. Mutations 2-3 are harder to detect because the agent already adapts somewhat on its own by reading the codebase.

**Pessimistic:** LLM stochasticity swamps the signal again. The agent's efficiency is dominated by the inherent difficulty of each phase, not by how well it knows the codebase. If so, the finding is still valuable: context loading doesn't matter as much as we thought, and the effort should go elsewhere (better tools, better decomposition, better models).
