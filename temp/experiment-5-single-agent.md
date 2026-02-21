# Experiment 5: Single-Agent Sprint

## Question

Does multi-agent delegation (Task tool, subagents) improve sprint outcomes compared to a single opus session?

## Design

Run Uluka Sprint 9 (Phase 22: Claim Extraction Quality) with a single agent constraint:
- No Task tool usage
- No subagent delegation
- One opus session does all work: planning, implementation, testing, gates

Compare against multi-agent baselines from Uluka S6 and S8.

## Constraint Prompt

Added to the sprint Phase 1+2 prompt:

> **Experiment constraint**: Do NOT use the Task tool or delegate to subagents. Complete all work — planning, implementation, testing, gate checks — in this single session. This is testing whether multi-agent delegation improves outcomes for a codebase of this size.

## Results

| Dimension | Multi-Agent (S6/S8 avg) | Single-Agent (S9) |
|-----------|-------------------------|---------------------|
| Active time | 10m 28s | 11m 22s |
| New-work tokens | 212K | 130K (-39%) |
| LOC produced | 830 | 1,226 (+48%) |
| Gate first-pass | 50% | 100% |
| Context compressions | 0 | 0 |

Single-agent produced more code with fewer tokens, passed all gates on the first attempt, and never hit context limits.

## Conclusion

For Uluka-sized codebases, single-agent is strictly better. The coordination overhead of multi-agent delegation (writing prompts, reading results, handling handoffs) is pure waste when the context window isn't a constraint. Default to single-agent until you hit context limits or have genuinely independent workstreams.
