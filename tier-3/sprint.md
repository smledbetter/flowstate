# Flowstate Sprint — Prompt-Only (Tier 3)

> Works in any LLM interface: ChatGPT, Claude web, API playground, Cursor, etc.
> No skills, no agents, no bash. Just the 3-phase structure as a prompting pattern.

---

## Before You Start

Have these ready before pasting the first prompt:

- Your project's **build command** (e.g., `npm run build`, `cargo build`, `go build ./...`)
- Your project's **test command** (e.g., `npm test`, `cargo test`, `pytest`)
- Your project's **lint command** (e.g., `eslint .`, `clippy`, `ruff check .`)
- A way to **run the real system** for a quick manual or automated smoke test
- Any existing project docs, README, or specs the LLM should reference

---

## Phase 1: THINK

Paste this at the start of your session:

```
I'm building [WHAT: what it does in one sentence].
[WHO: who uses it and how]
[CONTEXT: what already exists — language, framework, key files, test count]
[SCOPE: what THIS session should deliver — be specific]

Before writing any code, analyze this from five perspectives:

- Product: Does the scope make sense? Are requirements clear and testable? Is anything ambiguous?
- UX: If there's a user-facing surface, are error states, edge cases, and accessibility considered?
- Architecture: Are module boundaries clean? Are dependencies justified? Is the design the simplest thing that works?
- Production: Is this testable, deployable, and observable? Are failure modes handled?
- Security: Are inputs validated at boundaries? Are there injection, auth, or data exposure risks?

Then produce:

0. FEASIBILITY CHECK (do this first):
   - List every new dependency this scope requires (libraries, APIs, services)
   - For each: confirm it exists, is maintained, and the specific API you need is available
   - Identify the single highest-risk technical task. Describe how you would verify it works before building everything else around it
   - If anything is unverified or experimental, flag it now with a fallback plan

1. Acceptance criteria for this scope. For each requirement:
   - The happy path (what should happen when it works)
   - At least one failure or edge case (what happens when input is bad, state is wrong, network fails, etc.)

2. An implementation plan grouped into waves:
   - Wave = a group of tasks that share no files and could theoretically run in parallel
   - Order waves by dependency (wave 2 depends on wave 1 output, etc.)
   - For each task: files read, files written, what it produces
   - If the feasibility check flagged a risk, the spike/verification task goes in wave 1

Do not write any code yet. Just the plan.
```

## Phase 2: EXECUTE

After reviewing the plan, paste:

```
Execute the implementation plan you just produced, wave by wave.

After completing each wave:
- Verify it works (run tests, check types, or manually verify)
- Commit or note what was done before moving to the next wave

If something from the plan doesn't work as expected, stop, adjust the plan, and explain what changed before continuing. Don't silently deviate.

When all waves are complete, run these checks in order:
1. Build: [your build command]
2. Lint: [your lint command]
3. Tests: [your test command]
4. Smoke test: [one command or manual step that exercises the real system end-to-end, not just unit tests]

For each check that fails:
- Classify the failure: is this a REGRESSION (something that worked before) or a NEW issue (from this session's work)?
- Fix the issue and re-run that check
- If it still fails after 3 attempts, stop and report what's blocking — don't loop forever

Report the final status of all four checks.
```

## Phase 3: REVIEW

After execution is complete, paste:

```
Review what was just built:

1. What was delivered? (files changed, tests added, features completed)
2. What worked well? (specific patterns or decisions that went smoothly)
3. What went wrong or was harder than expected? (be specific — name the task, the assumption, and what actually happened)
4. If you were doing this again, what would you change about the plan?
5. Are there any quality issues in the code that should be fixed before shipping?

Then set up the next session:
6. Write a "current state" summary I can paste into my next session:
   - What was completed
   - What was deferred or left unfinished (and why)
   - Current status of build/test/lint (all passing?)
   - What the next session should do first
```

---

## Tips

- **Phase 1 is the most important.** A good plan prevents most execution problems. Don't rush it. If the plan looks weak, ask the LLM to revise it before moving to Phase 2.
- **The feasibility check exists because of real failures.** A dependency that doesn't exist, an API that changed, a library that doesn't compile — these waste entire sessions. Five minutes of verification saves hours.
- **Phase 2 can span multiple messages.** If context gets long, summarize progress and continue.
- **The smoke test is not optional.** Unit tests pass while the real system is broken more often than you'd expect. Run the actual thing.
- **Phase 3 is where you learn.** The review isn't just for this session — the "current state" summary is what makes your next session productive instead of starting cold.
- **You are the gate.** Without automated CI, you decide whether the code is ready to ship. Read the output critically.
