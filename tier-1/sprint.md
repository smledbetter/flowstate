# Sprint N: [Project] — [Milestone/Phase Name]

> Tier 1 sprint: full Claude Code with bash, automated metrics.

One-line description of what this sprint builds.

---

## Phase 1 + 2: THINK then EXECUTE (single prompt)

Copy-paste this prompt to start. The agent will plan AND execute without stopping.

```
You are running a Flowstate sprint for [PROJECT] [MILESTONE/PHASE].

Read these files:
- PRD.md (or README)
- [roadmap / requirements files]
- [metrics/baseline-sprint-N.md] (current state: tests, coverage, lint)
- flowstate.config.md (quality gates)
- [retrospectives/sprint-{N-1}.md] (last retro, if exists)
- All skill files in .claude/skills/

PHASE 1 — THINK:
Acting as a consensus agent with all 5 skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor):

1. Produce acceptance criteria (Gherkin format) for this sprint's scope:
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

Save gate output to metrics/sprint-N-gates.log.

If any gate fails: fix the issue, re-run that gate, max 3 cycles. If still failing after 3 cycles, stop and report.

When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."
```

## Phase 3: SHIP (retrospective + metrics)

Copy-paste this prompt after gates pass:

```
Run the Phase 3 retrospective for Sprint N.

1. Collect metrics by running: bash metrics/collect.sh <SESSION_ID>
   The session ID is from your current session.
   Save output to metrics/sprint-N-report.txt.

2. Write retrospectives/sprint-N.md with:
   - What was built (deliverables, test count, files changed, LOC)
   - Metrics comparison vs previous sprint (see baseline)
   - What worked, with evidence
   - What failed, with evidence
   - H7 audit: check these 5 skill instructions for compliance:
     [list 5 pre-selected instructions from baseline]

3. Hypothesis results table:
   | # | Hypothesis | Result | Evidence |
   Include at minimum: H1, H5, H7

4. Change proposals as diffs (if any). Must have at least one `- Before` / `+ After` block or explain why no changes are needed with evidence.

5. Apply any approved skill changes and commit everything:
   git add -A && git commit -m "sprint N: [description]"
```

---

## Post-Sprint

1. Review the retrospective and approve/reject each change proposal
2. Copy metrics/sprint-N-report.txt to Flowstate repo for RESULTS.md update
3. Write the next sprint's baseline: metrics/baseline-sprint-{N+1}.md

### Human Time

Tracked automatically by `collect.sh` — it detects gaps >60s between assistant and human entries in the session log and reports them as "Human idle" time. No manual logging needed.
