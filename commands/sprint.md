You are running a Flowstate sprint. Follow the Phase 1+2 workflow in CLAUDE.md exactly.

First, auto-detect the sprint number and phase:

1. Read `docs/ROADMAP.md` — find the first phase NOT marked done. That's this sprint's phase.
2. List files in `~/.flowstate/{SLUG}/metrics/` — find the highest-numbered `baseline-sprint-N.md`. N is your sprint number.
3. If no roadmap exists, this is Sprint 0. Follow the Sprint 0 instructions in CLAUDE.md.

Then read all required files listed in CLAUDE.md's "Phase 1+2" section (PRD, roadmap, baseline, progress, config, last retro, skills, hypotheses.json).

Execute Phase 1+2 as documented. When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."

Do NOT proceed to Phase 3 without human approval.
