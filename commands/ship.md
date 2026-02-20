Run Phase 3: SHIP for the sprint you just completed.

Auto-detect the sprint number:
- Check git log for the most recent "sprint N:" commit, or
- List files in `~/.flowstate/{SLUG}/metrics/` to find the sprint number from gate logs or baseline files

Then follow every step in CLAUDE.md's "Phase 3: SHIP" section:
1. Collect metrics via MCP tools (sprint_boundary, list_sessions, collect_metrics)
2. Write import JSON (validated via dry_run)
3. Write retrospective with H7 audit, hypothesis table, change proposals
4. Commit sprint code
5. Write next baseline
6. Update roadmap
7. Write progress.md
8. Run completion check — fix any MISSING items

Print the completion checklist when done.
