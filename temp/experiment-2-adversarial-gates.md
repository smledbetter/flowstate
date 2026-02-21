# Experiment 2: Adversarial Gate Test

## Hypotheses Targeted

- **H5**: Quality gates catch regressions before shipping
- **H8**: Structured sprint process reduces defect rate
- **H9**: Gate-fixing cycles converge within 3 attempts

## Setup

Branch: `exp-2-adversarial` (Uluka repo)
Commit: 903939b ("refactor: adjust verification thresholds and imports")

Three bugs planted:

| # | File | Bug | Expected Gate |
|---|------|-----|---------------|
| 1 | `src/cli/commands/verify.ts:7` | Unused `import { strict as assert } from "assert"` | Gate 2: `tsc --noUnusedLocals` |
| 2 | `src/verifiers/confidence-booster.ts:39` | `>= 0.8` changed to `> 0.9` (logic threshold) | Gate 3: `vitest` (test expects `'high'`, gets `'medium'`) |
| 3 | `src/verifiers/verification-engine.ts:71` | `.some()` changed to `.find()` (returns `Finding \| undefined` not `boolean`) | Gate 1: `tsc --noEmit` (type error) |

## Sprint Prompt

Run this in a fresh Claude Code session in `/Users/stevo/Sites/Uluka`, on the `exp-2-adversarial` branch.

The sprint uses Phase 21 (Crypto Library Knowledge Base) as the real work — the agent should discover the bugs during gate checks, not during implementation.

### Phase 1+2

```
You are running a Flowstate sprint for Uluka Phase 21 (Crypto Library Knowledge Base + Evidence Quality).

Read these files:
- docs/ROADMAP.md (this sprint's phase)
- ~/.flowstate/uluka/metrics/baseline-sprint-7.md (current state: tests, coverage, lint)
- ~/.flowstate/uluka/progress.md (if exists — operational state from last session)
- ~/.flowstate/uluka/flowstate.config.md (quality gates)
- ~/.flowstate/uluka/retrospectives/sprint-6.md (last retro, if exists)
- All skill files in .claude/skills/

PHASE 1 — THINK:
Acting as a consensus agent with all 5 skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor):

0. FEASIBILITY CHECK (do this BEFORE planning):
   - List every new external dependency this sprint requires (libraries, APIs, services)
   - For each: verify it exists in the registry, check version compatibility, confirm the API you need is available
   - Identify the single highest-risk technical task. Run a minimal spike (import, compile, call the API) to confirm it works
   - If any dependency is unverified or experimental, FLAG IT NOW with a fallback plan
   - If the spike fails, revise the scope before proceeding
   - Confirm a formatter AND linter are configured as gates in flowstate.config.md. If either is missing, set one up now before writing any code.

1. Produce acceptance criteria (Gherkin format) for this sprint's scope:
   - Library registry mapping library names to import patterns, algorithms, and security properties
   - Import-based detection for crypto libraries (vodozemac, libsodium, noble-curves, tweetnacl, webcrypto, PyCryptodome)
   - Weak algorithm warnings (MD5, SHA-1, DES, RC4) as findings
   - Test file exclusion from evidence confidence scoring
   - Import-usage validation (imported but not called = lower confidence)
   Every requirement must have at least one happy-path and one failure/edge-case scenario.

2. Produce an implementation plan with wave-based execution:
   - Group tasks into waves by file dependency (tasks sharing no files can be parallel)
   - For each task: files read, files written, agent model (haiku for mechanical, sonnet for reasoning)

PHASE 2 — EXECUTE:
Immediately after producing the plan, execute it. Do NOT wait for human approval between planning and execution.

- Spawn subagents per wave as specified in the implementation plan
- Each subagent gets: file path references (not content), task scope, relevant skill context
- Commit atomically after each wave
- Do NOT read full implementation files into your orchestrator context — delegate reading to subagents
- After all waves complete, run these quality gates IN ORDER:

Gate 1: npx tsc --noEmit
Gate 2: npx tsc --noEmit --noUnusedLocals
Gate 3: npx vitest --run
Gate 4: npx vitest --run --coverage
Gate 5 (smoke test): npx tsx bin/uluka.js scan --format json src/ 2>&1 | head -5

Save gate output to ~/.flowstate/uluka/metrics/sprint-8-gates.log.

If any gate fails:
- Classify each failure as REGRESSION (existed before this sprint) or FEATURE (new code). Compare against the baseline.
- Fix the issue, re-run that gate, max 3 cycles. If still failing after 3 cycles, stop and report.

When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."
```

### Phase 3

```
Run the Phase 3 retrospective for Sprint 8.

1. Collect metrics using Flowstate MCP tools:
   a. Call mcp__flowstate__sprint_boundary with project_path="/Users/stevo/Sites/Uluka"
   b. Call mcp__flowstate__list_sessions with project_path="/Users/stevo/Sites/Uluka"
      Pick the session(s) that cover this sprint's time range.
   c. Call mcp__flowstate__collect_metrics with project_path, session_ids, and the boundary timestamp as "after"
   d. Save the raw metrics response to ~/.flowstate/uluka/metrics/sprint-8-metrics.json

2. Write import JSON at ~/.flowstate/uluka/metrics/sprint-8-import.json:
   - Start from the MCP metrics response as the base
   - Add these fields:
     {
       "project": "uluka",
       "sprint": 8,
       "label": "Sprint 8: Crypto registry + evidence quality",
       "phase": "Phase 21: Crypto Library Knowledge Base + Evidence Quality",
       "metrics": {
         "...everything from sprint-8-metrics.json...",
         "tests_total": "<current>",
         "tests_added": "<added this sprint>",
         "coverage_pct": "<current>",
         "lint_errors": 0,
         "gates_first_pass": "<true|false>",
         "gates_first_pass_note": "<note if false>",
         "loc_added": "<from git diff --stat>",
         "loc_added_approx": false,
         "task_type": "feature",
         "delegation_ratio_pct": "<subagent tokens / total tokens %>",
         "context_compressions": "<count>"
       },
       "hypotheses": [
         {"id": "H1", "name": "3-phase structure", "result": "...", "evidence": "..."},
         {"id": "H5", "name": "Quality gates", "result": "...", "evidence": "..."},
         {"id": "H7", "name": "Skill compliance", "result": "...", "evidence": "..."}
       ]
     }
   - Validate: call mcp__flowstate__import_sprint with the import JSON path and dry_run=true

3. Write ~/.flowstate/uluka/retrospectives/sprint-8.md with:
   - What was built
   - Metrics comparison vs Sprint 7 baseline
   - What worked / what failed
   - H7 audit (5 instructions from baseline-sprint-7.md), dual verification (process + code checks)
   - Hypothesis results table
   - Change proposals as diffs

4. Do NOT apply skill changes. Commit the sprint's code:
   git add -A && git commit -m "sprint 8: crypto registry + evidence quality"

5. Write baseline-sprint-9.md, update ROADMAP.md, write progress.md.

6. COMPLETION CHECK before declaring done.
```

## Results

### Bug Detection Scorecard

| Bug | Caught by gate? | Gate # | Correctly identified root cause? | Correctly fixed? | Classified as REGRESSION? | Cycles to fix |
|-----|-----------------|--------|----------------------------------|-------------------|---------------------------|---------------|
| 1. Unused `assert` import | Yes | Gate 2 (`tsc --noUnusedLocals`) | Yes — identified as unused import from refactor | Yes — removed the import | Yes — traced to commit `903939b` | 1 |
| 2. Confidence threshold `> 0.9` | Yes | Gate 3 (`vitest`) | Yes — identified wrong threshold | Yes — restored `>= 0.8` | Yes — traced to commit `903939b` | 1 |
| 3. `.find()` type error | Yes | Gate 1 (`tsc --noEmit`) | Yes — `Finding \| undefined` not assignable to `boolean` | Yes — changed back to `.some()` | Yes — traced to commit `903939b` | 1 |

**All 3 bugs caught. All 3 correctly fixed. All 3 traced to the planted commit. Total fix cycles: 1 (all fixed in a single pass).**

### Key Questions Answered

1. **Did the agent classify the bugs as REGRESSION?** — Yes, but incorrectly called them "FEATURE regression" in the retro (meaning "a regression introduced by a feature refactor commit"). The classification is semantically correct (pre-existing bugs from a prior commit, not from Phase 21 work) but uses non-standard terminology.
2. **Did the agent notice the bugs were unrelated to Phase 21?** — Yes. The retro explicitly states all 3 came from commit `903939b` ("refactor: adjust verification thresholds and imports"), which is separate from the Phase 21 implementation.
3. **Did the agent fix them correctly?** — Yes, all 3 restored to their original correct implementations.
4. **Did `gates_first_pass` get marked as `false`?** — Yes. The import JSON has `"gates_first_pass": false` with a note explaining the 3 regressions.

### Hypothesis Results

| Hypothesis | Result | Evidence |
|------------|--------|----------|
| **H5**: Quality gates catch regressions | **CONFIRMED** | 3/3 planted bugs caught by gates (type check, lint, tests). Each gate caught exactly the bug it was designed for. |
| **H8**: Structured process reduces defects | **CONFIRMED** | The agent completed Phase 21 (1,078 LOC, 42 tests) AND fixed 3 pre-existing bugs, shipping clean code. Without gates, all 3 bugs would have shipped. |
| **H9**: Gate-fixing cycles converge within 3 attempts | **CONFIRMED** | All 3 bugs fixed in cycle 1 of 3 allowed. Root causes correctly identified on first inspection. |

### Sprint Metrics

- Active time: 10m 28s
- Total tokens: 4.2M (212K new-work)
- Cache hit: 95%
- LOC: 1,078 added
- Tests: 478 -> 520 (+42)
- Coverage: 73.14% -> 73.91%

### Notable Observations

1. **Gate ordering matters**: Bug 3 (type error) was caught by Gate 1 before the agent even reached Gates 2-3. This is the correct behavior — type errors block compilation and should fail fast.
2. **The agent proposed process improvements**: The retro suggested always running gates before committing refactors, and re-running THINK phase in continuation sessions. Both are reasonable responses to discovering pre-existing bugs.
3. **No false fixes**: The agent didn't "fix" the bugs by changing tests to match the buggy code. It correctly identified the code as wrong and the tests as correct.
