# Flowstate: Product Requirements Document

> A sprint-based, multi-agent development system for Claude Code that prioritizes code quality, wall time, and token efficiency — in that order. Built to evolve, not to be right on the first try.

## 1. Problem Statement

Building software with AI agents today requires choosing between:

- **Ad hoc prompting**: fast to start, no consistency, no learning between sessions
- **Rigid frameworks** (e.g., GSD): structured phases and context management, but opinionated about directory layout, phase numbering, and workflow. You install someone else's system rather than owning one that evolves with you
- **Raw Claude Code features** (subagents, agent teams): powerful primitives, but no sprint structure, no metrics, no feedback loops, no quality gates

None of these start from a product specification and produce a working, tested, continuously-improving development workflow.

### What's been proven (on one project)

Building Weaveto.do (8 milestones, 12K lines of TypeScript, 491 tests, $100 flat subscription) demonstrated that:

1. A **3-phase sprint** (Think → Execute+Gate → Ship) with retrospective feedback loops produces reliable output
2. **Thin orchestrator + wave-based parallel execution** keeps context budgets healthy while maximizing throughput
3. **Skills as markdown perspectives** (PM, UX, Architect, Prod Engineer, Security Auditor) loaded into a single consensus agent beat spawning 5 separate agents
4. **Verified token metrics** parsed from session logs create accountability — not vibes, but numbers
5. **Model mix optimization** (~27% opus, ~56% sonnet, ~17% haiku) cuts cost 3-5x vs. opus-only
6. **Retrospective → rule update loops** make each sprint measurably better than the last

### What's unproven

Every pattern above was discovered on a single project (SvelteKit frontend with crypto). The following are hypotheses, not facts:

- That the 3-phase sprint structure works for CLI tools, APIs, data pipelines, and other project shapes
- That the Weaveto.do skill set (PM, UX, Architect, Prod Engineer, Security Auditor) is the right set for all projects
- That the model mix sweet spot transfers across project types
- That the 30-40% context budget is the right threshold for all orchestration patterns
- That wave-based parallelism helps when the project has fewer independent subsystems
- That skill evolution via retrospective produces net-positive changes over 5+ sprints rather than accumulating scar tissue

**Sprint 0 exists to falsify these hypotheses on a second project (Uluka), not to confirm them.**

### What's missing

- **No portable system**: starting a new project means manual copy-paste and adaptation
- **No PRD-driven bootstrapping**: no way to go from a product spec to a running sprint workflow
- **No cross-sprint metrics**: token accounting exists but isn't standardized or comparable
- **No way to distinguish "skills helped" from "task was easy"**: no causal link between process changes and outcomes

## 2. Product Vision

Flowstate is a **set of markdown files and Claude Code skills** for sprint-based, multi-agent software development. It is:

- **PRD-first**: every project starts with a markdown specification that the architect agent works from
- **Sprint-structured**: work happens in sprints with quality gates and verified metrics
- **Empirical**: patterns are hypotheses tested across projects, not axioms declared upfront
- **Agent-flexible**: subagents, agent teams, or hybrid — chosen per task, not per project
- **Human-steered**: the human reviews plans, approves gates, and decides which retrospective changes to adopt

### Priorities (in order)

1. **Code quality** — correct, tested, reviewed code ships. Quality gates are the hard constraint
2. **Wall time** — parallelism and smart delegation minimize calendar time
3. **Token efficiency** — model mix, context management, and caching minimize cost per unit of accepted work

## 3. Users

### Primary: Solo builder / small team lead

- Uses Claude Code with Max subscription or API
- Building a real product (not a toy)
- Comfortable with markdown, git, and terminal workflows
- Willing to review agent output but wants to minimize review burden

### Secondary: The architect agent (Claude)

- Reads the PRD and project state to plan sprints
- Spawns and coordinates worker agents
- Runs quality gates (hard checks, not suggestions)
- Proposes process improvements via retrospective (human decides)

## 4. Core Concepts

### 4.1 The Sprint

A sprint is the atomic unit of work. Every sprint follows three phases:

```
Phase 1: THINK          Phase 2: EXECUTE + GATE       Phase 3: SHIP
─────────────────        ───────────────────────        ─────────────
                         Wave 1 (parallel)
PRD/milestone ──►        ┌─────┐ ┌─────┐               git push
Consensus agent          │agent│ │agent│               doc sync
(PM + UX + Arch)         └──┬──┘ └──┬──┘               retrospective
produces:                   │       │                   metrics
 • acceptance.md         Wave 2 (parallel)              
 • implementation.md     ┌─────┐ ┌─────┐ ┌─────┐       
   (waves + tasks)       │agent│ │agent│ │agent│
                         └──┬──┘ └──┬──┘ └──┬──┘
                            │       │       │
                         Ship-readiness gate
                         (tests, types, lint, audit)
                         PASS ──► Phase 3
                         FAIL ──► fix + re-gate
```

### 4.2 Skills vs Gates

This distinction is load-bearing.

**Skills** are advisory. They guide agent behavior through markdown instructions — perspectives, quality bars, patterns to follow. An agent *can* ignore a skill. Skills are useful but not trustworthy.

**Gates** are enforcement. They are automated checks that run after execution and block shipping if they fail. An agent cannot ignore a gate. Gates are the actual quality mechanism.

| Layer | Examples | Enforced by |
|-------|----------|-------------|
| **Gate** (hard) | Tests pass, types check, lint clean, coverage threshold, no regressions | Automated commands that return pass/fail |
| **Skill** (soft) | "No plaintext logging", "use pure functions", "write Gherkin acceptance criteria" | Agent following instructions (unverifiable without a corresponding gate) |

**The rule**: any skill instruction that matters enough to block shipping must have a corresponding gate. If you can't automate the check, the skill is aspirational, not operational. The security auditor skill's "no plaintext data" instruction is decorative unless there's a grep-based gate that enforces it.

Sprint 0 will identify which of the Weaveto.do skill instructions are actually gate-enforceable vs purely advisory.

**Security review as separate agent**: during planning (Phase 1), the security auditor perspective should be loaded into the consensus agent to shape acceptance criteria. During implementation (Phase 2), security checks should be run as a dedicated review agent or gate, not as instructions loaded into implementing subagents. Research (SusVibes benchmark) shows that agents given security instructions alongside implementation tasks produce 7% worse functional correctness with minimal security improvement. Planning and auditing are separate from implementing — the same agent should not implement and audit simultaneously.

### 4.3 The Architect

The architect is the lead agent. It:

- Reads the PRD, project state, and current skills
- Plans each sprint (Phase 1: Think)
- Decides the agent strategy for execution
- Manages the orchestration budget (target: 30-40% context — to be validated)
- Runs the retrospective and proposes process improvements
- **Never writes feature code directly** (delegate mode)

### 4.4 Agent Strategy

The architect selects the coordination model per task. Rows marked "unvalidated" are hypotheses — Sprint 0 uses subagents only.

| Signal | Strategy | Validation status |
|--------|----------|-------------------|
| 1 file, simple fix | Solo haiku subagent | Proven (Weaveto.do) |
| 1 subsystem, moderate complexity | Solo sonnet subagent | Proven (Weaveto.do) |
| 2-3 independent subsystems | Parallel subagents (wave-based) | Proven (Weaveto.do), testing on Uluka in Sprint 0 |
| 3+ subsystems needing coordination | Agent team with shared task list | Unvalidated — Sprint 2 |
| Cross-cutting + discussion needed | Agent team with peer messaging | Unvalidated — Sprint 2 |
| Security-critical work | Opus-led with plan approval required | Proven (Weaveto.do) |

**Important caveats**:

- "Independent subsystems" is a judgment call. Two modules that look independent often share a config file or type definition. The architect must check for shared files before declaring independence.
- Agent Teams are experimental. The fallback is not "run the same plan with subagents" — it's "replan for subagents," because team-shaped plans assume coordination that subagents can't provide.
- Hybrid mode (teammates spawning subagents) is an untested hypothesis. Sprint 2 will validate or discard it.

### 4.5 Context Management

Context rot is the primary enemy of code quality. Rules:

| Rule | Mechanism |
|------|-----------|
| Orchestrator stays thin | Target 30-40% context; delegates, doesn't accumulate |
| Fresh context per worker | Each subagent/teammate gets a clean 200K window |
| File references, not content | Pass `@file-path`, let workers read what they need |
| Collect summaries, not raw output | Workers report results; orchestrator doesn't re-read files |
| Commit per wave | Atomic commits create durable checkpoints |
| Session breaks at natural boundaries | If context exceeds 50%, commit and start fresh |

### 4.6 Quality Gates

Gates are non-negotiable. A sprint cannot ship unless all enabled gates pass:

| Gate | Default | Configurable |
|------|---------|-------------|
| Tests pass | Required | Command |
| Type check passes | Required | Command |
| Coverage threshold | 75% lines | Percentage |
| Lint clean | Required | Command |
| No regressions | Required | Enabled/disabled |
| Security audit (OWASP review) | Optional | Severity threshold |
| Retro format check | Required | Enabled/disabled |
| Smoke test | Optional | Command (one real end-to-end exercise) |
| Custom gates | None | Command + pass/fail criteria |

**Smoke test gate**: one command that exercises the real system end-to-end, not mocks. Example: for a CLI tool, `uluka verify ./fixtures/sample-project` and check output. For a P2P app, two processes connect and exchange a message over localhost. This gate exists because static gates (tests, lint, types) can all pass while the product doesn't actually work — mocks hide integration failures. Evidence: Dappled Shade Sprint 1 shipped 75 passing tests with all gates green, but the real Tor integration was never tested (all integration tests used MockTorService). See RESULTS.md and FeatBench research on F2P testing.

**Custom gates** are how skill instructions become enforceable. Example: the security auditor skill says "no plaintext logging." The corresponding custom gate is: `grep -r "console.log\|console.error" src/ --include="*.ts" | grep -v "// allowed"` must return empty.

**Retro format gate**: the retrospective must contain at least one `- Before` / `+ After` diff block, or it is rejected. This prevents agents from producing paragraph-style retros instead of actionable diffs.

**Phase 3 completion checklist**: Phase 3 ends with the agent printing a completion checklist — each required artifact marked `[x]` or `[MISSING]`. Required artifacts: metrics reports (text + JSON), retrospective (with hypothesis table and diff proposals), next baseline, roadmap update, committed code. Any `[MISSING]` item must be fixed before the sprint is considered shipped.

Failed gates produce specific findings with file paths and line numbers, not just pass/fail. When tests fail, classify each failure as **regression** (test existed before this sprint and now fails) or **feature** (new test that doesn't pass yet) by comparing against the pre-sprint test list in the baseline. This distinction matters: regressions mean the agent damaged existing code (fix: scope constraints), while feature failures mean implementation is incomplete (fix: finish the task). Evidence: FeatBench found regressions are the dominant failure mode in agent-generated code.

### 4.7 Metrics

Metrics are organized into **primary** (drive decisions) and **diagnostic** (investigated when a primary metric goes wrong).

**Primary metrics** — look at these every sprint:

| Metric | What it measures | Decision it drives |
|--------|-----------------|-------------------|
| First-pass gate success rate | Did code pass gates before fixes? | Skill quality — are agents writing correct code? |
| Active session time | Sum of active session durations from sprint start to ship (see note) | Parallelism effectiveness |
| Total new-work tokens | Non-cache tokens consumed | Raw cost of the sprint |

**Active session time note**: A sprint may span multiple agent sessions (due to the 50% context break rule). Active session time is the sum of active session durations, not the delta between first session start and last session end. Breaks between sessions (human away from keyboard, overnight gaps) are excluded. Session durations are parsed from Claude Code's JSONL session logs — each log entry has a `timestamp` field, so active session time is `last_event_timestamp - first_event_timestamp`. No manual recording needed.

**Session log structure**: Parent session logs live at `~/.claude/projects/{project-slug}/{session-id}.jsonl`. Subagent sessions are stored in `~/.claude/projects/{project-slug}/{session-id}/subagents/agent-{id}.jsonl`. Token usage and model mix must include subagent logs — otherwise the report only reflects the orchestrator's API calls and misses all worker token usage. The `collect.sh` script (at `~/.flowstate/{project-slug}/metrics/collect.sh`) automatically discovers and includes subagent logs for each parent session. It must be run from the project directory so it can derive the correct session log path.

**Diagnostic metrics** — investigate when primaries go wrong:

| Metric | When to check |
|--------|--------------|
| Model mix (opus/sonnet/haiku %) | When token cost spikes unexpectedly |
| Cache hit rate | When total tokens spike — are we thrashing context? |
| Meta overhead ratio (planning + retro tokens vs feature tokens) | When new-work tokens seem high relative to output |
| Tokens per accepted LOC | When comparing similar-complexity sprints (not across different project types) |
| Agent spawn count | When active session time is worse than expected |
| Test count (new + total) | When gate failures spike |
| Coverage delta | When coverage threshold is barely met |
| Defects found by gate (by type) | When first-pass success rate drops — what's failing? |
| Delegation ratio (subagent tokens / total tokens %) | When orchestrator context grows too large or quality degrades late in sprint |
| Context compressions (count of `compact_boundary` events) | When quality degrades late in sprint — 0 = context fit, >0 = window filled up |

**What we explicitly don't track** (yet): LOC as a productivity metric, skill change "impact" (no causal mechanism).

**Context efficiency**: Delegation ratio and context compressions replace the earlier "context utilization at session end" concept. Delegation ratio measures how well the orchestrator delegates (higher = more work in fresh subagent windows). Context compressions count how many times Claude Code's auto-compaction fired during the session — detected via `compact_boundary` system events in the JSONL logs. Both are computed automatically by `collect.sh`.

Metrics are stored in `~/.flowstate/{project-slug}/metrics/` (reports, baselines, gate logs). Cross-project metrics live in the Flowstate repo's `sprints.json`.

### 4.8 The Retrospective

Every sprint ends with a structured retrospective. The retro produces two outputs:

**1. The report** (informational):
- What was built: deliverables, test counts, files changed
- Primary metrics vs previous sprint
- What worked: specific patterns with evidence
- What failed: specific patterns with evidence

**2. The change proposal** (actionable, requires human approval):

Each proposed change is a **diff** — not a paragraph explaining what should change, but the literal before/after edit:

```
## Proposed Change: production-engineer.md
Reason: Gate caught 3 type errors that tests missed. Add explicit type-check reminder.
Evidence: Sprint 2 gate log, lines 45-67

- Before (line 34):
  ## Quality Gates
  All gates must pass before a milestone ships:
  - Unit test coverage >= 75% on all new code

+ After (line 34):
  ## Quality Gates
  All gates must pass before a milestone ships:
  - `npm run check` FIRST — Vitest doesn't catch TypeScript errors
  - Unit test coverage >= 75% on all new code
```

The retro format gate (section 4.6) enforces this: a retrospective without at least one `- Before` / `+ After` block is rejected automatically.

The agent proposes changes during Phase 3 but does **not** apply them. The human reviews the retrospective **after the sprint session ends** — not mid-session. This allows the agent to complete all Phase 3 work (metrics, retro, baseline, roadmap update) in one uninterrupted pass.

The human can: approve, modify, or reject each change individually. Rejected changes include a reason that feeds into the next retro ("Human rejected X because Y — do not re-propose without new evidence").

**Simplification bias**: when proposing skill changes, prefer removing or simplifying instructions over adding new ones. Each instruction added reduces agent compliance with all other instructions — research (Vibe Checker, VERICODE) shows compliance drops ~6 percentage points per additional instruction, falling below 50% at 3+ simultaneous instructions. The retro should justify any new instruction by explaining why it's worth the compliance cost to existing instructions.

**Skill pruning**: every 3 sprints, the retro flags skill instructions for review using two categories:

| Category | Meaning | Action |
|----------|---------|--------|
| **Never triggered, never relevant** | The instruction addresses a situation that never arose in any sprint (e.g., "handle file uploads" in a CLI tool) | Candidate for removal — the skill is bloat for this project |
| **Never triggered, always relevant** | The instruction addresses a situation that arises every sprint but was never cited in a gate failure or "what worked" entry (e.g., "no plaintext logging" and no one logged plaintext) | Keep — the guardrail may be working silently. Investigate before removing |
| **Triggered but unhelpful** | The instruction was cited but the agent's compliance didn't improve outcomes | Candidate for rewriting or removal |

The human decides. The default for ambiguous cases is **keep** — it's cheaper to carry a few extra lines than to remove a guardrail that was working.

## 5. System Architecture

### 5.1 Project Structure

```
project/
├── PRD.md                          # Product requirements (user-written)
├── CLAUDE.md                       # Claude Code config (generated + evolved)
├── .claude/
│   └── skills/                     # Skill files (gitignored)
│       ├── product-manager.md
│       ├── ux-designer.md
│       ├── architect.md
│       ├── production-engineer.md
│       ├── security-auditor.md
│       └── {project-specific}.md
├── docs/
│   ├── ROADMAP.md                  # Milestones broken into sprint-sized phases
│   ├── milestones/
│   │   └── M{N}-{name}/
│   │       ├── acceptance.md       # Gherkin acceptance criteria
│   │       └── implementation.md   # Wave-based execution plan
│   └── research/                   # Cached knowledge artifacts
└── src/                            # Project source code

~/.flowstate/{project-slug}/
├── flowstate.config.md             # Flowstate configuration
├── SPRINT-{N}.md                   # Sprint prompt (filled-in copy)
├── metrics/
│   ├── collect.sh                  # Metrics collector (auto-detects project from cwd)
│   ├── baseline-sprint-{N}.md      # Pre-sprint baselines
│   ├── sprint-{N}-gates.log        # Gate pass/fail output
│   └── sprint-{N}-report.txt       # Collected metrics
└── retrospectives/
    └── sprint-{N}.md               # Retro report + change proposals
```

Flowstate workflow files (config, sprints, metrics, retrospectives) live outside the project repo at `~/.flowstate/{project-slug}/` so they don't clutter open-source repos. Skills must stay at `.claude/skills/` (Claude Code auto-loads from this path) but are gitignored.

### 5.2 Configuration: `flowstate.config.md`

```markdown
# Flowstate Configuration

## Quality Gates
- test_command: npm run test
- type_check: npm run check
- lint: npm run lint
- coverage_threshold: 75
- custom_gates: []

## Agent Strategy Defaults
- orchestrator_model: opus
- worker_model: sonnet
- mechanical_model: haiku
- orchestrator_context_target: 40%

## Sprint Settings
- commit_strategy: per-wave
- session_break_threshold: 50%
```

### 5.3 Bootstrap Flow

Bootstrap happens in two phases to avoid context rot:

**Phase A: Configuration** (one agent session)
1. Human writes PRD.md
2. Architect reads PRD.md
3. Generates `flowstate.config.md` and `CLAUDE.md` (project configuration only — not skills)
4. `flowstate.config.md` must include a formatter and a linter as gates — every popular language has both (e.g., Prettier+ESLint for TS, cargo fmt+clippy for Rust, Black+Ruff for Python, gofmt+golangci-lint for Go). If the project has no formatter or linter configured, the bootstrap must set one up. Style enforcement without tooling is just a suggestion.
5. Human reviews and approves

Skills are **copied and adapted** from Flowstate's generic set, not generated from scratch. The architect may suggest which skills to include or exclude based on the PRD (e.g., "skip UX designer for a CLI tool"), but skill generation from PRD content is deferred until there's evidence about what good generated skills look like.

**Phase B: Roadmap** (fresh agent session)
1. Architect reads PRD.md + approved config from Phase A + copied skill files
2. Produces `docs/ROADMAP.md`: breaks PRD milestones into sprint-sized phases
   - Each phase = one sprint, with scope bullets and gate criteria
   - Dependency graph between phases (what blocks what)
   - Sprint schedule table mapping phases to sprint numbers
3. Human reviews, adjusts phase boundaries, approves
4. First sprint begins (referencing the roadmap for scope)

The roadmap bridges the gap between PRD milestones (what to build) and sprint prompts (what to build *this sprint*). Without it, every sprint re-derives scope from the PRD, which wastes context and produces inconsistent phase boundaries.

Splitting bootstrap prevents the architect from planning milestones in a context window already full of generated config.

### 5.4 Sprint Execution Flow

```
Human says: "sprint" or "start sprint for M{N}"

PHASE 1+2: THINK then EXECUTE (single prompt, no human break)
├── Architect loads: PRD, docs/ROADMAP.md (current phase), last retro
├── Architect loads skills: PM + UX + Architect (as one consensus agent)
├── Consensus agent reads codebase + docs (once)
├── Outputs: acceptance.md (Gherkin), implementation.md (waves)
├── Implementation.md includes:
│   ├── Wave groupings with explicit file-dependency analysis
│   ├── Agent strategy selection with rationale
│   └── Fallback plan if primary strategy fails
├── Immediately proceeds to execution (no human approval between plan and execute)
├── Architect analyzes implementation.md
├── Architect selects agent strategy
├── For each wave:
│   ├── Spawn workers with: file refs, task scope, skill context
│   ├── Workers execute (2-3 tasks max per worker)
│   ├── Workers commit atomically per wave
│   └── Architect collects summaries (not raw output)
├── If strategy fails (team instability, conflicts):
│   ├── Commit completed work
│   ├── Replan remaining work for fallback strategy
│   └── Continue with fallback
├── All waves complete
├── Ship-readiness gate:
│   ├── Run all quality gate commands
│   ├── Run custom gates
│   ├── Produce pass/fail report with specific findings
│   ├── If FAIL: fix agent addresses findings, re-gate (max 3 cycles)
│   └── If FAIL after 3 cycles: escalate to human
└── PASS → Phase 3

PHASE 3: SHIP (agent runs autonomously, human reviews after)
├── Collect metrics: collect.sh (text + JSON reports)
├── Doc sync: update docs/ROADMAP.md (mark phase done, update current state)
├── Retrospective:
│   ├── Collect primary + diagnostic metrics
│   ├── Compare to previous sprint
│   ├── Write report (what worked, what failed, with evidence)
│   ├── Propose changes as diffs (not paragraphs)
│   ├── Retro format gate: must contain ≥1 diff block or rejected
│   └── Write: {FLOWSTATE}/retrospectives/sprint-{N}.md
├── Commit sprint code work (skill changes NOT applied yet)
├── Write next sprint baseline: {FLOWSTATE}/metrics/baseline-sprint-{N+1}.md
├── Human reviews retro (post-sprint, not mid-session):
│   ├── Approve/modify/reject each proposed change
│   ├── Rejected changes include reason
│   └── Approved changes applied to .claude/skills/ and committed
├── Import to Flowstate repo: python3 tools/import_sprint.py --from <import-json>
└── Sprint complete
```

**Session hygiene**: each sprint should run in a fresh Claude Code session. Multi-sprint sessions are allowed but must be noted in the retro. The `--after` flag on collect.sh isolates token metrics when sessions span multiple sprints, but active time accuracy degrades with context compaction.

## 6. Deliverables

Flowstate ships as **markdown files + Claude Code skills** copied into a project:

### 6.1 Repo Structure

```
Flowstate/
├── PRD.md                          # This document
├── RESULTS.md                      # Experiment data and hypothesis results
├── skills/                         # Generic skill files (canonical set)
│   ├── product-manager.md          # Gherkin acceptance criteria, user value
│   ├── ux-designer.md              # User flows, interface standards
│   ├── architect.md                # Module design, agent strategy, orchestration
│   ├── production-engineer.md      # TDD, quality gates, test conventions
│   └── security-auditor.md         # Threat review, input validation, audit
├── tier-1/                         # Full: Claude Code + bash + metrics
│   ├── sprint.md                   # Sprint prompt template (Phase 1+2 + Phase 3)
│   ├── flowstate.config.md         # Config template with placeholder gates
│   └── collect.sh                  # Metrics collector (auto-detects project)
├── tier-2/                         # Skills + structure, no automated metrics
│   ├── sprint.md                   # Sprint prompt (produces sanitized export)
│   └── sanitized-export.md         # Redacted export template
├── tier-3/                         # Prompt-only, any LLM
│   └── sprint.md                   # Self-contained 3-phase prompt
└── imports/                        # Sanitized exports from Tier 2 sprints
```

### 6.2 How to Use

**New project (Tier 1)**:
1. Copy `skills/` into your project's `.claude/skills/` and adapt for your language/domain
2. Create `~/.flowstate/{project-slug}/metrics/` and `~/.flowstate/{project-slug}/retrospectives/`
3. Copy `tier-1/flowstate.config.md` into `~/.flowstate/{project-slug}/` and fill in gate commands
4. Copy `tier-1/collect.sh` into `~/.flowstate/{project-slug}/metrics/`
5. Add Flowstate patterns to your project's `.gitignore`: `SPRINT-*.md`, `flowstate.config.md`, `metrics/`, `retrospectives/`, `.claude/skills/`
6. Write `docs/ROADMAP.md`: break PRD milestones into sprint-sized phases (see section 5.3 Phase B)
7. Fill in `tier-1/sprint.md` (replacing `{FLOWSTATE}` with `~/.flowstate/{project-slug}`) and paste to start

**Work project (Tier 2)**:
1. Copy `skills/` into your project's `.claude/skills/` and adapt
2. Create `~/.flowstate/{project-slug}/` for retros and config
3. Fill in `tier-2/sprint.md` with your scope and paste to start
4. After the sprint, review the sanitized export and copy to `imports/`

**Any LLM (Tier 3)**:
1. Open `tier-3/sprint.md` and paste each phase prompt sequentially

### 6.3 Invocable Skills (planned)

| Command | Action |
|---------|--------|
| `/bootstrap` | Generate project structure from PRD.md |
| `/sprint` | Run a full sprint (all 3 phases) |
| `/gate` | Run quality gates independently |
| `/retro` | Run retrospective independently |
| `/metrics` | Show metrics for current or all sprints |

These are not yet implemented as Claude Code skill files. Currently, sprints are run by copy-pasting the prompt templates.

### 6.4 Deferred

- **Invocable skill files**: sprint/bootstrap/retro as `.claude/skills/` that respond to `/commands`
- **Node CLI**: deferred until markdown + skills prove insufficient
- **Dynamic agent strategy**: subagent-only until agent teams are validated
- **Skill generation from PRD**: deferred until evidence shows what good generated skills look like

## 7. What Flowstate is NOT

- **Not a replacement for Claude Code**: runs on top of its native features
- **Not a SaaS product**: files you own, version control, and evolve
- **Not prescriptive about tech stack**: works with any language or framework
- **Not autonomous**: human reviews plans, approves gates, decides which retro changes to adopt
- **Not a finished framework**: it's a set of hypotheses being tested. Sprint 0 is the first experiment

## 8. Experiments and Results

Flowstate is validated through hypothesis-driven sprints across multiple projects. All experiment designs, hypothesis definitions, test protocols, sprint results, and cross-project analysis are documented in [RESULTS.md](RESULTS.md).

**Current state** (as of 7 sprints across 2 projects):
- 12 hypotheses tested (H1-H12), none falsified, H5 confirmed on both projects (Uluka S3 lint gate caught unused import, DS S0 clippy caught 3 bugs)
- Projects: Uluka (TypeScript CLI, 4 sprints), Dappled Shade (Rust P2P, 2 sprints)
- Per-project stability: **Uluka STABLE** (3/3 clean sprints), Dappled Shade 1/3

## 9. Tiered Portability

Flowstate runs in environments with different levels of tooling access. The tier system ensures the feedback loop works even when automated metrics collection or bash execution isn't available.

### 9.1 Tier Definitions

| Tier | Environment | What works | What doesn't | Feedback mechanism |
|------|-------------|------------|--------------|-------------------|
| **Tier 1: Full** | Personal machine, Claude Code with bash | Skills, gates, automated metrics (collect.sh), session log parsing, full retros | Everything works | Automated: collect.sh parses logs, retro proposes diffs |
| **Tier 2: Skills + Structure** | Work laptop, Claude Code without bash (or with restricted bash) | Skills, sprint structure, quality gates (run manually), agent coordination | Automated metrics, session log parsing, collect.sh | Sanitized export: agent produces metrics estimates + process observations; human redacts before exporting |
| **Tier 3: Prompt-only** | Any LLM interface (API playground, web chat) | Sprint structure as a prompting pattern | Skills, gates, agents, metrics | Manual: human applies the 3-phase pattern and records observations |

### 9.2 The Proprietary Code Firewall

Tier 2 exists specifically for environments where source code and architecture details must not leave the machine. The firewall rule:

**Nothing project-specific crosses the boundary.** Safe to export: process metrics (numbers), hypothesis pass/fail, generalized skill proposals, workflow observations. NOT safe: file content, acceptance criteria, implementation plans, gate logs containing code, architecture decisions, business logic.

The human is the firewall. The retro agent produces a full local retrospective (stays on the machine) AND a sanitized export (safe to bring back to Flowstate). The human reviews the sanitized export before copying it out.

### 9.3 Tier 2 Sprint Flow

Tier 2 sprints use a dedicated template (`tier-2/sprint.md`) with these differences from Tier 1:

1. **Phase 1+2**: Same single-prompt structure. Agent plans and executes without human break. Gates are listed in the prompt (the agent runs them or the human runs them manually).
2. **Phase 3**: Produces TWO outputs:
   - Full retrospective (local only, never exported)
   - Sanitized export using `tier-2/sanitized-export.md` — numbers and generalized observations only
3. **Retro storage**: Full retrospective saved to `~/.flowstate/{project-slug}/retrospectives/sprint-{N}.md` (stays local).
4. **Import**: Human copies the sanitized export to `imports/{codename}-sprint-{N}.md` in the Flowstate repo.

### 9.4 What the Feedback Loop Loses in Tier 2

Honest accounting of the degradation:

| Feedback signal | Tier 1 | Tier 2 |
|----------------|--------|--------|
| Exact token counts | Parsed from logs | Agent estimate (±20%) |
| Model mix breakdown | Parsed from logs | Agent estimate |
| Active session time | Calculated from timestamps | Agent estimate |
| Human idle time | Detected from log gaps | Not available |
| Gate pass/fail | Automated, exact | Reported by agent |
| Why a gate failed | Full log with code context | Generalized category only |
| Skill change proposals | Specific diffs with line numbers | Generalized patterns |
| What went wrong | Full evidence chain | Category + process observation |

The scoreboard stays running. The improvement loop gets weaker — we keep the "what" but lose most of the "why." This is acceptable because the alternative (no feedback at all from work projects) is worse.

### 9.5 Tier File Locations

| Tier | Files | Purpose |
|------|-------|---------|
| **Tier 1** | `tier-1/sprint.md`, `tier-1/flowstate.config.md`, `tier-1/collect.sh` | Full sprint with automated metrics |
| **Tier 2** | `tier-2/sprint.md`, `tier-2/sanitized-export.md` | Sprint with sanitized export, no bash metrics |
| **Tier 3** | `tier-3/sprint.md` | Self-contained prompt for any LLM |
| **Shared** | `skills/` (5 files) | Generic skill files, copied to `.claude/skills/` per project (gitignored) |
| **Imports** | `imports/` | Sanitized exports from Tier 2, named `{codename}-sprint-{N}.md` |
| **Per-project** | `~/.flowstate/{project-slug}/` | Config, sprints, metrics, retrospectives — outside the project repo |

## 10. Success Criteria

Flowstate succeeds when:

1. **Sprint 0 produces clear hypothesis results**: we know which Weaveto.do patterns transfer and which don't. "Inconclusive" results include a clear re-test plan.
2. **Sprint 1 on Uluka completes faster than Sprint 0**: the generalized workflow has less friction than the copy-pasted one
3. **Quality gates catch real issues**: at least one gate failure prevents shipping broken code (gates aren't decorative)
4. **Primary metrics are comparable across sprints**: we can answer "was Sprint 2 better than Sprint 1?" with data, not feelings
5. **Skills get shorter without getting worse**: after 3 sprints, total skill file line count has not increased AND first-pass gate success rate has not dropped. Line count alone is gameable — the pair is the real criterion.
6. **A third project can bootstrap in < 30 minutes**: copying Flowstate into a new repo and running `/bootstrap` produces a working sprint plan without Weaveto.do or Uluka-specific knowledge. **Achieved**: Dappled Shade bootstrapped in 9 minutes 10 seconds (see RESULTS.md section 8.2.0)

## 11. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Weaveto.do patterns don't generalize | Sprint 0 produces little reusable material | Sprint 0 is designed to discover this. Cheaper to learn now than after building a framework |
| Agent Teams experimental / unstable | Execution failures, lost work | Subagent-only until Sprint 2; commit frequently |
| Context rot in long sprints | Quality degradation | Hard session break at 50% context; fresh workers per wave |
| Skill files accumulate scar tissue | Context waste, contradictory instructions | Skill pruning every 3 sprints with never-triggered distinction; 200-line cap per skill |
| Retro changes don't improve outcomes | Self-improvement is theater | Require causal evidence (specific failure → specific fix). Reject proposals without evidence |
| Metrics are confounded by task difficulty | Can't tell if improvement is real or tasks were easier | Record task complexity estimate alongside metrics; compare similar-complexity sprints |
| Over-engineering the meta-system | Building Flowstate instead of actual products | Sprint 0 builds Uluka, not Flowstate. Flowstate is the byproduct, not the goal |
| Review fatigue on retro proposals | Human rubber-stamps bad changes | Retro produces diffs, not documents. Each change is individually approve/reject. Rejected changes include reasons |
| Skills are advisory but treated as enforcement | False confidence in code quality | Explicit skill-vs-gate distinction. Any important instruction gets a corresponding automated gate |
| Sprint 0 observation overload | Human can't build and evaluate simultaneously | Hypotheses tiered into must-test and observe-if-possible. Execution always beats observation |
| Retro produces paragraphs not diffs | Change proposals aren't actionable | Retro format gate enforces ≥1 diff block; rejects paragraph-only retros |
| Flowstate becomes a permanent meta-project | Always improving itself, never serving actual work | Exit criteria defined: stable state reached when 3 consecutive sprints produce no approved changes to core skills |

## 12. Stability and Exit Criteria

Flowstate is not meant to be perpetually evolving. The goal is to reach a **stable state** where the system works reliably and changes are rare.

**Stable state definition**: When 3 consecutive sprints on the same project produce no human-approved retrospective changes to core skill files, Flowstate is stable for that project type. At that point:

- Retrospectives still run (to catch regressions), but the expectation shifts from "improve the system" to "confirm the system still works"
- New changes require evidence of a **new failure mode**, not just ideas for improvement
- The human can skip the retro review step and only engage when the retro flags an actual gate failure or quality regression

**Cross-project stability**: Flowstate is globally stable when it has reached stable state on 3+ projects of different types (e.g., web app, CLI tool, API service). At that point, the core skills are validated across project shapes and further changes are exceptional.

This prevents Flowstate from becoming a permanent hobby project disguised as productivity tooling.
