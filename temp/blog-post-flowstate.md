# How I Stopped Babysitting AI Agents and Started Coaching Them

I built an encrypted task manager with AI agent teams. I wrote about it. People seemed interested in the workflow — the skills, the waves, the retrospectives. What I didn't tell you was that the workflow was held together with duct tape and copy-paste.

Every sprint, I was the bottleneck. I designed the sprint scope. I copy-pasted prompts into Claude Code. I manually collected metrics from session logs. I read the retro, decided what to change, applied the changes, wrote the next baseline, updated the roadmap. The agents built the software. I did everything else.

That's not a workflow. That's a job.

## The Problem With Getting Things Done

Let me back up. When I started building weaveto.do, I drew inspiration from Steve Yegge's Gastown and glittercowboy's Get Shit Done — two Claude Code frameworks that manage planning, execution, and verification. I asked Claude to research GSD's approach and recommend changes to my workflow, optimizing for token efficiency. That led to a 5-phase-to-3-phase consolidation that cut redundant context loads by 60%. The workflow I landed on got me through eight milestones of end-to-end encrypted software.

That workflow had learning loops — retrospectives fed forward into the next sprint's constraints, and the agents genuinely got better over time. But the loops were manual. Lots of check-ins. The retros were unstructured — useful observations buried in prose with no consistent format to parse or compare across sprints. I was reviewing every retro, hand-editing skill files, deciding what to change and when. It worked, but it didn't scale. And when I started a second project — a TypeScript security CLI called Uluka — I realized I was manually transferring lessons from one project to the other by editing skill files and hoping I remembered what I'd learned.

Here's the deal: I didn't need a better build tool. I needed a coaching framework. Something that treats each sprint as a training session, measures what happened, and adjusts the program for next time. If you've ever written a strength program, you know what I'm talking about. You don't just tell the client "lift heavy things." You work together to figure out the load, the volume, the intensity. You measure the response. You adjust.

So for my own sanity, I'm building Flowstate.

The vision is straightforward: a set of markdown files and Claude Code skills for sprint-based, multi-agent software development. PRD-first — every project starts with a spec. Empirical — patterns are hypotheses tested across projects, not axioms declared upfront. Human-steered — I review plans, approve gates, and decide which retrospective changes to adopt. The agents propose. I decide. For now...

The priorities are ordered and non-negotiable:

1. **Code quality.** Correct, tested, reviewed code ships. Gates are the hard constraint.
2. **Wall time.** Parallelism and smart delegation minimize calendar time.
3. **Token efficiency.** Model mix, context management, and caching minimize cost per unit of accepted work.

That ordering matters. I will never sacrifice code quality to save time, and I will never sacrifice time to save tokens. When they conflict, quality wins. And all three depend on something most people don't think about: managing the context window. This was one of the best things I took from GSD — an agent drowning in context makes worse decisions, runs slower, and burns more tokens. Keeping the context lean isn't just an efficiency play — it's a code quality play.

## What Flowstate Actually Is

Flowstate is a sprint framework for AI coding agent teams — still in progress, still changing after every sprint. It's not a library. It's not a CLI tool. It's a set of markdown files — sprint templates, skill definitions, and a metrics pipeline — that I run through Claude Code. The goal is simple: approach each new product methodically and learn from every project. I plan to open-source the whole thing — templates, skills, metrics pipeline, all of it — once it's easier to set up for new projects and I've figured out a way for people using it to contribute to the data pipeline without exposing their project details.

Here's the loop:

```
        ┌──────────────────────────────────────────────────────┐
        │                                                      │
        │                       HUMAN                          │
        │                                                      │
        │   • Decide what to build (roadmap)                   │
        │   • Review retro                                     │
        │   • Approve/reject skill changes                     │
        │                                                      │
        └───────────────┬──────────────────────────────────────┘
                        │ starts sprint
                        ▼
        ┌──────────────────────────────────────────────────────┐
        │                                                      │
        │   PHASE 1+2: THINK → EXECUTE                         │
        │                                                      │
        │   Orchestrator loads 5 skills, reads baseline + retro│
        │   Writes Gherkin criteria, plans waves               │
        │                                                      │
        │   Wave 1 (parallel)    Wave 2 (parallel)   Wave 3    │
        │   ┌───────┐┌───────┐  ┌───────┐┌───────┐  ┌──────┐   │
        │   │ haiku ││ haiku │  │sonnet ││ haiku │  │sonnet│   │
        │   └───────┘└───────┘  └───────┘└───────┘  └──────┘   │
        │                                                      │
        │   Quality Gates: tests, types, lint, coverage        │
        │                                                      │
        └───────────────┬──────────────────────────────────────┘
                        │ gates pass
                        ▼
        ┌──────────────────────────────────────────────────────┐
        │                                                      │
        │   PHASE 3: SHIP                                      │
        │                                                      │
        │   • Collect metrics from session logs                │
        │   • Write retro (hypothesis table, evidence)         │
        │   • Propose skill changes as diffs                   │
        │   • Write next sprint's baseline                     │
        │   • Update roadmap                                   │
        │   • Export metrics to Flowstate dataset              │
        │   • Commit                                           │
        │                                                      │
        └───────────────┬──────────────────────────────────────┘
                        │ retro + proposals
                        │
                        └──────────► back to HUMAN
```

The core loop is three phases:

**Phase 1+2: Think, then Execute.** One prompt. The agent loads five skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor), writes acceptance criteria in Gherkin format, plans wave-based execution, then immediately builds it. No human approval between planning and execution. The agent spawns parallel subagents for independent tasks — haiku for mechanical work, sonnet for reasoning — and runs quality gates when all waves complete.

**Phase 3: Ship.** The agent collects its own metrics from session logs, writes a retrospective with hypothesis results and evidence, proposes skill changes as diffs, writes the next sprint's baseline, and updates the roadmap. The agent proposes changes but doesn't apply them. I review after.

**Post-sprint: We learn.** The agent exports its metrics to Flowstate, which updates the cross-project hypotheses table — are gates catching real issues? Are skills being followed? Is token efficiency improving or regressing? I read the retro and approve or reject skill change proposals. The system learns from the data. I learn from the patterns. Next sprint starts from both.

The key insight — the thing that makes this different from just "prompts with extra steps" — is that every sprint produces structured data that feeds the next one. The baseline tells the agent where it's starting. The retro tells it what worked. The skill files tell it how to think. And the metrics tell me whether the whole system is actually improving or just generating activity.

## Ten Sprints In

I've run Flowstate across two projects so far. Uluka is a TypeScript security CLI — six sprints, from a greenfield Phase 14 through a v2.1 release and tech debt cleanup. Dappled Shade is a Rust P2P encrypted messaging app — four sprints, from an MVP through relay protocol implementation.

Ten sprints in one day. 90 million tokens. But only 2.6 million of those were new-work tokens — where the model is actually thinking, generating code, making decisions. The rest is cache reads. 96-98% cache hit rate on individual sprints, 97% aggregate across all ten — up from 95.7% on weaveto.do.

Here's what those sprints actually produced: ~14,000 lines inserted across two languages (TypeScript and Rust), 528 tests at the end of the latest sprints, quality gates passing on first attempt 70% of the time, and skill compliance climbing from 3/5 in Sprint 0 to a steady 4.5-5/5 by Sprint 3.

The token efficiency numbers tell a story. New-work tokens per line of code ranged from ~77 (Uluka S1, a big feature sprint) to ~442 (Uluka S4, a hardening sprint with lots of test boilerplate). The median is around 235. For context, that means the model spends roughly 235 tokens of actual reasoning to produce each line of shipped code. Everything else is context loading from cache.

## What We Actually Learned

### Skills work. Checklists don't.

After ten sprints of auditing skill compliance, the pattern is clear: **skills that state principles get followed. Skills that state procedures get skipped.** "All key material in Zeroizing wrappers" is a principle — the agent applies it everywhere without being told which files to touch. H7 compliance went from 3/5 to a steady 5/5. But "each red-green-refactor cycle is one atomic commit" is a procedure — ignored from Sprint 0 onward. Same with "use `--after` on metrics collection to isolate per-sprint data" — exact command syntax, no ambiguity, ignored every time. The fix was to kill the decision point: "ALWAYS use --after." One rule, no conditionals, now it works.

Skills shape how agents think. Checklists tell agents what to do. Agents are better at thinking than following procedures.

Skills also get better through the retro loop, but only when improvements come from evidence — and only when the retro proposes changes instead of describing problems. On weaveto.do, retrospectives were walls of text. 1,000-line documents with "What Worked" and "What Was Inefficient" and "Top 5 Actionable Changes." Good observations, but I still had to read the prose, figure out which skill file to open, and write the edit myself. That's not a feedback loop. That's a book report.

Flowstate retros produce diffs. Not "consider adding async trait guidance to the architect skill" — the literal `- Before` / `+ After` edit, with the file path and line number. I approve or reject each change individually. A format gate rejects any retro without at least one diff block. The difference in practice is that I actually review and apply the changes now, because the cost of reviewing a diff is near zero. The cost of decoding a paragraph into an action was high enough that I'd skip it when I was tired.

The skills that aged best are the ones that accumulated domain-specific scar tissue from real builds. The architect skill didn't start with "async fn in traits is NOT dyn-compatible — use generics at call sites." That came from a Rust sprint where clippy caught it. The haiku cost threshold — "single-file changes following exact existing patterns" — came from a sprint where a "mechanical" task turned out to need 25 tool uses across multiple files. Every useful skill refinement traces back to a specific sprint where something went wrong.

### Gates are how you ship code that works

If skills are how agents think, gates are how you know the code is actually good. This isn't insurance. This is the quality mechanism. Without gates, you're trusting an agent that will confidently tell you everything passes while silently introducing a type error.

Clippy caught async trait issues in Rust. The lint gate caught an unused import a subagent introduced in TypeScript. Coverage gates prevented regression. These aren't edge cases — they're what happens every sprint when multiple subagents are writing code in parallel and nobody's reviewing each other's work. The gates are the review.

And here's the thing people miss about gates: they compound. A coverage gate doesn't just catch this sprint's regression. It prevents every future sprint from starting on a codebase where tests are already broken. A type-check gate means the next agent inherits code that compiles. Each gate protects the baseline for the next sprint, which means each sprint starts cleaner than it would have otherwise. Over ten sprints, that's the difference between a codebase that works and one that's held together by accident.

### Agents get better, but not the way you'd expect

The agents don't remember anything between sessions. They can't. Every session starts from zero — read the skills, read the baseline, read the retro, go. The "improvement" comes from three things the human controls: better skill instructions (from reviewing retro proposals), tighter gate thresholds (from observing what gates catch), and cleaner baselines (from each sprint's output feeding the next sprint's input).

The agent isn't learning. The system is learning. The agent is just the latest instantiation of the system's accumulated knowledge. Think of it like a game save file. The agent starts every session at level 1 with no memory. But the save file — the skills, the baseline, the retro — tells it exactly where the game left off and what strategies worked. The save file is everything.

### Self-contained modules are cheaper

This one's from the data. One sprint built a feature that was completely independent from the rest of the codebase — new module, no shared dependencies, no need to understand existing code. It produced nearly twice the lines of code as the previous sprint while using fewer new-work tokens — 125 tokens per line of code vs 241, a 48% improvement in efficiency. The agent didn't have to load half the project into context just to get started.

If you're designing for AI agent teams, keep your modules independent. Not because it's good software engineering (it is), but because every file an agent has to read costs tokens, and tokens cost money or time or both. The less context an agent needs to do its job, the cheaper and faster it works.

### My role is narrowing correctly

Sprint 0: I designed the sprint, wrote the prompts, collected metrics, wrote retro summaries, updated the roadmap, applied skill changes, created the next baseline.

Sprint 5: I said "start the next sprint." The agent read its CLAUDE.md, found the roadmap, picked up the next phase, read the baseline, loaded the skills, planned, built, gated, retro'd, and wrote the next baseline. I reviewed the retro and imported the metrics.

The remaining human tasks are: decide what to build (roadmap), approve skill changes (quality control on the meta-level), and fix metrics when the agent gets them wrong (still working on this one). The first two are genuinely human decisions. The third is a bug.

## What Doesn't Work Yet

I'm not going to pretend this is solved. Three problems I'm still working on:

**Agents skip steps when you're not watching.** Phase 3 has seven steps. Agents reliably do five or six of them. The fix we landed on is a completion checklist — the last step in Phase 3 requires the agent to print each artifact as `[x]` or `[MISSING]` and fix anything missing before declaring done. We'll see if it works. (I might be wrong though.)

**Multi-sprint sessions contaminate data.** Uluka ran five sprints in a single session with context compaction. The metrics blended together. Active time, token counts, subagent counts — all cumulative. We had to re-run the collection script with timestamp filters to isolate each sprint. The fix is simple: one sprint per session. Fresh context, clean data.

**Dual-tracking systems create confusion.** Uluka had GSD installed — the actual framework, not just inspiration from it — alongside Flowstate. Two roadmaps, two state files, two sets of phase tracking. The agent found GSD's `.planning/ROADMAP.md` instead of Flowstate's `docs/ROADMAP.md` and silently used the wrong one. We ripped GSD out entirely. Dappled Shade never had GSD and never had this problem.

## The Part Where I Get Philosophical

I spent a decade as a strength coach before I built software. The best training programs I wrote weren't sophisticated. They were the most learnable. They had simple primatives and tight feedback loops — train, measure, adjust. They didn't require the client to be perfect. They required the system to be honest about what happened and disciplined about what to change.

Flowstate is the same idea applied to AI agents. The agents aren't perfect. They skip steps. They ignore instructions. They produce cumulative metrics when you asked for per-sprint data. You have to always remember **they are well intentioned liars.** So build a system that catches what they miss, measures what they produce, and adjusts what it asks for next time.

Ten sprints across two projects, two languages, two very different codebases. The inner loop works — plan, build, test, retro. The outer loop is getting there — import metrics, validate retro completeness, update cross-project tables. The human's job is shrinking to the parts that should be human: deciding what matters and verifying that it's true.

It's not autopilot. It's a feedback loop. The system measures what happened, I decide what to change, and the next sprint starts from a better place. No magic. Just discipline and data.

Flowstate isn't done. I'm ten sprints in and still fixing how agents collect their own metrics. But every sprint teaches me something about how to coach these things, and that's the point. The framework improves because I use it. I use it because it improves.

---

## Appendix: Sprint Data

| Sprint | Time | Total Tokens | New-Work | LOC | Tokens/LOC | Tests | Coverage | Gates 1st | Subagents | H7 (Skills) |
|--------|------|-------------|----------|-----|-----------|-------|----------|-----------|-----------|-------------|
| Uluka S0 | 17m 39s | 9.4M | 287K | 1,200 | 239 | 237 | 65.7% | Yes | 3 | 3/5 |
| Uluka S1 | 21m 51s | 8.4M | 197K | 2,542 | 77 | 320 | 69.8% | Yes | 3 | 4/5 |
| Uluka S2 | 10m 44s | 6.1M | 211K | 826 | 255 | 348 | 69.9% | Yes | 3 | 4.5/5 |
| Uluka S3 | 12m 37s | 6.9M | 83K | 890 | 93 | 370 | 70.2% | No | 3 | 5/5 |
| Uluka S4 | 49m 29s | 9.2M | 362K | 820 | 442 | 404 | 70.3% | Yes | 3 | 4.5/5 |
| Uluka S5 | 59m 2s | 8.7M | 149K | 645 | 231 | 406 | 70.3% | Yes | 2 | 4/4 |
| DS S0 | 37m 43s | 16.8M | 630K | 3,268 | 192 | 57 | — | No | 14 | 4/5 |
| DS S1 | 16m 3s | 9.2M | 274K | 1,135 | 241 | 75 | — | Yes | 4 | 4.5/5 |
| DS S2 | 94m 15s | 7.8M | 265K | 2,114 | 125 | 114 | — | No | 4 | 4/5 |
| DS S3 | 65m 22s | 7.3M | 187K | 737 | 254 | 122 | — | Yes | 4 | — |
| **Totals** | | **89.8M** | **2.6M** | **~14,000** | **235 median** | **528 latest** | | **7/10** | | |
