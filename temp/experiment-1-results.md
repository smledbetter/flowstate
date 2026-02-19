# Experiment 1 Results: No-Flowstate Baseline

Date: 2026-02-19

## Protocol

Ran two sprints without Flowstate (no skills, no CLAUDE.md, no wave structure, no consensus agent). Plain prompt: "Implement [scope]. Read the PRD and codebase, plan your approach, then execute. Run tests/lint/build when done."

## Uluka S7 (Phase 21: Crypto Library Knowledge Base)

### Metrics

| Metric | Baseline | Flowstate Avg (S4-S6) | Delta |
|--------|----------|----------------------|-------|
| Active session time | 5m 38s | 43m 31s avg | **7.7x faster** |
| Total tokens | 2.3M | 9.7M avg | **4.2x fewer** |
| New-work tokens | 123K | 218K avg | **1.8x fewer** |
| LOC added | 963 | 682 avg | 41% more code |
| New-work tokens/LOC | 128 | 185 avg (range: 93-442) | **30% more efficient** |
| Tests added | 42 | 36 avg | Comparable |
| API calls | 40 | 104 avg | **2.6x fewer** |
| Gates | All pass | 2/3 first pass | Comparable |

### Blind Quality Review (5 dimensions, 0-5 each)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Acceptance criteria clarity | 4 | Delivered scope but no explicit ACs |
| Module boundary cleanliness | 5 | Clean registry/verifier separation |
| Test-first evidence | 4 | 42 thorough tests, can't verify TDD ordering |
| Input validation | 3 | `findLibrariesByImport` uses `.includes()` (fragile), loose fallback regex |
| Error message quality | 3 | Good explanations but N/A for user-facing |
| **Total** | **19/25 (76%)** | |

### Commit
- `431e021` on Uluka main

---

## Dappled Shade S5 (M3 Phase 2: Mesh Resilience)

### Metrics

| Metric | Baseline | DS Flowstate Avg (S0-S4) | Delta |
|--------|----------|-------------------------|-------|
| Active session time | 6m 19s | 28m avg | **4.4x faster** |
| Total tokens | 5.1M | 9.4M avg | **1.8x fewer** |
| New-work tokens | 185K | 322K avg | **1.7x fewer** |
| LOC added | 1,338 | 1,722 avg | 22% less code |
| New-work tokens/LOC | 138 | 187 avg | **26% more efficient** |
| Tests added | 19 | 20 avg | Comparable |
| API calls | 68 | 155 avg | **2.3x fewer** |
| Cache hit rate | 96.4% | 96.6% avg | Same |
| Gates (manual) | All pass | 3/5 first pass | Comparable |

### Blind Quality Review (5 dimensions, 0-5 each)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Acceptance criteria clarity | 4 | Delivers roadmap scope, no explicit ACs doc |
| Module boundary cleanliness | 5 | Wire format in proto, behavior in gossip |
| Test-first evidence | 4 | 19 tests with ASCII topology diagrams |
| Input validation | 5 | Strong: length checks, utf-8, signature verify, self-skip |
| Error message quality | 4 | Specific deserialization errors, good API design |
| **Total** | **22/25 (88%)** | |

### Quality gap found
- `process_message_resilient()` is dead code (delegates to `process_message` with no added logic)

### Not yet committed (uncommitted changes on DS main)

---

## Falsification Verdicts

### H1: 3-phase sprint works across project types
**Weakened, not falsified.** Both baselines completed faster with comparable quality. The 3-phase structure adds overhead that doesn't pay for itself on well-scoped, single-module milestones. However, we haven't tested oversized or multi-module scope (that's Experiment 4).

### H7: Skills are followed by agents (and improve quality)
**Partially falsified.** Blind quality scores: 76% (Uluka) and 88% (DS) vs self-assessed 100%. The baselines score *differently* (not uniformly worse), suggesting skills shape behavior but don't necessarily improve it. Input validation was the one area where skills might have helped (Uluka scored 3/5 without them).

### H4: Wave parallelism helps
**Not tested** — neither baseline sprint used subagents or parallelism. Both completed in single-threaded execution. This doesn't falsify H4 (the milestones may have been too small to benefit from parallelism) but it does show parallelism isn't needed for well-scoped work.

### H2: 5-skill set is right
**Weakened.** The baselines produced comparable code without any skills loaded. The skill set may be right but the evidence that it's *necessary* is weak.

### H3: Consensus agent works
**Not directly tested.** No consensus agent was used. The code quality suggests a single agent's judgment is sufficient for well-scoped milestones.

---

## Key Takeaway

The no-Flowstate baseline produced comparable or better quality code 4-8x faster across both projects and both languages. The efficiency gap is far larger than the quality gap. Flowstate's value proposition may be limited to:
1. Large, multi-module sprints where planning prevents wrong turns
2. Scope management (preventing over/under-delivery)
3. Cross-session continuity (progress files, roadmaps)
4. Hypothesis tracking itself (meta-value of measuring)

The next experiments (adversarial gates, blind compliance, scope stress) will test whether these remaining value propositions hold up.
