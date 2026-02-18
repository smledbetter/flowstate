# Flowstate — Project Instructions

This is a meta-project: a sprint-based development workflow system, not a codebase. It produces markdown files and shell scripts that are copied into other projects.

## How This Repo Works

- `PRD.md` is the system definition. `RESULTS.md` is the experiment data. Don't duplicate between them.
- `skills/` contains generic, language-agnostic skill files. When bootstrapping a new project, copy and adapt these.
- `tier-1/`, `tier-2/`, `tier-3/` contain sprint templates for different environments. See PRD section 9.
- `imports/` receives sanitized exports from Tier 2 sprints on restricted machines.
- `temp/` holds prompts and scratch files for ongoing work. Not permanent.

## Test Projects

- **Uluka** (`/Users/stevo/Sites/Uluka`): TypeScript CLI tool. Flowstate has been running sprints here since Sprint 0.
- **Dappled Shade** (`/Users/stevo/Sites/Dappled Shade`): Rust P2P encrypted messaging. Second test project.

## Conventions

- Active session time, not "wall time" — see PRD section 4.7 for metric definitions
- Hypotheses capped at H12 — re-test existing, don't add new ones
- Sprint files are copy-paste prompts. Phase 1+2 combined (no human break). Only Phase 3 has a checkpoint.
- collect.sh auto-detects project from cwd. No hardcoded paths.
- No manual tracking of any kind. Everything automated or estimated by the agent.
- No emojis unless the user explicitly asks.
- When updating RESULTS.md, use new-work tokens/LOC (not total tokens/LOC) for efficiency comparisons.

## Memory

Cross-session state lives in `~/.claude/projects/-Users-stevo-Sites-Flowstate/memory/`. MEMORY.md is loaded automatically. Check `pending.md` at session start for open threads.
