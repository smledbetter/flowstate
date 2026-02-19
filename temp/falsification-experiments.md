# Falsification Experiments

Four experiments designed to produce real evidence. Each has an explicit falsification criterion -- if it triggers, the hypothesis is falsified. No wiggle room.

---

## Experiment 1: No-Flowstate Baseline (targets H1, H2, H3, H4, H7)

**The question**: Does Flowstate actually help, or would the agent produce similar results without it?

**Protocol**:
1. Pick the next Uluka milestone (Phase 21). Write a plain prompt: "Implement [scope]. Read the PRD and codebase, plan your approach, then execute. Run tests, lint, and type-check when done."
2. No skills loaded. No `CLAUDE.md` sprint instructions. No wave structure. No consensus agent. No feasibility check. Just Claude Code with the project's existing test/lint/build commands.
3. Run in a fresh session. Collect metrics with collect.sh afterward (it works regardless of Flowstate).
4. Compare to Uluka S4-S6 averages (similar maturity phase):
   - Tokens/LOC
   - Active session time
   - Tests added
   - Gate pass rate (run the same gates manually after)
   - Bugs found in manual review (you review the code yourself for 15 minutes)

**Falsification criteria**:
- **H1 falsified if**: The no-Flowstate sprint produces comparable or better quality (same gate pass rate, similar test count, no bugs you catch in review) in comparable or less time.
- **H7 falsified if**: The code output is indistinguishable from a skills-guided sprint. (If skills don't change behavior, compliance is meaningless.)
- **H4 falsified if**: The agent naturally parallelizes work without wave instructions. (If Claude Code does this by default, wave structure adds nothing.)

**Time cost**: One sprint (~30 min). You're building a real milestone, so no wasted work.

---

## Experiment 2: Adversarial Gate Test (targets H5, H8, H9)

**The question**: Do gates catch functional bugs, or just lint?

**Protocol**:
1. Before the next Uluka sprint, plant 3 bugs in the codebase on a branch:
   - **Bug A (logic)**: Introduce an off-by-one error in a data flow function. Tests pass because existing tests don't cover that edge.
   - **Bug B (regression)**: Break an existing test by changing a return value. The test file exists but the specific assertion is missing.
   - **Bug C (security)**: Add an unsanitized input path that the security auditor skill explicitly warns about.
2. Run a normal Flowstate sprint on this branch. The sprint scope is unrelated to the planted bugs -- the agent is building a new feature.
3. After Phase 2 gates run, check: did any gate catch Bug A, B, or C?
4. After Phase 3 retro, check: did the security audit or any skill perspective flag Bug C?

**Falsification criteria**:
- **H5 falsified if**: Zero of the 3 planted bugs are caught by gates. Gates only catch what the agent introduces in the current sprint, not pre-existing issues. They're a formatting check, not a quality check.
- **H8 falsified if**: Bug B (the regression) is not caught by the coverage/test gate.
- **H9 falsified if**: Bug C (the security issue) is not caught by lint or the security audit.

**Note**: If gates catch 1 of 3, that's partial -- record which category gates are actually good at (lint/style vs logic vs security).

**Time cost**: 20 minutes to plant bugs. Sprint runs normally.

---

## Experiment 3: Blind Compliance Scoring (targets H7)

**The question**: Is skill compliance real, or is the agent just doing what any competent agent would do?

**Protocol**:
1. After the next DS sprint completes, take the git diff and test output.
2. Give the diff to a fresh Claude session with this prompt: "Review this code change. Score it on these 5 dimensions: (a) acceptance criteria clarity, (b) module boundary cleanliness, (c) test-first development evidence, (d) input validation at boundaries, (e) user-facing error message quality. Score each 0-5 with specific evidence."
3. The reviewer has NO access to the skills. It's scoring the code on its own judgment.
4. Compare the blind scores to the sprint's H7 self-assessment.

**Falsification criteria**:
- **H7 falsified if**: The blind reviewer gives scores >= the self-assessed compliance on 4+ of 5 dimensions. This means the skills didn't cause better code -- the code would have been the same quality without them.
- **H7 partially falsified if**: The blind reviewer identifies the same strengths but also flags weaknesses the self-assessment missed.

**Time cost**: 10 minutes. One extra Claude session after a normal sprint.

---

## Experiment 4: Scope Stress Test (targets H1, H6)

**The question**: Does the 3-phase structure break under pressure, or does it just degrade gracefully into something unrecognizable?

**Protocol**:
1. Pick a DS milestone that's deliberately too large for one sprint. Something that would normally be 2-3 sprints.
2. Run it as a single Flowstate sprint. Don't tell the agent to split it. Use the standard Phase 1+2 prompt.
3. Observe:
   - Does Phase 1 (THINK) identify the scope is too large and propose splitting?
   - Does the agent hit context compression? How many times?
   - Does quality degrade in later waves (more gate retries, worse test coverage)?
   - Does the agent deviate from the plan silently?

**Falsification criteria**:
- **H1 falsified if**: The agent completes the oversized sprint by silently dropping requirements or producing broken code that passes gates. The 3-phase structure "succeeded" but the output is incomplete or wrong.
- **H6 falsified if**: Context compressions > 2 AND quality metrics (gate pass, coverage) are worse than the project average. The context budget hypothesis is wrong -- context fills up and quality suffers.
- **H1 strengthened if**: The agent explicitly flags the scope problem in Phase 1 and proposes splitting. This is what a working phase structure should do.

**Time cost**: One sprint. You might need to finish the remaining work in a follow-up sprint, so budget for that.

---

## Scheduling

| Sprint | Project | Experiment | Hypotheses Targeted |
|--------|---------|-----------|-------------------|
| Uluka S7 | Uluka | Exp 1: No-Flowstate baseline | H1, H2, H3, H4, H7 |
| Uluka S8 | Uluka | Exp 2: Adversarial gates | H5, H8, H9 |
| DS S5 | DS | Exp 3: Blind compliance | H7 |
| DS S6 | DS | Exp 4: Scope stress test | H1, H6 |

Run Exp 1 first. It's the most important -- if the baseline is just as good, everything else is moot.

---

## What changes after

After all 4 experiments:
- Any falsified hypothesis gets marked falsified in hypotheses.json and sprints.json. No downgrading to "inconclusive."
- Partially falsified hypotheses get specific conditions added: "H5 confirmed for lint/style, falsified for logic bugs."
- The dashboard gets a new color: red dots on the heatmap. If we've been doing this right, some should appear.
- H13 gets removed from sprints.json. It was never in the registry and violates the H12 cap.
- PRD section 8 gets updated with honest language about what's confirmed vs unconfirmed.

The goal is not to destroy Flowstate. It's to find out which parts actually work so you can trust the ones that survive.
