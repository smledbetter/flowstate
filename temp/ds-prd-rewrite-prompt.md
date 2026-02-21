You are running a Flowstate consensus review to update the Dappled Shade PRD.

Load all 5 skill files in .claude/skills/

Read these files:
- PRD.md
- docs/ROADMAP.md

## Context: Sprint History (S0-S5)

No retrospective files exist on disk. Here is the accumulated evidence from 6 sprints:

**DS S0 (M0 MVP):** Built terminal P2P chat over TCP with Noise encryption, 3268 LOC, 57 tests. arti used only as a `.onion` stub — never tested on real Tor network. Clippy caught 3 real bugs (manual_div_ceil, async_fn_in_trait, .expect() on network data). 14 subagents across 7 waves.

**DS S1 (M1 dapple-olm):** Added Olm per-message E2EE on top of Noise. vodozemac integration was clean. Direct TCP transport verified between two physical machines. 1135 LOC, 75 tests.

**DS S2 (M2 Phase 1: Relay Protocol):** Built ephemeral relay service with store-and-forward. Clippy caught `or_insert_with` -> `or_default`. 2114 LOC, 114 tests. Self-contained module — no dependencies on crypto stack, which made it cheaper to build.

**DS S3 (M2 Phase 2: Relay Integration):** Integrated relay with existing two-peer architecture. 737 LOC, 122 tests. All gates passed first try.

**DS S4 (M3 Phase 1: Gossip Protocol):** Built multi-hop message routing with peer list, TTL, origin signing. 1357 LOC, 145 tests. Skill compliance dropped to 2/5 — threat model and crypto constraint instructions not followed.

**DS S5 (M3 Phase 2: Mesh Resilience — NO FLOWSTATE BASELINE):** Ran without Flowstate as a falsification experiment. 1338 LOC, 164 tests, 6m 19s active time (vs 28m avg with Flowstate). Blind quality review: 22/25 (88%). Found dead code: `process_message_resilient()` delegates to `process_message` with no added logic.

**Key finding across all sprints:** arti onion services have NEVER been tested on a real Tor network. All Tor-related code uses mocks or stubs. The PRD already reflects this (M4 is the arti validation milestone), but milestone scoping downstream of M4 should account for the possibility that arti doesn't work and an alternative is needed.

**Current state:** M0-M1 shipped and verified. M2 (relay) shipped. M3 (gossip) shipped including baseline. Codebase: ~8800 LOC Rust, 164 tests. Next unstarted work is M4 (Tor validation).

## Your Task

Acting as a consensus agent with PM, UX, and Architect perspectives:

1. Review milestones 2-5 and Track B (Android) in the PRD against the sprint history above. Specifically consider:
   - M2 and M3 are already shipped — mark them done, don't propose changes
   - M4 (arti validation) is the critical risk gate — is the go/no-go structure right?
   - M5 (Matrix bridge) has significant open risks listed in the PRD — are they still the right risks?
   - Track B (Android) — is the dependency chain realistic? Should any Track A work complete first?
   - The no-Flowstate baseline (S5) showed a single agent completing M3 Phase 2 in 6 minutes. For Experiment 4, we need an **oversized milestone** — one that is clearly too large for a single sprint, requiring either parallelism or multi-sprint delivery. Does the current roadmap have one, or should we construct one?

2. For each unshipped milestone (M4, M5, B1, B2, B3, R1), recommend one of:
   - KEEP as-is (with justification)
   - REVISE (show the before/after diff)
   - REPLACE (describe the new milestone and why)
   - REORDER (move it, explain the dependency change)
   - MERGE (combine with another milestone, explain why)

3. PM perspective: does the milestone sequence deliver usable value incrementally? Can a user do something new at each boundary?
4. UX perspective: is there a usable product at each milestone? What's the first milestone where someone other than the developer could use it?
5. Architect perspective: are the technical dependencies realistic given what we now know? Are there milestones that are too large or too small?

6. **Experiment 4 milestone:** Explicitly identify or construct one milestone that would be a good scope stress test — large enough that a single agent in a single session would struggle. This should be a real milestone (not artificial), ideally combining multiple subsystems.

Do NOT modify M0-M3. They are shipped.

Output the proposed changes as diffs against PRD.md. Do not apply them — I will review first.
