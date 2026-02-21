# DS Sprint 6: M4 + M5 Combined (Experiment 4: Scope Stress Test)

> Paste into a fresh Claude Code session in `~/Sites/Dappled Shade/`.
> This is TWO milestones in one sprint — deliberately oversized.

---

## Phase 1 + 2: THINK then EXECUTE

```
You are running a Flowstate sprint for Dappled Shade — Sprint 6.

THIS IS EXPERIMENT 4: SCOPE STRESS TEST.
This sprint combines M4 (Tor validation) AND M5 (Matrix bridge) into a single sprint.
This is deliberately oversized — approximately 3x normal DS sprint scope.
The experiment tests whether Flowstate's structure handles oversized scope better than a single-agent approach.
Record any moments where scope feels unmanageable, context gets heavy, or you need to cut corners.

BOOTSTRAP: The ~/.flowstate/dappled-shade/ directory does not exist.
Create it now with this structure:
  ~/.flowstate/dappled-shade/
  ~/.flowstate/dappled-shade/metrics/
  ~/.flowstate/dappled-shade/retrospectives/

Read these files:
- PRD.md
- docs/ROADMAP.md (M4 and M5 phases)
- All skill files in .claude/skills/
- ~/.flowstate/hypotheses.json (if exists — canonical hypothesis IDs)

PHASE 1 — THINK:
Acting as a consensus agent with all 5 skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor):

0. FEASIBILITY CHECK (do this BEFORE planning):
   M4 dependencies:
   - arti crate: verify current version, check if onion service API exists
   - Run a minimal spike: can arti bootstrap and create an onion service in code? (compile check, not live Tor)
   - If the API doesn't exist or won't compile, the M4 scope pivots to the no-go path immediately

   M5 dependencies:
   - ruma crate: verify current version, check appservice types exist
   - axum: verify compatibility with ruma
   - Can you construct a minimal Matrix appservice registration + event handler? (compile check)
   - If ruma appservice types are missing or broken, flag and propose fallback

   Confirm cargo fmt and cargo clippy are available as gates.

1. Produce acceptance criteria (Gherkin format) for BOTH milestones:
   M4: Tor validation spike + integration (or transport hardening if no-go)
   M5: Matrix appservice outbound + inbound bidirectional bridge

   Every requirement must have at least one happy-path and one failure/edge-case scenario.

2. Produce an implementation plan with wave-based execution:
   - M4 and M5 touch completely different subsystems — they CAN be parallelized
   - M4 Phase 1 (spike) should run FIRST since it has a go/no-go gate that affects M4 Phase 2
   - M5 work can start in parallel with M4 Phase 1
   - Group tasks into waves by file dependency
   - For each task: files read, files written, agent model

   Suggested wave structure (adjust based on feasibility check):
   Wave 1: M4 Phase 1 spike (arti bootstrap) + M5 Phase 1 (ruma appservice scaffold) — parallel
   Wave 2: M4 go/no-go decision point. M5 outbound messaging continues.
   Wave 3: M4 Phase 2 (whichever path) + M5 Phase 2 (inbound routing) — parallel
   Wave 4: Integration tests, security audit, cross-subsystem verification

PHASE 2 — EXECUTE:
Immediately after producing the plan, execute it. Do NOT wait for human approval.

- Spawn subagents per wave as specified
- Each subagent gets: file path references (not content), task scope, relevant skill context
- Commit atomically after each wave
- Do NOT read full implementation files into orchestrator context — delegate to subagents
- After all waves complete, run quality gates IN ORDER:

Gate 1: cargo build
Gate 2: cargo clippy -- -D warnings
Gate 3: cargo fmt --check
Gate 4: cargo test
Gate 5 (optional): bash ~/Sites/Flowstate/tools/deps_check.sh
Gate 6 (optional): bash ~/Sites/Flowstate/tools/sast_check.sh

Save gate output to ~/.flowstate/dappled-shade/metrics/sprint-6-gates.log

If any gate fails:
- Fix the issue, re-run that gate, max 3 cycles
- If still failing after 3 cycles, stop and report

When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."
```

## Phase 3: SHIP

```
Run the Phase 3 retrospective for Sprint 6.

THIS IS EXPERIMENT 4. In addition to normal retro items, record:
- Total scope delivered vs planned (did you have to cut anything?)
- Where did context pressure appear? (wave number, task count at that point)
- Did parallelism between M4 and M5 actually help, or did the orchestrator struggle to track both?
- Correction depth: how many gate retry cycles per gate?
- Would this sprint have been better as 2 separate sprints? Why or why not?

1. Collect metrics (run from project directory):
   Find boundary: git log --format='%aI %s' | head -5
   bash ~/.flowstate/dappled-shade/metrics/collect.sh --after <BOUNDARY> <SESSION_ID>
   Save to ~/.flowstate/dappled-shade/metrics/sprint-6-report.txt
   JSON: bash ~/.flowstate/dappled-shade/metrics/collect.sh --json --after <BOUNDARY> <SESSION_ID>
   Save to ~/.flowstate/dappled-shade/metrics/sprint-6-report.json

2. Write import JSON at ~/.flowstate/dappled-shade/metrics/sprint-6-import.json:
   {
     "project": "dappled-shade",
     "sprint": 6,
     "label": "DS S6",
     "phase": "M4 + M5: Tor Validation + Matrix Bridge (EXPERIMENT 4: SCOPE STRESS)",
     "experiment": "exp4_scope_stress",
     "metrics": {
       ...from report.json...
       "tests_total": <current>,
       "tests_added": <added>,
       "coverage_pct": null,
       "lint_errors": 0,
       "gates_first_pass": <true|false>,
       "gates_first_pass_note": "<details>",
       "loc_added": <from git diff --stat>,
       "loc_added_approx": false,
       "task_type": "feature",
       "scope_cut": "<list anything cut from original plan, or null>",
       "context_pressure_notes": "<where context got heavy>"
     },
     "hypotheses": [
       {"id": "H1", "name": "3-phase sprint works across project types", "result": "...", "evidence": "..."},
       {"id": "H4", "name": "Wave parallelism helps", "result": "...", "evidence": "Specifically: did M4/M5 parallelism save time vs sequential?"},
       {"id": "H5", "name": "Gates catch real issues", "result": "...", "evidence": "..."},
       {"id": "H7", "name": "Skills are followed by agents", "result": "...", "evidence": "..."}
     ],
     "quality_review": null
   }
   Validate: python3 ~/Sites/Flowstate/tools/import_sprint.py --from --dry-run ~/.flowstate/dappled-shade/metrics/sprint-6-import.json

3. Write retrospective at ~/.flowstate/dappled-shade/retrospectives/sprint-6.md:
   - What was built (both milestones)
   - Metrics comparison vs DS S4 and S5 (last Flowstate and baseline sprints)
   - Experiment 4 analysis: scope stress findings
   - H7 audit: check these 5 instructions:
     1. PM: every story has happy path + edge case (Gherkin)
     2. Architect: cheapest appropriate model per task
     3. Security: Zeroizing on all key material
     4. ProdEng: tests written before or alongside implementation
     5. Security: no .unwrap() on network/external data
   - Hypothesis results table
   - Change proposals (diffs)

4. Do NOT apply skill changes.
   Commit: git add -A && git commit -m "sprint 6: M4 tor validation + M5 matrix bridge (experiment 4)"

5. Write baseline at ~/.flowstate/dappled-shade/metrics/baseline-sprint-7.md

6. Update docs/ROADMAP.md: mark M4 and M5 phases done, update Current State

7. Write ~/.flowstate/dappled-shade/progress.md

8. Completion check — print with [x] or [MISSING]:
   [ ] metrics/sprint-6-report.txt
   [ ] metrics/sprint-6-report.json
   [ ] metrics/sprint-6-import.json
   [ ] retrospectives/sprint-6.md (hypothesis table + experiment 4 analysis + change proposals)
   [ ] metrics/baseline-sprint-7.md
   [ ] progress.md
   [ ] docs/ROADMAP.md updated
   [ ] Code committed
```

## Post-Sprint (you do this in Flowstate repo)

1. Review retro at ~/.flowstate/dappled-shade/retrospectives/sprint-6.md
2. Blind quality scoring (Experiment 3 folded in):
   - Open a fresh Claude session, paste the sprint diff, ask for 5-dimension blind review
   - Compare against DS S5 baseline (88%) and self-assessed score
3. Import: python3 tools/import_sprint.py --from ~/.flowstate/dappled-shade/metrics/sprint-6-import.json
4. Regenerate tables, update RESULTS.md
