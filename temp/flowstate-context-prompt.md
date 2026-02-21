# Flowstate: System Context

You are working on a project that uses Flowstate, a sprint-based development workflow for Claude Code. This document explains how the system works so you can operate effectively within it.

## What Flowstate Is

Flowstate is a set of markdown files and Claude Code skills that structure AI-agent development into repeatable sprints. It prioritizes -- in this order -- code quality, active session time (wall clock), and token efficiency.

It is not a framework you install. It is a process you follow: markdown templates, skill files loaded into `.claude/skills/`, and a feedback loop that makes each sprint better than the last.

## The 3-Phase Sprint

Every sprint has three phases:

**Phase 1+2: THINK then EXECUTE** (single prompt, no human break)
- A consensus agent loads 5 skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor) simultaneously -- not 5 separate agents
- The consensus agent writes Gherkin acceptance criteria and a wave-based implementation plan
- Execution begins immediately: subagents are spawned per wave, grouped by file dependency
- Each subagent gets file path references (not file content), task scope, and relevant skill context
- The orchestrator does not read implementation files -- it delegates everything to subagents
- Quality gates run after all waves complete

**Phase 3: SHIP** (human checkpoint)
- Metrics collection (automated or agent-estimated depending on tier)
- Retrospective with hypothesis results and change proposals as diffs
- Next sprint baseline written
- Roadmap updated

The human reviews the retro after the session ends. Skill changes are proposed but not applied until the human approves.

## Why This Structure Works

Evidence from 7 sprints across 2 projects (TypeScript CLI + Rust P2P):

**Consensus agent > multiple agents**: Loading 5 perspectives into one agent produces coherent output. Spawning 5 separate planning agents creates contradictions and wastes tokens.

**Wave-based parallelism**: Group tasks by file dependency. Tasks sharing no files run in parallel. Tasks sharing files run sequentially. This prevents merge conflicts and keeps subagent scope small.

**Thin orchestrator**: The orchestrator plans and dispatches but never reads implementation files. This keeps its context budget under 40%, leaving room for error handling and gate cycles.

**Subagent scope limit**: Each subagent modifies no more than 3 files. Larger tasks get split across multiple subagents in the same or adjacent waves. Agents lose coherence on cross-cutting changes.

**Model mix**: Use the cheapest model that can do the job. Haiku for single-file mechanical changes following existing patterns. Sonnet for multi-file wiring that requires reading context. Opus for orchestration.

## Quality Gates

Gates are non-negotiable automated checks. A sprint cannot ship unless all enabled gates pass. Common gates:

1. Build / type check
2. Lint (zero warnings)
3. Tests (all pass)
4. Coverage (above floor)
5. Smoke test (one real end-to-end exercise, not mocks)

When a gate fails:
- Classify the failure as REGRESSION (existing test now fails) or FEATURE (new test doesn't pass yet). This distinction drives the fix: regressions mean the agent damaged existing code, feature failures mean implementation is incomplete.
- Fix, re-run, max 3 cycles. If still failing after 3, stop and report.

A formatter and linter must be configured as gates before Sprint 0. Style enforcement without tooling is just a suggestion.

## Skills

Five markdown files in `.claude/skills/`, each defining a perspective:

- **Product Manager**: Gherkin acceptance criteria, scope boundaries, user stories
- **UX Designer**: Interface patterns, error messages, help text, accessibility
- **Architect**: Module boundaries, agent strategy, wave planning, interface contracts
- **Production Engineer**: TDD workflow, gate enforcement, dependency management, test coverage verification
- **Security Auditor**: Input validation, threat model, dependency audit

Skills are advisory -- agents can ignore them. Gates are enforcement -- automated pass/fail. Important skill instructions should have a corresponding gate.

**Security deployment model**: During planning (Phase 1), the security auditor perspective is loaded into the consensus agent. During implementation (Phase 2), security is NOT loaded into implementing subagents. Security review runs as a separate pass after implementation. Research shows agents given security + implementation instructions simultaneously produce worse code on both dimensions.

## The Feedback Loop

Each sprint ends with a retrospective that:
1. Compares metrics to the previous sprint
2. Audits 5 specific skill instructions for compliance (H7)
3. Proposes changes as `- Before` / `+ After` diffs

**Simplification bias**: When proposing changes, prefer removing or simplifying instructions over adding new ones. Each added instruction reduces compliance with all others. Research shows compliance drops ~6 percentage points per additional instruction, falling below 50% at 3+ simultaneous instructions.

The human approves or rejects each change. Rejected changes include a reason that feeds into the next retro.

**Per-project stability**: When a project has 3 consecutive sprints with 0 or minimal skill changes, the skill set is considered stable. Stop proposing changes unless new evidence justifies them.

## Hypotheses You Should Know About

Flowstate tracks 12 hypotheses across sprints. The ones most relevant to your work:

- **H1**: The 3-phase structure works for this project type (confirmed across 7 sprints, 2 languages)
- **H5**: Gates catch real issues, not just ceremony (confirmed -- clippy caught 3 bugs on Rust, lint caught unused import on TS)
- **H7**: Skills are actually followed by agents (improved from 3/5 to 5/5 over 7 sprints)

## Key Conventions

- One sprint per session. Fresh Claude Code session for each sprint.
- Active session time, not "wall time" -- sum of active session durations excluding human-away gaps.
- Commit atomically after each wave. Single commit acceptable for sequential waves sharing no files.
- Do NOT read full implementation files into orchestrator context. Delegate to subagents.
- Feasibility check before planning: verify external dependencies exist, spike the highest-risk task, confirm formatter + linter gates.
- Test coverage verification: every new source file must have a corresponding test file modified in the same sprint.
