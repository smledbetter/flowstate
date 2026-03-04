# Sprint Template

> Tier 1 sprint: full Claude Code with bash, automated metrics.
> The sprint workflow auto-loads from `.claude/skills/flowstate/SKILL.md`.

---

## Usage

Start a fresh session. Say:

```
go
```

The agent reads SKILL.md, determines the sprint number and scope from the roadmap and baseline, and starts. It will:
1. Run Phase 1+2 (Think + Execute) until gates pass
2. Auto-run Phase 3 (Ship) — retro, metrics, baseline, progress
3. Check the roadmap for the next phase
4. Start the next sprint, or stop if the roadmap is complete

The agent pauses only when:
- Sprint 0 completes (roadmap review before building)
- A retro contains change proposals that need human review
- A feasibility check fails and needs a human decision
- 5+ pending decisions have accumulated, or one is marked `[BLOCKING]`
- Gates fail after 3 fix cycles
- The roadmap is complete

## Post-Session

1. Review retrospectives at `{FLOWSTATE}/retrospectives/`
2. Import metrics: `/import` (or `python3 tools/import_sprint.py --from {FLOWSTATE}/metrics/sprint-N-import.json`)
3. Optional: run mutation testing as a diagnostic: `bash "${FLOWSTATE_REPO:-$HOME/Sites/Flowstate}"/tools/mutation_check.sh`

### Human Time

Tracked automatically by the MCP `collect_metrics` tool — it detects gaps >60s between entries in the session log and excludes them from active session time. No manual logging needed.
