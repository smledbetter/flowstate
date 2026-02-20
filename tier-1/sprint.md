# Sprint N: [Project] — [Milestone/Phase Name]

> Tier 1 sprint: full Claude Code with bash, automated metrics.
> Set `{FLOWSTATE}` = `~/.flowstate/{project-slug}` (e.g., `~/.flowstate/uluka`).
> Skills live at `.claude/skills/` in the project repo (gitignored). Everything else is in `{FLOWSTATE}/`.
> **Start each sprint in a FRESH session.** One sprint = one session.
> Multi-sprint sessions degrade metric accuracy (active time, token counts blend across sprints).
> If you must continue in an existing session, note it in the retro.

One-line description of what this sprint builds.

---

## Phase 1 + 2: THINK then EXECUTE (single prompt)

Copy-paste this prompt to start. The agent will plan AND execute without stopping.

```
You are running a Flowstate sprint for [PROJECT] [MILESTONE/PHASE].

Read these files:
- PRD.md (or README)
- docs/ROADMAP.md (this sprint's phase)
- [{FLOWSTATE}/metrics/baseline-sprint-N.md] (current state: tests, coverage, lint)
- [{FLOWSTATE}/progress.md] (if exists — operational state from last session)
- {FLOWSTATE}/flowstate.config.md (quality gates)
- [{FLOWSTATE}/retrospectives/sprint-{N-1}.md] (last retro, if exists)
- All skill files in .claude/skills/

If a previous sprint's PR was reviewed by CodeRabbit, read the review comments before planning.

PHASE 1 — THINK:

0. SCOPE CHECK (do this FIRST):
   Read the roadmap phase for this sprint. Estimate: how many source files will be created or modified?
   - If ≤5 files AND no new external dependencies: use LIGHT MODE.
     Skip the consensus agent, skip Gherkin, skip wave planning.
     Just list what you'll build, implement it directly, then run gates.
   - If >5 files OR new external dependencies: use FULL MODE (continue below).

   FEASIBILITY CHECK (both modes):
   - List every new external dependency this sprint requires (libraries, APIs, services)
   - For each: verify it exists in the registry, check version compatibility, confirm the API you need is available
   - Identify the single highest-risk technical task. Run a minimal spike (import, compile, call the API) to confirm it works
   - If any dependency is unverified or experimental, FLAG IT NOW with a fallback plan
   - If the spike fails, revise the scope before proceeding
   - Confirm a formatter AND linter are configured as gates in flowstate.config.md. If either is missing, set one up now before writing any code.

FULL MODE only (skip if light mode):

1. Acting as a consensus agent with all 5 skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor),
   produce acceptance criteria (Gherkin format) for this sprint's scope:
   [describe requirements here]
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

Gate 1: [type check / build command]
Gate 2: [lint command]
Gate 3: [test command]
Gate 4: [coverage command]
Gate 5 (smoke test): [one command that exercises the real system end-to-end, not mocks]
Gate 6 (optional): bash ~/Sites/Flowstate/tools/deps_check.sh    (verify new deps exist in registry)
Gate 7 (optional): bash ~/Sites/Flowstate/tools/sast_check.sh    (static security analysis)
Gate 8 (optional): bash ~/Sites/Flowstate/tools/deadcode_check.sh (detect unused exports/deps)

Save gate output to {FLOWSTATE}/metrics/sprint-N-gates.log.

If any gate fails:
- Classify each test failure as REGRESSION (test existed before this sprint) or FEATURE (new test). Compare failing test names against the baseline test list.
- Fix the issue, re-run that gate, max 3 cycles. If still failing after 3 cycles, stop and report.

When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."
```

## Phase 3: SHIP (retrospective + metrics)

Copy-paste this prompt after gates pass:

```
Run the Phase 3 retrospective for Sprint N.

1. Collect metrics using Flowstate MCP tools:
   a. Find the boundary timestamp:
      Call mcp__flowstate__sprint_boundary with project_path and sprint_marker (e.g. "M8", "sprint 2")
      This returns the last commit timestamp BEFORE the sprint's work.
   b. Find the session ID:
      Call mcp__flowstate__list_sessions with project_path
      Pick the session(s) that cover this sprint's time range.
   c. Collect metrics:
      Call mcp__flowstate__collect_metrics with project_path, session_ids, and the boundary timestamp as "after"
      This returns structured metrics: tokens, active time, model mix, delegation ratio, rework rate, etc.
   d. Save the raw metrics response to {FLOWSTATE}/metrics/sprint-N-metrics.json

2. Write import JSON at {FLOWSTATE}/metrics/sprint-N-import.json:
   - Start from the MCP metrics response (sprint-N-metrics.json) as the base
   - Add these fields:
     ```json
     {
       "project": "{project-slug}",
       "sprint": N,
       "label": "Sprint N: [phase description]",
       "phase": "[phase name from roadmap]",
       "metrics": {
         "...everything from sprint-N-metrics.json...",
         "tests_total": "<current test count>",
         "tests_added": "<tests added this sprint>",
         "coverage_pct": "<current coverage %>",
         "lint_errors": 0,
         "gates_first_pass": "<true|false>",
         "gates_first_pass_note": "<note if false, empty string if true>",
         "loc_added": "<LOC from git diff --stat>",
         "loc_added_approx": false,
         "task_type": "<feature|bugfix|refactor|infra|planning|hardening>",
         "rework_rate": "<from sprint-N-metrics.json, or null if not available>",
         "judge_score": "<[scope, test_quality, gate_integrity, convention, diff_hygiene] 1-5 each, from Stop hook output, or null>",
         "judge_blocked": "<true if LLM judge prevented stopping, false otherwise, or null>",
         "judge_block_reason": "<reason string if blocked, or null>",
         "coderabbit_issues": "<number of CodeRabbit issues on PR, or null if no PR>",
         "coderabbit_issues_valid": "<number human agreed were real, or null>",
         "mutation_score_pct": "<mutation score % if run, or null>",
         "delegation_ratio_pct": "<from sprint-N-metrics.json — subagent tokens / total tokens %, or null if no subagents>",
         "orchestrator_tokens": "<from sprint-N-metrics.json>",
         "subagent_tokens": "<from sprint-N-metrics.json>",
         "context_compressions": "<from sprint-N-metrics.json — number of context compression events>"
       },
       "hypotheses": [
         // Use IDs and names from hypotheses.json in the Flowstate repo.
         // Valid results: confirmed, partially_confirmed, inconclusive, falsified
         {"id": "H1", "name": "<from hypotheses.json>", "result": "...", "evidence": "..."},
         {"id": "H5", "name": "<from hypotheses.json>", "result": "...", "evidence": "..."},
         {"id": "H7", "name": "<from hypotheses.json>", "result": "...", "evidence": "..."}
       ]
     }
     ```
   - The schema matches sprints.json entries exactly — same field names, same types
   - Validate: call mcp__flowstate__import_sprint with the import JSON path and dry_run=true
   - Fix any errors before proceeding. Warnings (auto-corrections) are ok.

3. Write {FLOWSTATE}/retrospectives/sprint-N.md with:
   - What was built (deliverables, test count, files changed, LOC)
   - Metrics comparison vs previous sprint (see baseline)
   - What worked, with evidence
   - What failed, with evidence
   - H7 audit: check these 3 fixed instructions for compliance.
     These are mechanically verifiable — grep the new/modified source files for evidence.
     a. TESTS EXIST: every new source file has a corresponding test file with ≥1 test.
        PASS: test file exists and covers new code. FAIL: new source file with no tests.
     b. NO SECURITY ANTI-PATTERNS: no eval(), new Function(), or unescaped template
        literals in user-facing paths in new/modified code.
        PASS: grep returns empty. FAIL: grep finds matches in non-test files.
     c. COVERAGE DID NOT REGRESS: compare current coverage % to baseline.
        PASS: coverage ≥ baseline. FAIL: coverage dropped.
     For each, quote file:line evidence.

4. Hypothesis results table:
   | # | Hypothesis | Result | Evidence |
   Include at minimum: H1, H5, H7

5. Skill relevance audit:
   Review each skill file (.claude/skills/*.md). For each rule/instruction, classify as:
   - USED: influenced a decision or caught an issue this sprint (cite the decision or file)
   - UNUSED: not relevant to this sprint's work
   List the results as a table: | Skill | Rule | Status | Note |
   If a rule has been UNUSED for 4+ consecutive sprints (check prior retros), flag it as a STALE CANDIDATE for removal in step 6.

6. Change proposals as diffs (if any). Must have at least one `- Before` / `+ After` block or explain why no changes are needed with evidence.
   When proposing skill changes, prefer REMOVING or SIMPLIFYING instructions over adding new ones. Each added instruction reduces compliance with all others. Justify any addition by explaining why it's worth the cost.
   Include removal proposals for any STALE CANDIDATEs from step 5.

7. Do NOT apply skill changes — proposals stay in the retro for human review.
   Commit the sprint's code work:
   git add -A && git commit -m "sprint N: [description]"

8. Write the next sprint's baseline at {FLOWSTATE}/metrics/baseline-sprint-{N+1}.md:
   - Current git SHA
   - Test count, coverage %, lint error count
   - Gate commands and their current status (run each gate, record pass/fail)
   - H7 audit uses the 3 fixed instructions (tests exist, no security anti-patterns, coverage not regressed) — no rotation needed

9. Update docs/ROADMAP.md:
   - Mark this sprint's phase as done (strikethrough or checkmark)
   - Update the "Current State" section with new test count, LOC, milestone status

10. Write progress file at {FLOWSTATE}/progress.md:
   - What was completed this sprint (list of deliverables)
   - What failed or was deferred (and why)
   - What the next session should do first
   - Any blocked items or external dependencies awaiting resolution
   - Current gate status (all passing? which ones?)
   This file is operational state for the next agent session, not analysis.
   Overwrite any previous progress.md — it is always "current state."

11. COMPLETION CHECK — before declaring done, verify ALL of these exist:
   [ ] {FLOWSTATE}/metrics/sprint-N-metrics.json (raw MCP metrics response)
   [ ] {FLOWSTATE}/metrics/sprint-N-import.json (complete import-ready JSON, validated via MCP dry_run)
   [ ] {FLOWSTATE}/retrospectives/sprint-N.md contains:
       - Hypothesis results table with columns: # | Hypothesis | Result | Evidence
       - At least H1, H5, H7 rows
       - At least one change proposal with - Before / + After diff (or explicit "no changes needed" with evidence)
   [ ] {FLOWSTATE}/metrics/baseline-sprint-{N+1}.md with SHA, tests, coverage, gates
   [ ] {FLOWSTATE}/progress.md written (current state for next session)
   [ ] docs/ROADMAP.md updated (phase marked done, Current State refreshed)
   [ ] Sprint code committed

   Print this checklist with [x] or [MISSING] for each item.
   If anything is MISSING, fix it before proceeding.
```

---

## Post-Sprint

1. Review the retrospective at {FLOWSTATE}/retrospectives/sprint-N.md
2. Approve or reject each change proposal — apply approved changes to .claude/skills/ and commit
3. Validate import: call mcp__flowstate__import_sprint with dry_run=true, or: `python3 tools/import_sprint.py --from --dry-run {FLOWSTATE}/metrics/sprint-N-import.json`
4. Import metrics: call mcp__flowstate__import_sprint with dry_run=false, or: `python3 tools/import_sprint.py --from {FLOWSTATE}/metrics/sprint-N-import.json`
5. Run pipeline tests: `python3 tools/test_pipeline.py` (verifies import validation and table generation)
6. Optional: run mutation testing as a diagnostic: `bash ~/Sites/Flowstate/tools/mutation_check.sh` (expensive — not every sprint)

### Human Time

Tracked automatically by the MCP `collect_metrics` tool — it detects gaps >60s between entries in the session log and excludes them from active session time. No manual logging needed.
