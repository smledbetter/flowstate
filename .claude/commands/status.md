Show the current status of a Flowstate project.

If an argument is provided ($ARGUMENTS), use it as the project slug or path. Otherwise, check if the current working directory has a `~/.flowstate/` counterpart (derive slug from cwd).

Read and summarize these files (skip any that don't exist):
1. `~/.flowstate/{slug}/progress.md` — what happened last, what's next
2. `docs/ROADMAP.md` (in the project repo) — current phase, overall milestone status
3. The most recent baseline in `~/.flowstate/{slug}/metrics/` — test count, coverage, gate status
4. The most recent retrospective in `~/.flowstate/{slug}/retrospectives/` — last sprint's results

Present a concise summary:
- Project name and slug
- Last sprint completed (number, phase, date if available)
- Current state (tests, coverage, stability)
- Next up (which phase, what it builds)
- Any blocked items or open issues from progress.md
