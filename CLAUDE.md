# Flowstate — Project Instructions

A sprint-based development workflow for Claude Code. This repo contains the workflow files (templates, skills, tools) that get copied into target projects.

## Repo Structure

- `PRD.md` — workflow reference (what Flowstate is, how it works)
- `RESULTS.md` — sprint log template
- `sprints.json` — sprint metrics (single source of truth)
- `skills/` — planning skills (PM, UX, Architect, Prod Eng, Security). Copy to `.claude/skills/` in target projects.
- `tier-1/`, `tier-2/`, `tier-3/` — sprint templates for different environments
- `tools/import_sprint.py` — import sprint metrics into sprints.json
- `tools/mcp_server.py` — MCP server for collecting metrics from session logs
- `tools/init.py` — bootstrap script for new projects
- `imports/` — archive of imported sprint JSON files
- `dashboard/` — optional static Next.js dashboard over sprints.json

## File Layout (Target Projects)

- Flowstate workflow files live at `~/.flowstate/{project-slug}/`, not in the target repo
- Skills go in `.claude/skills/` in the target project (Claude Code auto-loads them)
- `collect.sh` runs FROM the project directory (auto-detects project from cwd)
- Sprint templates use `{FLOWSTATE}` as a placeholder for `~/.flowstate/{project-slug}`
- Each project should have a `docs/ROADMAP.md` breaking milestones into sprint-sized phases

## Sprint Workflow

- Phase 1+2 combined (no human break). Only Phase 3 has a checkpoint.
- Phase 3 proposes skill changes but does NOT apply them. Human reviews after the session.
- After a sprint, import metrics: `python3 tools/import_sprint.py --from <import-json>`
- One sprint per session. Multi-sprint sessions contaminate metrics.

## Conventions

- Active session time, not wall time
- Sprint files are copy-paste prompts
- No manual tracking — everything automated or estimated by the agent
- No emojis unless explicitly requested
- Use new-work tokens/LOC (not total tokens/LOC) for efficiency comparisons
