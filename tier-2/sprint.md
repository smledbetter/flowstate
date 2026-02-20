# Sprint N: [Project Codename] -- [Milestone/Phase Name]

> Tier 2 sprint: skills + structure, no automated metrics collection.
> The retro produces a sanitized export you can bring back to the Flowstate repo.
> Set `{FLOWSTATE}` = `~/.flowstate/{project-slug}` (e.g., `~/.flowstate/my-project`).
> Skills live at `.claude/skills/` in the project repo (gitignored). Everything else is in `{FLOWSTATE}/`.
> **Start each sprint in a FRESH session.** One sprint = one session.
> Multi-sprint sessions degrade metric accuracy. If you must continue in an existing session, note it in the retro.

One-line description of what this sprint builds.

---

## Phase 1 + 2: THINK then EXECUTE (single prompt)

Copy-paste this prompt to start. The agent will plan AND execute without stopping.

```
You are running a Flowstate sprint.

Read these files:
- All skill files in .claude/skills/
- docs/ROADMAP.md (this sprint's phase)
- [{FLOWSTATE}/metrics/baseline-sprint-N.md] (current state: tests, coverage, lint)
- [{FLOWSTATE}/progress.md] (if exists -- operational state from last session)
- {FLOWSTATE}/flowstate.config.md (quality gates)
- [{FLOWSTATE}/retrospectives/sprint-{N-1}.md] (last retro, if exists)
- [project config / requirements -- adapt this list to your project]

PHASE 1 -- THINK:

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
   - Confirm a formatter AND linter are configured as gates. If either is missing, set one up now before writing any code.

FULL MODE only (skip if light mode):

1. Acting as a consensus agent with all 5 skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor),
   produce acceptance criteria (Gherkin format) for this sprint's scope:
   [describe requirements here]
   Every requirement must have at least one happy-path and one failure/edge-case scenario.

2. Produce an implementation plan with wave-based execution:
   - Group tasks into waves by file dependency
   - For each task: files read, files written, agent model (haiku for mechanical, sonnet for reasoning)

PHASE 2 -- EXECUTE:
Immediately after producing the plan, execute it. Do NOT wait for human approval between planning and execution.

- Spawn subagents per wave as specified in the implementation plan
- Each subagent gets: file path references (not content), task scope, relevant skill context
- Commit atomically after each wave
- Do NOT read full implementation files into your orchestrator context -- delegate reading to subagents
- After all waves complete, run quality gates:

[list your project's gate commands here, e.g.:]
Gate 1: [type check command]
Gate 2: [lint command]
Gate 3: [test command]
Gate 4: [coverage command]
Gate 5 (smoke test): [one command that exercises the real system end-to-end, not mocks]

If bash is available, save gate output to {FLOWSTATE}/metrics/sprint-N-gates.log.
If not, copy-paste the gate output into {FLOWSTATE}/retrospectives/sprint-N.md under a "## Gate Log" section so the evidence is preserved.

If any gate fails:
- Classify each test failure as REGRESSION (test existed before this sprint) or FEATURE (new test). Compare failing test names against the baseline test list.
- Fix the issue, re-run that gate, max 3 cycles.

When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."
```

## Phase 3: SHIP (retrospective + sanitized export)

Copy-paste this prompt after gates pass:

```
Run the retrospective for this sprint.

1. Write {FLOWSTATE}/retrospectives/sprint-N.md (full retrospective, stays local):
   - What was built (deliverables, test count, files changed)
   - What worked, with evidence
   - What failed, with evidence
   - Change proposals as diffs (if any). Must have at least one `- Before` / `+ After` block or explain why no changes are needed with evidence.
   - When proposing skill changes, prefer REMOVING or SIMPLIFYING instructions over adding new ones. Each added instruction reduces compliance with all others. Justify any addition by explaining why it's worth the cost.
   - Skill relevance audit: review each skill file (.claude/skills/*.md). For each rule/instruction, classify as USED (influenced a decision — cite it) or UNUSED (not relevant this sprint). If a rule has been UNUSED for 4+ consecutive sprints (check prior retros at {FLOWSTATE}/retrospectives/), flag it as a STALE CANDIDATE for removal. Include removal proposals for stale candidates in the change proposals above.

2. H7 audit: check these 3 fixed instructions for compliance.
   These are mechanically verifiable — grep the new/modified source files for evidence.
   a. TESTS EXIST: every new source file has a corresponding test file with ≥1 test.
      PASS: test file exists and covers new code. FAIL: new source file with no tests.
   b. NO SECURITY ANTI-PATTERNS: no eval(), new Function(), or unescaped template
      literals in user-facing paths in new/modified code.
      PASS: grep returns empty. FAIL: grep finds matches in non-test files.
   c. COVERAGE DID NOT REGRESS: compare current coverage % to baseline.
      PASS: coverage ≥ baseline. FAIL: coverage dropped.
   For each, quote file:line evidence.

3. Hypothesis results table:
   | # | Hypothesis | Result | Evidence |
   Include at minimum: H1, H5, H7

4. Now produce a SANITIZED EXPORT for process improvement. This will leave this environment, so it must contain NO proprietary code, architecture details, file paths, business logic, or project-specific content. Only include:
   - Sprint number, language/framework, generalized scope description
   - Metrics: estimate your active session time, count subagents spawned, count tests added, gate pass/fail
   - Task type: feature, bugfix, refactor, infra, planning, or hardening
   - Hypothesis results: H1 (3-phase worked?), H5 (gates caught issues?), H7 (X/5 compliance)
   - Skill change proposals GENERALIZED: strip project-specific details, describe the pattern not the implementation
   - Process observations: did the single prompt work? friction points? what would you change?

Format the sanitized export as a markdown document starting with "# Flowstate Sanitized Sprint Export".

5. Do NOT apply skill changes -- proposals stay in the retro for human review.
   Commit the sprint's code work:
   git add -A && git commit -m "sprint N: [generalized description]"

6. Write the next sprint's baseline at {FLOWSTATE}/metrics/baseline-sprint-{N+1}.md:
   - Current git SHA
   - Test count, coverage %, lint error count
   - Gate commands and their current status (run each gate, record pass/fail)
   - H7 audit uses the 3 fixed instructions (tests exist, no security anti-patterns, coverage not regressed) — no rotation needed

7. Update docs/ROADMAP.md:
   - Mark this sprint's phase as done (strikethrough or checkmark)
   - Update the "Current State" section with new test count, LOC, milestone status

8. Write progress file at {FLOWSTATE}/progress.md:
   - What was completed this sprint (list of deliverables)
   - What failed or was deferred (and why)
   - What the next session should do first
   - Any blocked items or external dependencies awaiting resolution
   - Current gate status (all passing? which ones?)
   This file is operational state for the next agent session, not analysis.
   Overwrite any previous progress.md — it is always "current state."

9. COMPLETION CHECK — before declaring done, verify ALL of these exist:
   [ ] {FLOWSTATE}/retrospectives/sprint-N.md contains:
       - Hypothesis results table with columns: # | Hypothesis | Result | Evidence
       - At least H1, H5, H7 rows
       - At least one change proposal with - Before / + After diff (or explicit "no changes needed" with evidence)
   [ ] Sanitized export produced (starting with "# Flowstate Sanitized Sprint Export")
   [ ] {FLOWSTATE}/metrics/baseline-sprint-{N+1}.md with SHA, tests, coverage, gates
   [ ] {FLOWSTATE}/progress.md written (current state for next session)
   [ ] docs/ROADMAP.md updated (phase marked done, Current State refreshed)
   [ ] Sprint code committed

   Print this checklist with [x] or [MISSING] for each item.
   If anything is MISSING, fix it before proceeding.
```

---

## After the Sprint

1. Review the retrospective at {FLOWSTATE}/retrospectives/sprint-N.md
2. Approve or reject each change proposal -- apply approved changes to .claude/skills/ and commit
3. Review the sanitized export -- redact anything you are not comfortable sharing
4. Copy the sanitized export to your Flowstate repo: `imports/[codename]-sprint-N.md`
