# Flowstate — Project Instructions

This is a meta-project: a sprint-based development workflow system, not a codebase. It produces markdown files and shell scripts that are copied into other projects.

## How This Repo Works

- `PRD.md` is the system definition. `RESULTS.md` is the experiment data. Don't duplicate between them.
- `skills/` contains generic, language-agnostic skill files. When bootstrapping a new project, copy and adapt these.
- `tier-1/`, `tier-2/`, `tier-3/` contain sprint templates for different environments. See PRD section 9.
- `tools/` contains pipeline scripts: `import_sprint.py`, `generate_tables.py`, `extract_metrics.py`.
- `imports/` receives import JSON archives and sanitized exports from Tier 2 sprints.
- `hypotheses.json` is the canonical hypothesis registry (IDs, names, valid results).
- `temp/` holds prompts and scratch files for ongoing work. Not permanent.

## Test Projects

- **Uluka** (`/Users/stevo/Sites/Uluka`): TypeScript CLI tool. Flowstate has been running sprints here since Sprint 0.
- **Dappled Shade** (`/Users/stevo/Sites/Dappled Shade`): Rust P2P encrypted messaging. Second test project.

## File Layout

- Flowstate workflow files (sprints, metrics, retros, config) live at `~/.flowstate/{project-slug}/`, not in target repos.
- Skills stay at `.claude/skills/` in the project repo (Claude Code requirement) but are gitignored.
- `collect.sh` must be run FROM the project directory (it auto-detects the project from cwd).
- Sprint templates use `{FLOWSTATE}` as a placeholder for `~/.flowstate/{project-slug}`.
- Each project should have a `docs/ROADMAP.md` that breaks PRD milestones into sprint-sized phases. Created during bootstrap (Phase B).

## Sprint Workflow

- Project agents run sprints autonomously. Human pastes Phase 1+2, then Phase 3 — agent does the rest.
- Phase 3 proposes skill changes but does NOT apply them. Human reviews retro after the session ends.
- Phase 3 also writes the next sprint's baseline and updates docs/ROADMAP.md.
- After a sprint, import metrics: `python3 tools/import_sprint.py --from ~/.flowstate/{slug}/metrics/sprint-N-import.json`
- Then regenerate tables: `python3 tools/generate_tables.py <command>` and paste into RESULTS.md.

## Conventions

- Active session time, not "wall time" — see PRD section 4.7 for metric definitions
- Hypotheses capped at H12 — re-test existing, don't add new ones
- Sprint files are copy-paste prompts. Phase 1+2 combined (no human break). Only Phase 3 has a checkpoint.
- collect.sh auto-detects project from cwd. No hardcoded paths.
- No manual tracking of any kind. Everything automated or estimated by the agent.
- One sprint per session. Multi-sprint sessions contaminate metrics (active time, token counts blend).
- No emojis unless the user explicitly asks.
- When updating RESULTS.md, use new-work tokens/LOC (not total tokens/LOC) for efficiency comparisons.

## Memory

Cross-session state lives in `~/.claude/projects/-Users-stevo-Sites-Flowstate/memory/`. MEMORY.md is loaded automatically. Check `pending.md` at session start for open threads.
