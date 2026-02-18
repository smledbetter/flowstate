# Sprint N: [Project Codename] -- [Milestone/Phase Name]

> Tier 2 sprint: skills + structure, no automated metrics collection.
> The retro produces a sanitized export you can bring back to the Flowstate repo.

One-line description of what this sprint builds.

---

## Phase 1 + 2: THINK then EXECUTE (single prompt)

Copy-paste this prompt to start. The agent will plan AND execute without stopping.

```
You are running a Flowstate sprint.

Read these files:
- All skill files in .claude/skills/
- [project config / requirements -- adapt this list to your project]

PHASE 1 -- THINK:
Acting as a consensus agent with all 5 skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor):

1. Produce acceptance criteria (Gherkin format) for this sprint's scope:
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

If any gate fails: fix the issue, re-run that gate, max 3 cycles.

When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."
```

## Phase 3: SHIP (retrospective + sanitized export)

Copy-paste this prompt after gates pass:

```
Run the retrospective for this sprint.

1. Write a full retrospective (keep this local, do not share outside this environment):
   - What was built (deliverables, test count, files changed)
   - What worked, with evidence
   - What failed, with evidence
   - Change proposals as diffs (if any)

2. H7 audit: check these 5 skill instructions for compliance:
   [list your 5 pre-selected instructions here]

3. Now produce a SANITIZED EXPORT for process improvement. This will leave this environment, so it must contain NO proprietary code, architecture details, file paths, business logic, or project-specific content. Only include:
   - Sprint number, language/framework, generalized scope description
   - Metrics: estimate your active session time, count subagents spawned, count tests added, gate pass/fail
   - Hypothesis results: H1 (3-phase worked?), H5 (gates caught issues?), H7 (X/5 compliance)
   - Skill change proposals GENERALIZED: strip project-specific details, describe the pattern not the implementation
   - Process observations: did the single prompt work? friction points? what would you change?

Format the sanitized export as a markdown document starting with "# Flowstate Sanitized Sprint Export".

4. Apply any skill changes and commit:
   git add -A && git commit -m "sprint N: [generalized description]"
```

---

## After the Sprint

1. Review the full retrospective (stays on this machine)
2. Review the sanitized export -- redact anything you are not comfortable sharing
3. Copy the sanitized export to your Flowstate repo: `imports/[codename]-sprint-N.md`
