# Experiment 3+4 Results: Blind Scoring + Scope Stress

Date: 2026-02-19

## Experiment 4: Scope Stress Test (DS Sprint 6)

### Protocol

Ran DS Sprint 6 with M4 (Tor spike) + M5 (Matrix outbound bridge) combined as a single Flowstate sprint. This is ~2.5x normal DS sprint LOC (2,652 vs ~1,100 avg). Tests whether the 3-phase structure holds under combined milestone pressure.

### Metrics

| Metric | DS S6 (Exp 4) | DS Flowstate Avg (S0-S4) | DS S5 Baseline (no-Flowstate) |
|--------|--------------|-------------------------|-------------------------------|
| LOC added | 2,652 | 1,722 avg | 1,338 |
| Tests added | 48 | 20 avg | 19 |
| Tests total | 212 | — | 164 |
| Gates first pass | yes | 3/5 first pass | yes |
| Commits | 2 | — | — |
| Token/timing | null (no collect.sh) | — | — |

Note: Token and timing metrics are null because DS does not yet have a collect.sh. This is a known gap flagged in the sprint retro.

### Hypothesis Results

| # | Hypothesis | Result | Evidence |
|---|-----------|--------|----------|
| H1 | 3-phase works under combined scope | Confirmed | M4+M5 delivered cleanly. Think->Execute->Ship held. Wave-based execution grouped transport concerns efficiently. |
| H5 | Gates catch real issues | Confirmed | 212 tests + 0 clippy validated 2,652 LOC on first attempt. |
| H7 | Skills are followed | Partially confirmed (self-assessed) | 8/10 skill instructions followed. Missing: dedicated security audit wave, some adversarial scenarios. |

### Scope Stress Verdict

The 3-phase structure held at ~2.5x normal scope. Two milestones in one sprint worked because M4 and M5 share transport abstraction concerns — the agent correctly grouped them. This partially counters Exp 1's finding that 3-phase adds overhead: for multi-module work, the planning phase prevents wrong turns.

However, token metrics are unavailable, so we cannot compare efficiency. The structure held but we can't measure the cost.

---

## Experiment 3: Blind Compliance Scoring (folded into Exp 4)

### Protocol

After DS S6 completed, gave the code artifacts (diff, gate log, source files, skill files) to a fresh agent with NO knowledge of Flowstate. The agent scored 5 dimensions (1-5 each) purely on output quality.

The blind judge was explicitly told not to read any retro, metrics, or import files — only code and artifacts.

### Blind Scores vs Self-Assessment

| Dimension | Blind Score | Self-Reported | Notes |
|-----------|------------|---------------|-------|
| Scope delivery | 4/5 | H1 confirmed | Aligned — both say scope was delivered |
| Test quality | 4/5 | H5 confirmed | Aligned — both say tests are solid |
| Code quality | 3/5 | — | New dimension — sprint retro doesn't score this |
| Convention compliance | 3/5 | H7 partially confirmed | Aligned on partial compliance |
| Diff hygiene | 4/5 | — | New dimension — sprint retro doesn't score this |
| **Overall** | **18/25 (72%)** | | |

### Comparison to Exp 1 Baselines

| Sprint | Blind Score | Method |
|--------|------------|--------|
| DS S5 (no Flowstate) | 22/25 (88%) | Exp 1 blind review |
| DS S6 (Flowstate, 2.5x scope) | 18/25 (72%) | Exp 3 blind review |

DS S6 scored lower than the no-Flowstate baseline, but at 2.5x the scope. Not directly comparable — larger sprints have more surface area for issues.

### What the Blind Judge Found That the Sprint Agent Missed

**Code-level violations invisible to process-level auditing:**

1. **`validate_hs_token` uses string `!=`, not constant-time comparison** — directly violates the security-auditor skill's explicit instruction for constant-time auth tag comparisons. The sprint agent's H7 audit noted "no unwrap on network data" (true) but missed the timing attack vector.

2. **Bridge binds to `0.0.0.0` by default** — a privacy application binding to all interfaces is a security concern. Neither the sprint agent nor the H7 audit flagged this.

3. **No cancellation safety docs on async functions** — the architect skill requires this. The sprint agent noted "async patterns with timeouts: YES" but didn't check for the documentation requirement.

4. **`GhostUserManager::hash_peer` uses djb2** (non-cryptographic hash) — in a privacy tool, peer-to-ghost-user mapping should use a cryptographic hash. Not caught by any audit.

5. **All types are `pub` instead of `pub(crate)`** — the architect skill says `pub(crate)` by default. Not flagged.

6. **`#[allow(dead_code)]` without justification comment** — violates production-engineer skill.

### Root Cause

The H7 audit checks *process compliance* ("did the agent run a security review?", "were Gherkin scenarios written?") but not *code compliance* ("does the code actually follow the security-auditor skill's specific instructions?"). The sprint agent treated H7 as a checklist of activities performed, not a code review against skill requirements.

### Falsification Verdict

**H7 remains partially confirmed, but the audit methodology is insufficient.** The sprint agent's self-assessment was honest (it correctly rated H7 as partial) but shallow. A process-level checklist misses code-level violations that a blind reviewer catches by reading the actual source.

---

## Combined Takeaways

1. **Exp 4 (scope stress)**: 3-phase holds at 2.5x scope. The planning phase adds value for multi-module work (countering Exp 1's finding). Missing: token metrics to measure cost.

2. **Exp 3 (blind scoring)**: Self-assessed H7 is not inflated but is shallow. Process compliance != code compliance. The H7 audit methodology needs to include actual code review against specific skill instructions, not just activity verification.

3. **Actionable change**: The H7 audit instruction in the sprint template should require the agent to read new/modified source files and grep for specific patterns from each skill's requirements, not just check whether activities occurred.
