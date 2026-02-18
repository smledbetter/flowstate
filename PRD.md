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
| Custom gates | None | Command + pass/fail criteria |

**Custom gates** are how skill instructions become enforceable. Example: the security auditor skill says "no plaintext logging." The corresponding custom gate is: `grep -r "console.log\|console.error" src/ --include="*.ts" | grep -v "// allowed"` must return empty.

**Retro format gate**: the retrospective must contain at least one `- Before` / `+ After` diff block, or it is rejected. This prevents agents from producing paragraph-style retros instead of actionable diffs.

Failed gates produce specific findings with file paths and line numbers, not just pass/fail.

### 4.7 Metrics

Metrics are organized into **primary** (drive decisions) and **diagnostic** (investigated when a primary metric goes wrong).

**Primary metrics** — look at these every sprint:

| Metric | What it measures | Decision it drives |
|--------|-----------------|-------------------|
| First-pass gate success rate | Did code pass gates before fixes? | Skill quality — are agents writing correct code? |
| Active session time | Sum of active session durations from sprint start to ship (see note) | Parallelism effectiveness |
| Total new-work tokens | Non-cache tokens consumed | Raw cost of the sprint |

**Active session time note**: A sprint may span multiple agent sessions (due to the 50% context break rule). Active session time is the sum of active session durations, not the delta between first session start and last session end. Breaks between sessions (human away from keyboard, overnight gaps) are excluded. Session durations are parsed from Claude Code's JSONL session logs — each log entry has a `timestamp` field, so active session time is `last_event_timestamp - first_event_timestamp`. No manual recording needed.

**Session log structure**: Parent session logs live at `~/.claude/projects/{project-slug}/{session-id}.jsonl`. Subagent sessions are stored in `~/.claude/projects/{project-slug}/{session-id}/subagents/agent-{id}.jsonl`. Token usage and model mix must include subagent logs — otherwise the report only reflects the orchestrator's API calls and misses all worker token usage. The `metrics/collect.sh` script automatically discovers and includes subagent logs for each parent session.

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
| Context utilization at session end | When quality degrades late in a sprint |

**What we explicitly don't track** (yet): LOC as a productivity metric, skill change "impact" (no causal mechanism), "context utilization %" as a quality proxy (high read-to-write ratios can be correct behavior).

Metrics are stored in `metrics/sprint-{N}.json` and a summary appended to `metrics/HISTORY.md`.

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

The human can: approve, modify, or reject each change individually. Rejected changes include a reason that feeds into the next retro ("Human rejected X because Y — do not re-propose without new evidence").

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
├── flowstate.config.md             # Flowstate configuration
├── .claude/
│   └── skills/                     # Skill files
│       ├── product-manager.md
│       ├── ux-designer.md
│       ├── architect.md
│       ├── production-engineer.md
│       ├── security-auditor.md
│       └── {project-specific}.md
├── docs/
│   ├── milestones/
│   │   └── M{N}-{name}/
│   │       ├── acceptance.md       # Gherkin acceptance criteria
│   │       └── implementation.md   # Wave-based execution plan
│   ├── STATE.md                    # Current project state
│   └── research/                   # Cached knowledge artifacts
├── metrics/
│   ├── sprint-{N}.json             # Raw metrics per sprint
│   └── HISTORY.md                  # Human-readable trends
├── retrospectives/
│   └── sprint-{N}.md               # Retro report + change proposals
└── src/                            # Project source code
```

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
4. Human reviews and approves

Skills are **copied and adapted** from Flowstate's generic set, not generated from scratch. The architect may suggest which skills to include or exclude based on the PRD (e.g., "skip UX designer for a CLI tool"), but skill generation from PRD content is deferred until there's evidence about what good generated skills look like.

**Phase B: Planning** (fresh agent session)
1. Architect reads PRD.md + approved config from Phase A + copied skill files
2. Proposes milestone breakdown with acceptance criteria
3. Creates first sprint plan (M1 implementation.md)
4. Human reviews and approves
5. Sprint 1 begins

Splitting bootstrap prevents the architect from planning milestones in a context window already full of generated config.

### 5.4 Sprint Execution Flow

```
Human says: "sprint" or "start sprint for M{N}"

PHASE 1+2: THINK then EXECUTE (single prompt, no human break)
├── Architect loads: PRD, STATE.md, metrics/HISTORY.md, last retro
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

PHASE 3: SHIP
├── git push (human approves)
├── Doc sync: update STATE.md, milestone status
├── Retrospective:
│   ├── Collect primary + diagnostic metrics
│   ├── Compare to previous sprint
│   ├── Write report (what worked, what failed, with evidence)
│   ├── Propose changes as diffs (not paragraphs)
│   ├── Retro format gate: must contain ≥1 diff block or rejected
│   └── Write: retrospectives/sprint-{N}.md
├── Human reviews retro:
│   ├── Approve/modify/reject each proposed change
│   ├── Rejected changes include reason
│   └── Approved changes applied to skills/config
└── Sprint complete
```

## 6. Deliverables

Flowstate ships as **markdown files + Claude Code skills** copied into a project:

### 6.1 Core Files

| File | Purpose |
|------|---------|
| `skills/product-manager.md` | Generic PM perspective |
| `skills/ux-designer.md` | Generic UX perspective |
| `skills/architect.md` | Orchestration, agent strategy, system design |
| `skills/production-engineer.md` | Testing, quality gates, CI |
| `skills/security-auditor.md` | Security review, threat modeling |
| `skills/bootstrap.md` | Bootstrap a project from PRD (2-phase) |
| `skills/sprint.md` | Run a sprint (3-phase lifecycle) |
| `skills/retrospective.md` | Run retro, propose changes as diffs |
| `templates/flowstate.config.md` | Default configuration |
| `templates/acceptance.md` | Acceptance criteria template |
| `templates/implementation.md` | Implementation plan template |
| `templates/retrospective.md` | Retrospective template |
| `templates/STATE.md` | Project state template |

### 6.2 Invocable Skills

| Command | Action |
|---------|--------|
| `/bootstrap` | Generate project structure from PRD.md (2-phase) |
| `/sprint` | Run a full sprint (all 3 phases) |
| `/think` | Phase 1 only |
| `/execute` | Phase 2 only |
| `/ship` | Phase 3 only |
| `/gate` | Run quality gates independently |
| `/retro` | Run retrospective independently |
| `/metrics` | Show metrics for current or all sprints |
| `/status` | Show current project state |

### 6.3 Deferred

- **Metrics collector**: Sprint 0 uses a shell script (`metrics/collect.sh`) that parses Claude Code JSONL session logs. If the log format changes in a future Claude Code update, fixing the parser is a Sprint 1 task.
- **Node CLI**: deferred until markdown + skills prove insufficient.
- **Dynamic agent strategy**: subagent-only in Sprint 0. Teams added in Sprint 2 after subagent patterns are validated.
- **Skill generation from PRD**: deferred until Sprint 1+ reveals what good generated skills look like. Bootstrap uses copy + adapt.

## 7. What Flowstate is NOT

- **Not a replacement for Claude Code**: runs on top of its native features
- **Not a SaaS product**: files you own, version control, and evolve
- **Not prescriptive about tech stack**: works with any language or framework
- **Not autonomous**: human reviews plans, approves gates, decides which retro changes to adopt
- **Not a finished framework**: it's a set of hypotheses being tested. Sprint 0 is the first experiment

## 8. Experiments and Results

Flowstate is validated through hypothesis-driven sprints across multiple projects. All experiment designs, hypothesis definitions, test protocols, sprint results, and cross-project analysis are documented in [RESULTS.md](RESULTS.md).

**Current state** (as of 6 sprints across 2 projects):
- 12 hypotheses tested (H1-H12), none falsified, H5 inconclusive on Uluka (gates keep passing first try)
- Projects: Uluka (TypeScript CLI, 3 sprints), Dappled Shade (Rust P2P, 2 sprints)
- Per-project stability: Uluka 2/3 clean sprints, Dappled Shade 1/3

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

Tier 2 sprints use a dedicated template (`templates/SPRINT-TIER2.md`) with these differences from Tier 1:

1. **Phase 1+2**: Same single-prompt structure. Agent plans and executes without human break. Gates are listed in the prompt (the agent runs them or the human runs them manually).
2. **Phase 3**: Produces TWO outputs:
   - Full retrospective (local only, never exported)
   - Sanitized export using `templates/sanitized-export.md` — numbers and generalized observations only
3. **Import**: Human copies the sanitized export to `imports/{codename}-sprint-{N}.md` in the Flowstate repo.

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

### 9.5 Tier 2 Files

| File | Purpose |
|------|---------|
| `templates/SPRINT-TIER2.md` | Sprint prompt template for restricted environments |
| `templates/sanitized-export.md` | Redacted export template (human fills in after reading full retro) |
| `imports/` | Directory for imported sanitized exports, named `{codename}-sprint-{N}.md` |

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
