# Flowstate Sprint — Prompt-Only (Tier 3)

> Works in any LLM interface: ChatGPT, Claude web, API playground, Cursor, etc.
> No skills, no agents, no bash. Just the 3-phase structure as a prompting pattern.

---

## Phase 1: THINK

Paste this at the start of your session:

```
I'm building [describe what you're building].

Before writing any code, act as both a product manager and a system architect:

1. Write acceptance criteria for this scope. For each requirement, describe:
   - The happy path (what should happen when it works)
   - At least one failure or edge case (what happens when input is bad, state is wrong, etc.)

2. Write an implementation plan:
   - Break the work into sequential steps ordered by dependency
   - For each step: what files are read, what files are written
   - Flag any steps that could be done in parallel (no shared files)

Do not write any code yet. Just the plan.
```

## Phase 2: EXECUTE

After reviewing the plan, paste:

```
Execute the implementation plan you just produced.

After completing each step:
- Verify it works (run tests, check types, or manually verify)
- Commit or note what was done before moving to the next step

If something from the plan doesn't work as expected, adjust the plan and continue.
Don't skip steps or combine them unless they're truly trivial.

When all steps are complete, run these checks:
- [your build command]
- [your test command]
- [your lint command]

Report what passed and what failed.
```

## Phase 3: REVIEW

After execution is complete, paste:

```
Review what was just built:

1. What was delivered? (list files changed, tests added, features completed)
2. What worked well? (specific patterns or decisions that went smoothly)
3. What went wrong or was harder than expected? (be specific)
4. If you were doing this again, what would you change about the plan?
5. Are there any quality issues in the code that should be fixed before shipping?
```

---

## Tips

- **Phase 1 is the most important.** A good plan prevents most execution problems. Don't rush it.
- **Phase 2 can span multiple messages.** If context gets long, summarize progress and continue.
- **Phase 3 is where you learn.** The review isn't just for this session — it tells you what to do differently next time.
- **You are the gate.** Without automated checks, you decide whether the code is ready to ship. Read the output critically.
