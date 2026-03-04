---
name: flowstate
description: Flowstate sprint process (Tier 2) — planning, execution, shipping with sanitized export. No automated metrics.
---

# Flowstate Sprint Workflow (Tier 2)

This project uses the Flowstate sprint process (Tier 2: skills + structure, no automated metrics). Metrics are agent-estimated. The retro produces a sanitized export that the human brings back to the Flowstate repo.

## File Locations

- **Flowstate dir**: `{FLOWSTATE}/`
- **Config**: `{FLOWSTATE}/flowstate.config.md` (quality gates, agent strategy)
- **Baselines**: `{FLOWSTATE}/metrics/baseline-sprint-N.md`
- **Retrospectives**: `{FLOWSTATE}/retrospectives/sprint-N.md`
- **Progress**: `{FLOWSTATE}/progress.md` (operational state for next session)
- **Roadmap**: `docs/ROADMAP.md` (in this repo -- create if missing)
- **Skills**: `.claude/skills/` (in this repo)

## How to Determine the Next Sprint

1. If no `docs/ROADMAP.md` exists, this is Sprint 0 (see below).
2. Read `docs/ROADMAP.md` -- find the first phase not marked done.
3. Find the highest-numbered baseline in `{FLOWSTATE}/metrics/` -- that's your sprint number.
4. Read that baseline for starting state, gate commands, and quality audit instructions.

---

## Sprint 0: Project Setup (planning only -- no code)

Sprint 0 produces the roadmap, baseline, and conventions that all future sprints depend on. No application code is written.

**Phase 1+2: RESEARCH then PLAN**

Read these files:
- `PRD.md` (fully -- every section)
- `{FLOWSTATE}/flowstate.config.md`
- All files in `.claude/skills/`

Then do ALL of the following:

1. **Verify gate commands.** Run each gate command from `{FLOWSTATE}/flowstate.config.md`. If any don't work (wrong tool, missing dependency), update them in CLAUDE.md AND in `{FLOWSTATE}/flowstate.config.md`. Record what works and what doesn't.

2. **Create `docs/ROADMAP.md`.**
   - Break PRD milestones into sprint-sized phases. Each phase = one sprint.
   - Right-sizing guide: a phase should be deliverable in 10-60 minutes of active agent time, produce 500-2500 LOC, and have a clear "done" state that gates can verify.
   - Budget for test code: tests are typically 40-50% of total LOC.
   - Number phases starting from 1 (Sprint 0 is this planning sprint).
   - Include a "Current State" section at the top (tests, coverage, LOC, milestone status).

3. **Fill in the Conventions section** in `CLAUDE.md`:
   - Language, framework, test runner
   - Lint rules and coverage floors
   - Coding standards specific to this stack
   - Any constraints from the PRD
   - Known issues and gotchas

4. **Write the initial baseline** at `{FLOWSTATE}/metrics/baseline-sprint-1.md`:
   - Current git SHA, test count (0 if greenfield), coverage status
   - Gate commands and whether each passes right now

5. **Commit**: `git add -A && git commit -m "sprint 0: project setup"`

When done, say: "Ready for Phase 3: SHIP whenever you want to proceed."

**Phase 3: SHIP**

Sprint 0's Phase 3:
1. Write `{FLOWSTATE}/retrospectives/sprint-0.md` (what was planned, gate verification results, any issues found)
2. Produce a SANITIZED EXPORT (see Phase 3 below for format)
3. Write progress file at `{FLOWSTATE}/progress.md`
4. Completion check (see Phase 3 below)

---

## Phase 1+2: THINK then EXECUTE (Sprint 1+)

Read these files first:
- `PRD.md`
- `docs/ROADMAP.md` (find this sprint's phase)
- The current baseline (see above)
- `{FLOWSTATE}/progress.md` (if exists -- operational state from last session)
- `{FLOWSTATE}/flowstate.config.md`
- The previous sprint's retro (if exists)
- All files in `.claude/skills/`

### Scope Check (do this FIRST)

Read the roadmap phase for this sprint. Estimate: how many source files will be created or modified?
- If ≤5 files AND no new external dependencies: use **LIGHT MODE**.
  Skip Gherkin, skip formal planning. List what you'll build, implement directly, run gates continuously.
- If >5 files OR new external dependencies: use **FULL MODE** (continue below).

### Feasibility Check (both modes)

- List every new external dependency this sprint requires
- For each: verify it exists in the registry, check version compatibility
- Identify the single highest-risk task. Run a minimal spike to confirm it works.
- If the spike fails, revise scope before proceeding
- Confirm a formatter AND linter are configured as gates. If either is missing, set one up now.

### THINK (FULL MODE)

Use Plan mode. Iterate until the plan is solid, considering all skill perspectives (PM, UX, Architect):

1. Write acceptance criteria in Gherkin format for the phase scope.
2. Produce an implementation plan grouped by file dependency.
3. For each task: files to read, files to write.

### Multi-Agent Strategy (FULL MODE)

Document your strategy choice in the plan:
- **Sequential (default):** Implement in the main session. Best when files reference each other or total LOC < 800.
- **Subagents:** Use for 2-3 independent packages that share no files.
- **Teams:** Use for 1200+ LOC new features with 3+ independent workstreams.

### Test Labeling

Label tests honestly by what they actually verify:
- **Unit test**: tests a single function/module in isolation, mocks external dependencies.
- **Integration test**: tests composition of multiple modules or stages together. Proves they connect correctly.
- **End-to-end test**: starts the system in its actual deployment configuration, sends input through the real entry point, asserts output through the real exit point.

Do NOT call a one-shot integration test "end-to-end" — this creates false confidence.

### Pipeline Buffering Convention

If any script outputs to stdout in a pipeline, it must flush after every line. Without explicit flush, stdout is block-buffered (~4KB) when piped — messages stall between stages.

| Language | Unbuffered stdout |
|----------|-------------------|
| Python | `print(..., flush=True)` or `PYTHONUNBUFFERED=1` |
| Bash | Use `stdbuf -oL script.sh` |
| Node.js | `process.stdout` is unbuffered by default (not affected) |
| Go | `fmt.Println` to os.Stdout is unbuffered. `bufio.Writer` requires explicit `Flush()` |

### EXECUTE

After planning, switch to auto-accept mode and implement:
- Run gates after every meaningful change -- not batch-at-end
- Commit atomically after completing logical units of work
- If any gate fails: classify as REGRESSION vs FEATURE, fix, re-run, max 3 cycles
- If bash is available, save gate output to `{FLOWSTATE}/metrics/sprint-N-gates.log`
- If not, paste the gate output into the retrospective under a "## Gate Log" section

When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."

---

## Phase 3: SHIP

1. **Write retrospective** at `{FLOWSTATE}/retrospectives/sprint-N.md`:
   - What was built (deliverables, test count, files changed)
   - What worked / what failed, with evidence
   - Quality audit: check these 4 fixed instructions for compliance (grep-verifiable):
     a. TESTS EXIST: every new source file has a corresponding test file with at least 1 test.
     b. NO SECURITY ANTI-PATTERNS: no eval(), new Function(), or unescaped template literals in user-facing paths.
     c. COVERAGE DID NOT REGRESS: current coverage >= baseline.
     d. PRODUCTION SHAPE TESTED: if any new/modified component has a long-running mode (--watch, --daemon, polling loop, persistent connection, piped pipeline), at least one test starts it as a background process, sends real input, and verifies output arrives within a bounded wait. N/A if no long-running components.
     For each, quote file:line evidence.
   - Change proposals as diffs (with `- Before` / `+ After` blocks). Prefer removing or simplifying instructions over adding new ones.

2. **Sanitized export** -- produce a markdown document starting with "# Flowstate Sanitized Sprint Export". This will leave this environment, so it must contain NO proprietary code, architecture details, file paths, business logic, or project-specific content. Only include:
   - Sprint number, language/framework, generalized scope description
   - Metrics: estimate your active session time, count subagents spawned, count tests added, gate pass/fail
   - Task type: feature, bugfix, refactor, infra, planning, or hardening
   - Quality audit results: X/4 compliance (tests exist, no security anti-patterns, coverage not regressed, production shape tested)
   - Skill change proposals GENERALIZED: strip project-specific details, describe the pattern not the implementation
   - Process observations: did the single prompt work? friction points? what would you change?

3. **Do NOT apply skill changes** -- proposals stay in the retro for human review

4. **Commit**: `git add -A && git commit -m "sprint N: [generalized description]"`

5. **Write next baseline** at `{FLOWSTATE}/metrics/baseline-sprint-{N+1}.md`:
   - Current git SHA, test count, coverage %, lint error count
   - Gate commands and current status

6. **Update roadmap**: mark this phase done in `docs/ROADMAP.md`, update Current State section

7. **Write progress file** at `{FLOWSTATE}/progress.md`:
   - What was completed this sprint (list of deliverables)
   - What failed or was deferred (and why)
   - What the next session should do first
   - Any blocked items or external dependencies awaiting resolution
   - Current gate status (all passing? which ones?)
   This is operational state for the next agent session, not analysis. Overwrite any previous progress.md.

8. **Completion check** -- print this checklist with [x] or [MISSING] for each:
   - `{FLOWSTATE}/retrospectives/sprint-N.md` has Quality audit and change proposals
   - Sanitized export produced (starting with "# Flowstate Sanitized Sprint Export")
   - `{FLOWSTATE}/metrics/baseline-sprint-{N+1}.md` exists with SHA, tests, coverage, gates
   - `{FLOWSTATE}/progress.md` written (current state for next session)
   - `docs/ROADMAP.md` updated
   - Code committed
   Fix any MISSING items before declaring done.
