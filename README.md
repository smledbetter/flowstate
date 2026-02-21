# Flowstate

A sprint-based development workflow for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Gates for quality. Structure for scope. Metrics for tracking.

## What You Get

- **Quality gates**: Automated checks (tests, types, lint) that run after every sprint. Pass or fix -- no judgment calls.
- **Sprint templates**: Copy-paste prompts that give Claude Code a three-phase workflow (Think, Execute, Ship).
- **Planning skills**: PM, UX, and Architect perspectives for roadmap conversations between sprints.
- **Metrics pipeline**: Token usage, session time, test counts, and coverage tracked in `sprints.json`.

## Quick Start

### 1. Clone and set up your project workspace

```bash
git clone https://github.com/smledbetter/flowstate.git

mkdir -p ~/.flowstate/my-project/metrics
mkdir -p ~/.flowstate/my-project/retrospectives
```

### 2. Copy planning skills into your project

```bash
cp flowstate/skills/product-manager.md your-project/.claude/skills/
cp flowstate/skills/ux-designer.md your-project/.claude/skills/
cp flowstate/skills/architect.md your-project/.claude/skills/
```

### 3. Configure your gates

Create `~/.flowstate/my-project/flowstate.config.md`:

```markdown
## Quality Gates
- test_command: npm test
- type_check: npx tsc --noEmit
- lint: npx eslint .
- coverage_command: npm test -- --coverage
- coverage_threshold: 65
```

### 4. Write a baseline and run your first sprint

Record your starting state (SHA, test count, coverage), then paste the sprint prompt from `tier-1/sprint.md` into a fresh Claude Code session.

See [PRD.md](PRD.md) for the full workflow reference.

## Repo Structure

```
skills/              Planning skills (PM, UX, Architect, Prod Eng, Security)
tier-1/              Sprint template + config for standard environments
tier-2/              Sprint template for restricted environments
tier-3/              Minimal sprint template
tools/
  import_sprint.py   Import sprint metrics into sprints.json
  mcp_server.py      MCP server for collecting metrics from session logs
  init.py            Bootstrap script for new projects
sprints.json         Sprint metrics (ships with example data, cleared on first import)
PRD.md               Workflow reference
RESULTS.md           Sprint log template
dashboard/           Optional static dashboard for visualizing sprint data
```

## Collecting Metrics

**Option A: MCP server** (recommended)

The MCP server at `tools/mcp_server.py` reads Claude Code session logs directly. At the end of a sprint, run `/import` to collect and import metrics automatically.

**Option B: Shell script**

Run `tier-1/collect.sh` from your project directory. It auto-detects the project and writes the import JSON.

Either way, import with:

```bash
python3 tools/import_sprint.py --from ~/.flowstate/my-project/metrics/sprint-1-import.json
```

## Research

Flowstate was developed over 19 sprints across three projects with four falsification experiments. The complete research data is on the [`archive/v1-research`](https://github.com/smledbetter/flowstate/tree/archive/v1-research) branch.

Key findings:
- Gates catch real bugs (3/3 planted bugs caught in adversarial testing)
- Sprint structure prevents scope drift on complex work
- Skills are optional for implementation, useful for planning
- Single-agent beats multi-agent on moderate codebases
