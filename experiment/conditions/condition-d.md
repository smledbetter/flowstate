---
name: flowstate
description: Flowstate sprint process — planning, execution, shipping, and metrics workflow. Invoked when the user says "go", "start", "next sprint", or "run a sprint".
---

# Flowstate Sprint Workflow

This project uses the Flowstate sprint process. When the user says "go" (or any variation like "start", "next sprint", "continue"), follow this workflow.

## File Locations

- **Flowstate dir**: `{FLOWSTATE}/`
- **Config**: `{FLOWSTATE}/flowstate.config.md` (quality gates, agent strategy)
- **Baselines**: `{FLOWSTATE}/metrics/baseline-sprint-N.md`
- **Retrospectives**: `{FLOWSTATE}/retrospectives/sprint-N.md`
- **Metrics**: `{FLOWSTATE}/metrics/`
- **Metrics collection**: Use `mcp__flowstate__collect_metrics` MCP tool
- **Progress**: `{FLOWSTATE}/progress.md` (operational state for next session)
- **Decisions**: `{FLOWSTATE}/decisions-pending.md` (ambiguities logged during sprints)
- **Roadmap**: `docs/ROADMAP.md` (in this repo -- create if missing)
- **Skills**: `.claude/skills/` (in this repo)
- **Mission Control slug**: `flowstate` (used for MCP calls to update project dashboard)

## How to Determine the Next Sprint

1. If no `docs/ROADMAP.md` exists, this is Sprint 0 (see below).
2. Read `docs/ROADMAP.md` -- find the first phase not marked done.
3. Find the highest-numbered baseline in `{FLOWSTATE}/metrics/` -- that's your sprint number.
4. Read that baseline for starting state and gate commands.

---

## Sprint 0: Project Setup (planning only -- no code)

Sprint 0 produces the roadmap, baseline, and conventions that all future sprints depend on. No application code is written. It still gets full metrics tracking.

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
   - Phases that are mostly research or refactoring will be smaller. Phases that build new features from scratch will be larger.
   - Budget for test code: tests are typically 40-50% of total LOC. A 1000-LOC feature is really ~1500-2000 LOC with tests.
   - Number phases starting from 1 (Sprint 0 is this planning sprint).
   - Include a "Current State" section at the top (tests, coverage, LOC, milestone status).

3. **Fill in the Conventions section** in `CLAUDE.md`:
   - Language, framework, test runner
   - Lint rules and coverage floors
   - Coding standards specific to this stack
   - Any constraints from the PRD (e.g., "no .unwrap() on network data", "strict mode")
   - Known issues and gotchas discovered during gate verification

4. **Set up permissions** in `.claude/settings.json`:
   - If the file already exists, merge the `permissions` key into it (preserve existing hooks, env, etc.)
   - If it doesn't exist, create it
   - Required permissions block:
     ```json
     {
       "permissions": {
         "allow": [
           "mcp__acp__Bash",
           "mcp__acp__Edit",
           "mcp__acp__Write"
         ]
       }
     }
     ```
   - This allows future sprints to run without manual permission approval

5. **Write the initial baseline** at `{FLOWSTATE}/metrics/baseline-sprint-1.md`:
   - Current git SHA, test count (0 if greenfield), coverage status
   - Gate commands and whether each passes right now

6. **Commit**: `git add -A && git commit -m "sprint 0: project setup"`

7. **Pause for human review.** The roadmap is the foundation — if it's wrong, every sprint builds on a bad plan. Say: "Sprint 0 complete. Review the roadmap at `docs/ROADMAP.md` and the baseline, then say 'go' to continue." Wait for the human before proceeding to Phase 3.

**Phase 3: SHIP**

Sprint 0's Phase 3 follows the same steps as all sprints but with these differences:
- `tests_total`: 0 (or current count if pre-existing)
- `tests_added`: 0
- `coverage_pct`: null
- `loc_added`: LOC from git diff --stat (roadmap, baseline, conventions -- not application code)
- `gates_first_pass`: null (no code gates to run)
- `gates_first_pass_note`: "planning sprint -- no code gates"

Then follow the Phase 3: SHIP steps below (skip steps that Sprint 0 already completed).

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
- Cross-project lessons (if provided in your launch prompt -- see below)

### Cross-Project Learnings

If your launch prompt includes a "Cross-Project Learnings" section, read it. These are patterns learned from other Flowstate projects, ranked by confidence. Apply them where relevant to this sprint. Do not apply lessons that conflict with this project's specific conventions in CLAUDE.md.

### Scope Check (do this FIRST)

Read the roadmap phase for this sprint. Estimate: how many source files will be created or modified?
- If ≤5 files AND no new external dependencies: use **LIGHT MODE**.
  Skip Gherkin, skip formal wave planning. List what you'll build, implement directly, run `/gate` continuously.
- If >5 files OR new external dependencies: use **FULL MODE** (continue below).

### Feasibility Check (both modes)

- List every new external dependency this sprint requires (libraries, APIs, services)
- For each: verify it exists in the registry, check version compatibility, confirm the API you need is available
- Identify the single highest-risk technical task. Run a minimal spike (import, compile, call the API) to confirm it works
- If any dependency is unverified or experimental, FLAG IT NOW with a fallback plan. If no fallback exists, log as `[BLOCKING]` in `{FLOWSTATE}/decisions-pending.md` and pause for human input.
- If the spike fails, revise the scope before proceeding. If the revision changes what the sprint delivers, log the decision to `{FLOWSTATE}/decisions-pending.md`.
- Confirm a formatter AND linter are configured as gates in `{FLOWSTATE}/flowstate.config.md`. If either is missing, set one up now.

### THINK (FULL MODE)

Write your implementation plan directly (do NOT use Claude Code's plan mode — permissions are already set). Consider all skill perspectives (PM, UX, Architect):

1. Write acceptance criteria in Gherkin format for the phase scope. Every requirement must have at least one happy-path and one failure/edge-case scenario.
2. Produce an implementation plan grouped by file dependency (tasks sharing no files can be parallel).
3. For each task: files to read, files to write.

### Multi-Agent Strategy (FULL MODE)

Document your strategy choice in the plan:
- **Sequential (default):** Implement in the main session. Best when files reference each other or total LOC < 800.
- **Subagents:** Use `Task` tool with `isolation: "worktree"` for 2-3 independent packages that share no files. Each subagent gets its own copy of the repo.
- **Teams:** Use `TeamCreate` + named teammates for large sprints (1200+ LOC) with 3+ genuinely independent workstreams.

### Test Labeling

Label tests honestly by what they actually verify:
- **Unit test**: tests a single function/module in isolation, mocks external dependencies.
- **Integration test**: tests composition of multiple modules or stages together. Proves they connect correctly.
- **End-to-end test**: starts the system in its actual deployment configuration, sends input through the real entry point, asserts output through the real exit point. Runs against a live (or realistic) environment, not mocked stages.

Do NOT call a one-shot integration test "end-to-end" — this creates false confidence. If a system runs continuously (pipelines, servers, watchers), an E2E test must run it continuously too.

### EXECUTE

Implement:
- **Lint pre-check**: Before running `/gate`, run the lint/format command from `{FLOWSTATE}/flowstate.config.md` independently. If it fails, fix lint errors FIRST, then run `/gate`. This prevents the most common gate failure (31% of all gate failures are lint/format issues).
- Log whether lint found errors: write `lint_activated: true/false` and a one-line error summary to `{FLOWSTATE}/metrics/sprint-N-lint-log.txt`
- Run `/gate` after every meaningful change -- not batch-at-end
- Commit atomically after completing logical units of work
- If any gate fails: classify as REGRESSION (test existed before) or FEATURE (new test), fix, re-run, max 3 cycles
- Save gate output to `{FLOWSTATE}/metrics/sprint-N-gates.log`
- Optional preventive gates (run after core gates pass, if Flowstate repo is available):
  - `bash "${FLOWSTATE_REPO:-$HOME/Sites/Flowstate}"/tools/deps_check.sh` (verify new deps exist in registry)
  - `bash "${FLOWSTATE_REPO:-$HOME/Sites/Flowstate}"/tools/sast_check.sh` (static security analysis)
  - `bash "${FLOWSTATE_REPO:-$HOME/Sites/Flowstate}"/tools/deadcode_check.sh` (detect unused exports/deps)

When all gates pass, **proceed directly to Phase 3** — do not pause for human approval.

### Pipeline Buffering Convention

If any script outputs to stdout in a pipeline (pipes to another process), it must flush after every line. Without explicit flush, stdout is block-buffered (~4KB) when piped — messages stall between stages until the buffer fills or the process exits. One-shot tests mask this because process exit flushes all buffers.

| Language | Unbuffered stdout |
|----------|-------------------|
| Python | `print(..., flush=True)` or `PYTHONUNBUFFERED=1` or `python -u` |
| Bash | Use `stdbuf -oL script.sh` or write via python. Avoid bare `printf` in pipes |
| Ruby | `$stdout.sync = true` or `STDOUT.flush` after each write |
| Perl | `$\| = 1` (set autoflush on current output handle) |
| Node.js | `process.stdout` is unbuffered by default (not affected) |
| Go | `fmt.Println` to os.Stdout is unbuffered. `bufio.Writer` requires explicit `Flush()` |
| C | `setlinebuf(stdout)` or `fflush(stdout)` after each write |
| Rust | `io::stdout().flush()` or `BufWriter` with explicit flush |

---

## Phase 3: SHIP

1. **Collect metrics** using Flowstate MCP tools:
   - Call `mcp__flowstate__sprint_boundary` with project_path and sprint_marker to find the boundary timestamp
   - Call `mcp__flowstate__list_sessions` with project_path to find the session ID(s) for this sprint
   - Call `mcp__flowstate__collect_metrics` with project_path, session_ids, and the boundary timestamp as "after"
   - Save the raw metrics response to `{FLOWSTATE}/metrics/sprint-N-metrics.json`

2. **Write import JSON** at `{FLOWSTATE}/metrics/sprint-N-import.json`:
   - Start from the MCP metrics response (`sprint-N-metrics.json`) as the base
   - Add these fields:
     ```json
     {
       "project": "{SLUG}",
       "sprint": N,
       "label": {LABEL_EXAMPLE},
       "phase": "[phase name from roadmap]",
       "metrics": {
         "...everything from sprint-N-metrics.json...",
         "tests_total": "<current test count>",
         "tests_added": "<tests added this sprint>",
         "coverage_pct": "<current coverage % or null>",
         "lint_errors": 0,
         "gates_first_pass": "<true|false>",
         "gates_first_pass_note": "<note if false, empty string if true>",
         "loc_added": "<LOC from git diff --stat>",
         "loc_added_approx": false,
         "task_type": "<feature|bugfix|refactor|infra|planning|hardening>",
         "rework_rate": "<from sprint-N-metrics.json, or null>",
         "judge_score": "<[scope, test_quality, gate_integrity, convention, diff_hygiene] 1-5 each, or null>",
         "judge_blocked": "<true if judge prevented stopping, false otherwise, or null>",
         "judge_block_reason": "<reason string if blocked, or null>",
         "coderabbit_issues": "<number of CodeRabbit issues on PR, or null>",
         "coderabbit_issues_valid": "<number human agreed were real, or null>",
         "mutation_score_pct": "<mutation score if run, or null>",
         "delegation_ratio_pct": "<from sprint-N-metrics.json — subagent tokens / total tokens %, or null if no subagents>",
         "orchestrator_tokens": "<from sprint-N-metrics.json>",
         "subagent_tokens": "<from sprint-N-metrics.json>",
         "context_compressions": "<from sprint-N-metrics.json — number of context compression events>"
       }
     }
     ```
   - The schema matches `sprints.json` entries exactly -- same field names, same types
   - Validate: call `mcp__flowstate__import_sprint` with dry_run=true
   - Fix any errors before proceeding. Warnings (auto-corrections) are ok.

3. **Write retrospective** at `{FLOWSTATE}/retrospectives/sprint-N.md`:
   - What was built (deliverables, test count, files changed, LOC)
   - Metrics comparison vs previous sprint (see baseline)
   - What worked / what failed, with evidence

   **Sprints 1-8 (establishing)** — full retro:
   - Quality audit: check these 4 fixed instructions for compliance.
     These are mechanically verifiable -- grep the new/modified source files for evidence.
     a. TESTS EXIST: every new source file has a corresponding test file with at least 1 test.
        PASS: test file exists and covers new code. FAIL: new source file with no tests.
     b. NO SECURITY ANTI-PATTERNS: no eval(), new Function(), or unescaped template
        literals in user-facing paths in new/modified code.
        PASS: grep returns empty. FAIL: grep finds matches in non-test files.
     c. COVERAGE DID NOT REGRESS: compare current coverage % to baseline.
        PASS: coverage >= baseline. FAIL: coverage dropped.
     d. PRODUCTION SHAPE TESTED: if any new/modified component has a long-running mode
        (--watch, --daemon, --serve, polling loop, persistent connection, piped pipeline),
        at least one test starts it as a background process, sends real input, and verifies
        output arrives within a bounded wait (e.g., 10 seconds).
        PASS: background/continuous test exists for each long-running component, OR N/A (no long-running components).
        FAIL: all tests use one-shot/exit mode for a component meant to run continuously.
     For each, quote file:line evidence.
   - Skill relevance audit: review each skill file (.claude/skills/*.md). For each rule, classify as USED (cite the decision) or UNUSED. If a rule has been UNUSED for 4+ consecutive sprints, flag as STALE CANDIDATE.
   - Change proposals as diffs (with `- Before` / `+ After` blocks). Prefer REMOVING or SIMPLIFYING instructions over adding new ones.

   **Sprints 9+ (mature)** — slim retro:
   - If gates passed first try and coverage did not regress: write "No retro issues — gates passed, conventions held." Skip the quality audit, skill audit, and change proposals.
   - If a gate failed or coverage regressed: include the quality audit (4 checks above) and a change proposal ONLY for what broke. Still skip the skill relevance audit.

4. **Carry learnings forward:**
   - **Skill/convention change proposals** (modifying `.claude/skills/*.md` or `CLAUDE.md`): Do NOT apply. These stay in the retro for human review. Auto-Continue will pause if any exist.
   - **Operational learnings** ("this test pattern worked", "avoid X with this framework", "this API has a quirk"): Write these into `{FLOWSTATE}/progress.md` under a "Learnings" section. The next sprint subagent reads progress.md and inherits them automatically.

5. **Commit**: `git add -A && git commit -m "sprint N: [description]"`

6. **Update Mission Control** (if `mcp__mission_control__update_project_status` is available):
   - Call `mcp__mission_control__update_project_status` with:
     - `slug`: `flowstate`
     - `status`: "running" (or "complete" if this was the last phase in the roadmap)
     - `next_step`: what the next sprint will build (from roadmap), or "Deploy and configure" if roadmap is done
   - Call `mcp__mission_control__update_step` for the just-completed phase:
     - `slug`: `flowstate`
     - `step_title`: the phase title (match it to the step in Mission Control)
     - `status`: "done"
   - If the MCP server is unreachable, log a warning and continue — this is best-effort, never blocking.

7. **Write next baseline** at `{FLOWSTATE}/metrics/baseline-sprint-{N+1}.md`:
   - Current git SHA, test count, coverage %, lint error count
   - Gate commands and current status
   - Quality audit uses the 4 fixed instructions above -- no rotation needed

8. **Update roadmap**: mark this phase done in `docs/ROADMAP.md`, update Current State section

9. **Record lessons to DuckDB** (if `mcp__flowstate__record_lesson` is available):
   - For each NEW learning added to progress.md this sprint (not carried-forward ones):
     call `mcp__flowstate__record_lesson` with `text`, `category` (one of: gate, framework, testing, performance, convention, tooling), `source_project`, `source_sprint`
   - If the MCP tools are unreachable, skip — this is best-effort, never blocking.

10. **Write progress file** at `{FLOWSTATE}/progress.md`:
   - **First, read the existing `{FLOWSTATE}/progress.md`** (if it exists) to extract the accumulated Learnings section. Do not skip this step — learnings compound across sprints and losing them degrades future sprint quality.
   - Then write the new progress.md with:
     - What was completed this sprint (list of deliverables)
     - What failed or was deferred (and why)
     - What the next session should do first
     - Any blocked items or external dependencies awaiting resolution
     - Current gate status (all passing? which ones?)
     - **Learnings** (accumulated): copy ALL prior learnings from the old progress.md, then append new ones from this sprint. Patterns that worked, pitfalls to avoid, framework quirks. This section only grows — never remove entries unless they're proven wrong.
   This is operational state for the next agent session, not analysis.

11. **Completion check** -- print this checklist with [x] or [MISSING] for each:
   - `{FLOWSTATE}/metrics/sprint-N-metrics.json` exists (raw MCP metrics response)
   - `{FLOWSTATE}/metrics/sprint-N-import.json` exists (complete import-ready JSON, validated via MCP dry_run)
   - `{FLOWSTATE}/retrospectives/sprint-N.md` contains:
     - Deliverables, metrics comparison, what worked/failed
     - **Sprints 1-8**: quality audit (4 checks), skill relevance audit, change proposal (or "no changes needed")
     - **Sprints 9+**: "No retro issues" line if gates passed first try, OR quality audit + change proposal for what broke
   - `{FLOWSTATE}/metrics/baseline-sprint-{N+1}.md` exists with SHA, tests, coverage, gates
   - `{FLOWSTATE}/progress.md` written (current state for next session)
   - `docs/ROADMAP.md` updated (phase marked done, Current State refreshed)
   - Sprint code committed
   - Mission Control updated (status + step marked done), or "MCP unavailable" if server unreachable
   - Lessons recorded to DuckDB (new learnings from this sprint), or "MCP unavailable"
   Fix any MISSING items before declaring done.

**This sprint is now complete.** If you are running as a subagent, return control to the orchestrator. Do NOT proceed to Auto-Continue — that section runs ONLY in the main orchestrator session.

---

## Auto-Continue (orchestrator only — do NOT run this in a sprint subagent)

After Phase 3 completes, check whether to continue:

1. Read `docs/ROADMAP.md`. Is there a next phase not marked done?
   - **No** → All phases complete. Update Mission Control: `mcp__mission_control__update_project_status` with slug="flowstate", status="complete". Say "Roadmap complete. N sprints run." and stop.
   - **Yes** → Continue to step 2.

2. Check the retro just written. Does it contain change proposals (diffs with `- Before` / `+ After`)?
   - **Yes** → Pause. Say "Sprint N complete. Retro has change proposals — review before continuing." Show the proposals. Wait for human.
   - **No** → Continue to step 3.

3. Check `{FLOWSTATE}/decisions-pending.md`. If it has 5+ unresolved decisions, or any marked `[BLOCKING]`, pause and present them to the human for review.

4. **Milestone checkpoint (infrastructure projects).** If the just-completed sprint finishes a milestone (all phases in that milestone are now done) AND the project has infrastructure components (Docker, networking, services, long-running pipelines), pause for human smoke-testing. Say: "Milestone MN complete. Infrastructure projects need human smoke-testing before continuing. Verify the deployment works end-to-end, then say 'go' to continue." Feature-only projects (no infrastructure) skip this check.

5. **Auto-import metrics.** Before launching the next sprint, import the just-completed sprint's metrics so they aren't lost if the session ends unexpectedly:
   - Validate: call `mcp__flowstate__import_sprint` with the import JSON path and `dry_run=true`
   - If valid: call `mcp__flowstate__import_sprint` with `dry_run=false` to write to sprints.json
   - If validation fails: log a warning in progress.md but don't block — the human can import manually later

6. **Gather cross-project lessons.** If `mcp__flowstate__get_lessons` is available, call it with the current project slug. Include the returned lessons in the subagent prompt as a "Cross-Project Learnings" section.

7. **Launch the next sprint as a subagent.** Use `Task` with `subagent_type: "general-purpose"` and `mode: "bypassPermissions"`. Pass a prompt containing:
   - The project path and `{FLOWSTATE}` path
   - "Read `.claude/skills/flowstate/SKILL.md`. Run Sprint N+1: Phase 1+2 (THINK then EXECUTE) and Phase 3 (SHIP)."
   - "Read `{FLOWSTATE}/progress.md` for handoff state and accumulated learnings from previous sprints."
   - The cross-project lessons from step 6 (if any)
   - "Stop after the Phase 3 completion check. Do NOT run Auto-Continue."

   **Architecture rules:**
   - Each sprint subagent runs exactly ONE sprint (Phase 1+2+3) and returns
   - The subagent reads state from files (progress.md, baseline, roadmap) and writes state to files (progress.md, baseline, retro, metrics)
   - Auto-Continue runs ONLY here in the orchestrator — never inside a subagent
   - This keeps nesting flat (max 2 levels: orchestrator → sprint subagent) and prevents unbounded recursion

   When the subagent completes, read the updated `{FLOWSTATE}/progress.md` and `docs/ROADMAP.md`, then repeat from step 1.

   **Why subagents:** Each sprint consumes ~270K new-work tokens. Running multiple sprints in the same context window causes degradation. Fresh context per sprint keeps quality consistent. Learnings propagate via progress.md (within-project) and DuckDB lessons (cross-project).

---

## Decision Batching

When you encounter an ambiguity or design question during a sprint:

1. **Don't block.** Pick the most reasonable default and continue.
2. **Log it.** Append to `{FLOWSTATE}/decisions-pending.md`:
   ```
   ### Sprint N — [short description]
   **Question**: [what's ambiguous]
   **Default chosen**: [what you went with and why]
   **Impact if wrong**: [what would need to change]
   **Status**: PENDING
   ```
   Mark as `[BLOCKING]` only if no safe default exists and continuing would waste significant work.
3. **Keep building.** The human reviews pending decisions at natural checkpoints (see Auto-Continue step 3) or when a `[BLOCKING]` decision forces a pause.

Decisions that are NOT ambiguities (don't log these):
- Implementation details with one obvious answer
- Library/API choices where one clearly fits
- Code structure that follows established project patterns

Decisions that ARE ambiguities (log these):
- Product behavior the PRD doesn't specify ("should this be a modal or a page?")
- Trade-offs between conflicting requirements
- Scope questions ("the PRD says X but that implies Y — should we build Y too?")
- External dependency choices with no clear winner
