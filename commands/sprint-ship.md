Run Phase 3 (SHIP) for the current sprint.

$ARGUMENTS contains the sprint number and any notes from the implementation phase.

Orient yourself by reading:
- `~/.flowstate/{SLUG}/flowstate.config.md`
- `~/.flowstate/{SLUG}/metrics/` (find the current sprint number from the highest baseline file)
- `~/.flowstate/{SLUG}/metrics/sprint-N-gates.log` (gate results from this sprint)
- `docs/ROADMAP.md` (this sprint's phase)

Then execute every step in the "Phase 3: SHIP" section of `.claude/skills/flowstate/SKILL.md`.

Before writing the next baseline, review `docs/ROADMAP.md` against what this sprint revealed:
- Should adjacent phases merge (too small) or split (too large)?
- Should any later phase move earlier (blocker discovered) or later (less critical)?
- Did this sprint surface a prerequisite that a future phase assumes exists but doesn't?
Apply roadmap changes if needed, or note "Roadmap reviewed — no changes" in the retro.
