# Tier 2 Setup Guide

Step-by-step instructions for starting a Flowstate Tier 2 project on a work laptop.

**What Tier 2 gives you**: full sprint structure, 5 skill perspectives, quality gates, hypothesis tracking, retrospectives. Metrics are agent-estimated (no automated collection). Each sprint produces a sanitized export you bring back to your personal Flowstate repo.

**What stays on the work laptop**: all project code, full retrospectives, skill files, baselines, gate logs. Nothing proprietary leaves unless you put it in the sanitized export (which you review before copying).

## Prerequisites

- Claude Code installed on the work laptop
- Python 3 available
- Git available
- The Flowstate repo cloned somewhere on the work laptop (e.g., `~/Flowstate`)

## Steps

### 1. Clone Flowstate

```bash
git clone <your-flowstate-repo-url> ~/Flowstate
```

The Flowstate repo contains only markdown, shell scripts, and Python tooling -- no proprietary code.

### 2. Create your project repo

```bash
mkdir ~/Projects/my-project
cd ~/Projects/my-project
git init
```

Or clone an existing repo you'll be working on.

### 3. Write PRD.md

Create `PRD.md` in the project root. This is the product requirements document -- describe what you're building, the tech stack, and milestones. At minimum:

```markdown
# My Project

One-line description.

## Tech Stack

- Language (e.g., Python 3.12, TypeScript, Rust, Go)
- Key frameworks or libraries

## Milestones

### M1: [First milestone name]
- Requirement 1
- Requirement 2

### M2: [Second milestone name]
- ...
```

The init script uses the Tech Stack section to auto-detect your language and configure gates.

### 4. Run init

```bash
cd ~/Projects/my-project
python3 ~/Flowstate/tools/init.py --tier 2
```

This creates:
- `~/.flowstate/{slug}/flowstate.config.md` -- quality gate commands
- `~/.flowstate/{slug}/metrics/` -- baselines and gate logs go here
- `~/.flowstate/{slug}/retrospectives/` -- sprint retros go here
- `~/.flowstate/hypotheses.json` -- shared hypothesis registry
- `.claude/skills/` -- 5 generic skill files (PM, UX, Architect, Production Engineer, Security Auditor)
- `CLAUDE.md` -- sprint workflow instructions the agent reads every session
- `.claude/settings.json` -- LLM-as-judge Stop hook

### 5. Add .gitignore entries

```bash
echo '.claude/skills/' >> .gitignore
```

Skills are copied from Flowstate and adapted per project -- they shouldn't be committed to the project repo.

### 6. Review what was generated

Open `CLAUDE.md` and `~/.flowstate/{slug}/flowstate.config.md`. Check that:
- Gate commands match your toolchain (init infers them from the PRD, but may guess wrong)
- The project name and description look right

If gates need fixing, edit them now or let Sprint 0 discover and fix them.

### 7. Start Sprint 0

Open a fresh Claude Code session in your project directory and say:

```
start the next sprint
```

The agent reads `CLAUDE.md`, sees no roadmap exists, and runs Sprint 0:
- Verifies gate commands work
- Creates `docs/ROADMAP.md` (milestones broken into sprint-sized phases)
- Fills in language conventions in `CLAUDE.md`
- Writes the initial baseline for Sprint 1
- Writes a retrospective and sanitized export

### 8. Review Sprint 0 output

After the agent finishes:

1. Read `~/.flowstate/{slug}/retrospectives/sprint-0.md` -- approve or reject any change proposals
2. Read the sanitized export the agent produced -- redact anything you're not comfortable sharing
3. Copy the sanitized export to your personal Flowstate repo: `imports/{codename}-sprint-0.md`

### 9. Run Sprint 1

Open a **fresh** Claude Code session (one sprint per session) and say:

```
start the next sprint
```

The agent reads the roadmap, finds the first undone phase, reads the baseline, and runs the sprint autonomously.

## Ongoing workflow

Each sprint follows the same pattern:

1. Fresh session, say "start the next sprint"
2. Agent plans, executes, runs gates
3. When gates pass, paste the Phase 3 prompt (or the agent will prompt you)
4. Agent writes retro + sanitized export
5. You review the retro, approve/reject skill changes, bring the sanitized export home

## Bringing data back to Flowstate

On your personal machine:

```bash
cd ~/Sites/Flowstate
# Paste the sanitized export into imports/
cp /path/to/sanitized-export.md imports/{codename}-sprint-N.md
```

The sanitized export contains only: sprint number, language, generalized scope, estimated metrics, hypothesis results, and generalized skill proposals. No proprietary code, no file paths, no business logic.
