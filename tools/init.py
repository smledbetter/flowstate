#!/usr/bin/env python3
"""Bootstrap a new Flowstate project from a PRD.

Usage:
    cd /path/to/new-project    # PRD.md must exist here
    python3 ~/Sites/Flowstate/tools/init.py [--tier 1|2]

Options:
    --tier 1    Full Claude Code with bash, automated metrics (default)
    --tier 2    Skills + structure, no automated metrics. Produces sanitized exports.

Reads PRD.md, infers project name, description, and language/stack.
Creates everything needed for Sprint 0 with zero prompts.

Creates:
    ~/.flowstate/{slug}/           (flowstate.config.md, metrics/, retrospectives/)
    ~/.flowstate/{slug}/metrics/collect.sh  (Tier 1 only, legacy — MCP tools preferred)
    ~/.flowstate/hypotheses.json   (shared registry, if not already present)
    .claude/skills/                (5 generic skill files)
    .claude/commands/              (slash commands: /sprint, /ship)
    CLAUDE.md                      (generated sprint workflow, tier-specific)
"""

import json
import os
import re
import shutil
import sys

FLOWSTATE_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOWSTATE_HOME = os.path.expanduser("~/.flowstate")

# Language -> default gate commands
GATE_PRESETS = {
    "rust": [
        "cargo build",
        "cargo clippy -- -D warnings",
        "cargo fmt --check",
        "cargo test",
    ],
    "typescript": [
        "npx tsc --noEmit",
        "npx tsc --noEmit --noUnusedLocals",
        "npx vitest --run",
        "npx vitest --run --coverage",
    ],
    "python": [
        "python3 -m py_compile src/**/*.py",
        "ruff check .",
        "pytest",
        "pytest --cov",
    ],
    "go": [
        "go build ./...",
        "golangci-lint run",
        "go test ./...",
        "go test -cover ./...",
    ],
}

# Keywords that indicate a language (checked case-insensitive)
LANGUAGE_KEYWORDS = {
    "rust": ["rust", "cargo", "tokio", "crate"],
    "typescript": ["typescript", "node.js", "vitest", "jest", "npx", "tsx"],
    "python": ["python", "pip", "pytest", "django", "flask", "fastapi"],
    "go": ["golang", "goroutine", "go module", "go build", "go test"],
}


# ---------------------------------------------------------------------------
# PRD parsing
# ---------------------------------------------------------------------------


def parse_prd(path):
    """Extract project name, description, and language from PRD.md.

    Returns dict with keys: name, description, language (or None).
    """
    with open(path) as f:
        content = f.read()
    lines = content.split("\n")

    # Name: first # heading, strip "PRD:" prefix
    name = None
    for line in lines:
        if line.startswith("# "):
            name = line[2:].strip()
            # Strip common prefixes
            for prefix in ["PRD:", "PRD -", "PRD --"]:
                if name.upper().startswith(prefix.upper()):
                    name = name[len(prefix) :].strip()
            # Strip trailing " -- subtitle" or " - subtitle"
            name = re.split(r"\s+[-—]+\s+", name)[0].strip()
            break

    if not name:
        name = os.path.basename(os.getcwd())

    # Description: first non-empty, non-heading paragraph
    description = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        description = stripped
        break

    if not description:
        description = name

    # Language detection: check tech stack section first, then first 50 lines
    language = detect_language(content)

    return {"name": name, "description": description, "language": language}


def detect_language(content):
    """Detect primary language from PRD content.

    Prioritizes a Tech Stack section if present, falls back to keyword scan.
    """
    lines = content.split("\n")

    # Try to find a Tech Stack section
    tech_section = ""
    in_tech = False
    for line in lines:
        if re.match(r"^#{1,3}\s+tech\s+stack", line, re.IGNORECASE):
            in_tech = True
            continue
        if in_tech:
            if line.startswith("#"):
                break
            tech_section += line + "\n"

    # Score each language by keyword hits
    search_text = tech_section if tech_section else "\n".join(lines[:50])
    search_lower = search_text.lower()

    scores = {}
    for lang, keywords in LANGUAGE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            score += len(re.findall(re.escape(kw.strip()), search_lower))
        if score > 0:
            scores[lang] = score

    if not scores:
        return None

    # If tech stack section had hits, use those; otherwise use first-50-lines hits
    if tech_section:
        tech_lower = tech_section.lower()
        tech_scores = {}
        for lang, keywords in LANGUAGE_KEYWORDS.items():
            score = 0
            for kw in keywords:
                score += len(re.findall(re.escape(kw.strip()), tech_lower))
            if score > 0:
                tech_scores[lang] = score
        if tech_scores:
            return max(tech_scores, key=tech_scores.get)

    return max(scores, key=scores.get)


def make_slug(name):
    """Convert project name to a slug (lowercase, hyphens, no special chars)."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def make_label_prefix(name):
    """Generate label prefix from project name initials.

    "Dappled Shade" -> "DS", "Uluka" -> "Uluka", "My Cool Project" -> "MCP"
    """
    words = name.split()
    if len(words) == 1:
        return name
    return "".join(w[0].upper() for w in words if w)


# ---------------------------------------------------------------------------
# Project settings (Claude Code hooks)
# ---------------------------------------------------------------------------


JUDGE_PROMPT = (
    "You are a sprint quality reviewer for a Flowstate sprint. "
    "Evaluate the assistant's last message and the conversation context.\\n\\n"
    "Score each dimension 1-5:\\n"
    "1. SCOPE: Did the work match the sprint phase scope? "
    "(no scope creep, no missing requirements)\\n"
    "2. TEST_QUALITY: Do tests verify real behavior, or are they mocking away "
    "the thing they should test?\\n"
    "3. GATE_INTEGRITY: Were quality gates run honestly? "
    "Any skipped, ignored, or worked-around?\\n"
    "4. CONVENTION_COMPLIANCE: Does the code follow project conventions "
    "and skill instructions?\\n"
    "5. DIFF_HYGIENE: Is the diff minimal and focused? "
    "No unnecessary reformatting, no dead code left behind?\\n\\n"
    "If ANY dimension scores 2 or below, respond with "
    '{"ok": false, "reason": "[dimension]: [specific issue]"}\\n'
    'If all dimensions are 3+, respond with {"ok": true}\\n\\n'
    "Context: $ARGUMENTS"
)


def generate_project_settings():
    """Generate .claude/settings.json with the LLM-as-judge Stop hook."""
    return json.dumps(
        {
            "hooks": {
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "prompt",
                                "prompt": JUDGE_PROMPT,
                                "timeout": 30,
                            }
                        ]
                    }
                ]
            }
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# Config template
# ---------------------------------------------------------------------------


def generate_config(gates, language):
    gate_lines = []
    labels = ["build/typecheck", "lint", "test", "coverage"]
    for i, cmd in enumerate(gates):
        label = labels[i] if i < len(labels) else f"gate_{i + 1}"
        gate_lines.append(f"- {label}: {cmd}")

    lang_note = (
        f"Language detected: {language}"
        if language
        else "Language: not detected -- update gates manually"
    )

    return f"""# Flowstate Configuration

## Quality Gates
{chr(10).join(gate_lines)}
- coverage_threshold: none (establish after Sprint 1)
- custom_gates: []

## Agent Strategy Defaults
- orchestrator_model: opus
- worker_model: sonnet
- mechanical_model: haiku
- orchestrator_context_target: 40%

## Sprint Settings
- commit_strategy: per-wave
- session_break_threshold: 50%

## Notes
- {lang_note}
- Gates may need adjustment after Sprint 0 discovers the actual toolchain
"""


# ---------------------------------------------------------------------------
# CLAUDE.md template
# ---------------------------------------------------------------------------


def generate_claude_md(name, description, slug, gates, label_prefix, language):
    gate_lines = "\n".join(f"  {i + 1}. `{cmd}`" for i, cmd in enumerate(gates))
    label_example = f'"{label_prefix} SN"'

    # Gate TODO marker if language wasn't detected
    gate_note = ""
    if not language:
        gate_note = "\n<!-- TODO: Gate commands are placeholders. Sprint 0 should verify and update these. -->"

    return f"""# {name}

{description}

## Flowstate Sprint Workflow

This project uses the Flowstate sprint process. When asked to "start the next sprint" or "run a sprint," follow this workflow.

### File Locations

- **Flowstate dir**: `~/.flowstate/{slug}/`
- **Config**: `~/.flowstate/{slug}/flowstate.config.md` (quality gates, agent strategy)
- **Baselines**: `~/.flowstate/{slug}/metrics/baseline-sprint-N.md`
- **Retrospectives**: `~/.flowstate/{slug}/retrospectives/sprint-N.md`
- **Metrics**: `~/.flowstate/{slug}/metrics/`
- **Metrics collection**: Use `mcp__flowstate__collect_metrics` MCP tool (or legacy `~/.flowstate/{slug}/metrics/collect.sh`)
- **Progress**: `~/.flowstate/{slug}/progress.md` (operational state for next session)
- **Roadmap**: `docs/ROADMAP.md` (in this repo -- create if missing)
- **Skills**: `.claude/skills/` (in this repo)

### How to Determine the Next Sprint

1. If no `docs/ROADMAP.md` exists, this is Sprint 0 (see below).
2. Read `docs/ROADMAP.md` -- find the first phase not marked done.
3. Find the highest-numbered baseline in `~/.flowstate/{slug}/metrics/` -- that's your sprint number.
4. Read that baseline for starting state, gate commands, and H7 audit instructions.

### Sprint 0: Project Setup (planning only -- no code)

Sprint 0 is a dedicated planning sprint. It produces the roadmap, baseline, and conventions that all future sprints depend on. No code is written. It still gets full metrics tracking.

**Phase 1+2: RESEARCH then PLAN**

Read these files:
- `PRD.md` (fully -- every section)
- `~/.flowstate/{slug}/flowstate.config.md`
- All files in `.claude/skills/`
- `~/.flowstate/hypotheses.json`

Then do ALL of the following:

1. **Verify gate commands.** Run each gate command below. If any don't work for this project (wrong tool, missing dependency), update them in this file AND in `~/.flowstate/{slug}/flowstate.config.md`. Record what works and what doesn't.
{gate_lines}{gate_note}

2. **Create `docs/ROADMAP.md`.**
   - Break PRD milestones into sprint-sized phases. Each phase = one sprint.
   - Right-sizing guide: a phase should be deliverable in 10-60 minutes of active agent time, produce 500-2500 LOC, and have a clear "done" state that gates can verify.
   - Phases that are mostly research or refactoring will be smaller. Phases that build new features from scratch will be larger.
   - Number phases starting from 1 (Sprint 0 is this planning sprint).
   - Include a "Current State" section at the top (tests, coverage, LOC, milestone status).

3. **Fill in the Conventions section** at the bottom of this file:
   - Language, framework, test runner
   - Lint rules and coverage floors
   - Coding standards specific to this stack
   - Any constraints from the PRD (e.g., "no .unwrap() on network data", "strict mode")

4. **Write the initial baseline** at `~/.flowstate/{slug}/metrics/baseline-sprint-1.md`:
   - Current git SHA, test count (0 if greenfield), coverage status
   - Gate commands and whether each passes right now
   - 5 H7 instructions picked from `.claude/skills/` to audit in Sprint 1

5. **Commit**: `git add -A && git commit -m "sprint 0: project setup"`

When done, say: "Ready for Phase 3: SHIP whenever you want to proceed."

**Phase 3: SHIP**

Sprint 0's Phase 3 follows the same steps as all sprints (collect metrics, write import JSON, write retro). The differences for Sprint 0:
- `tests_total`: 0 (or current count if pre-existing)
- `tests_added`: 0
- `coverage_pct`: null
- `loc_added`: LOC from git diff --stat (roadmap, baseline, conventions -- not application code)
- `gates_first_pass`: null (no code gates to run)
- `gates_first_pass_note`: "planning sprint -- no code gates"
- Phase 3 steps 6-8 below still apply (retro, baseline already written in step 4, roadmap already written in step 2)
- Hypothesis results: at minimum H1 and H11 (does the process work for this project type?)

Then follow steps 1-8 in Phase 3 below (skip steps that Sprint 0 already completed above).

---

### Phase 1+2: THINK then EXECUTE (Sprint 1+)

Read these files first:
- `PRD.md`
- `docs/ROADMAP.md` (find this sprint's phase)
- The current baseline (see above)
- `~/.flowstate/{slug}/progress.md` (if exists -- operational state from last session)
- `~/.flowstate/{slug}/flowstate.config.md`
- The previous sprint's retro (if exists)
- All files in `.claude/skills/`
- `~/.flowstate/hypotheses.json` (canonical hypothesis IDs, names, valid results)

**THINK**: Acting as a consensus agent with all 5 skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor):
0. FEASIBILITY CHECK: List new external dependencies, verify they exist in the registry, run a minimal spike on the highest-risk task. Flag unverified or experimental deps with a fallback plan. If the spike fails, revise scope before proceeding.
1. Write acceptance criteria in Gherkin format for the phase scope
2. Produce a wave-based implementation plan (group tasks by file dependency; parallel where no shared files)
3. For each task: files to read, files to write, agent model (haiku for mechanical, sonnet for reasoning)

**EXECUTE**: Immediately after planning -- do NOT wait for human approval:
- Spawn subagents per wave
- Each subagent gets file path references (not content), task scope, relevant skill context
- Commit atomically after each wave (single commit is acceptable for sequential waves sharing no files)
- Do NOT read full implementation files into orchestrator context -- delegate to subagents
- Run quality gates IN ORDER after all waves:
{gate_lines}{gate_note}
- Optional preventive gates (run after core gates pass):
  - `bash ~/Sites/Flowstate/tools/deps_check.sh` (verify new deps exist in registry)
  - `bash ~/Sites/Flowstate/tools/sast_check.sh` (static security analysis)
  - `bash ~/Sites/Flowstate/tools/deadcode_check.sh` (detect unused exports/deps)
- Save gate output to `~/.flowstate/{slug}/metrics/sprint-N-gates.log`
- If any gate fails: fix, re-run, max 3 cycles

When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."

### Phase 3: SHIP

1. **Collect metrics** using Flowstate MCP tools:
   - Call `mcp__flowstate__sprint_boundary` with project_path and sprint_marker to find the boundary timestamp
   - Call `mcp__flowstate__list_sessions` with project_path to find the session ID(s) for this sprint
   - Call `mcp__flowstate__collect_metrics` with project_path, session_ids, and the boundary timestamp as "after"
   - Save the raw metrics response to `~/.flowstate/{slug}/metrics/sprint-N-metrics.json`

2. **Write import JSON** at `~/.flowstate/{slug}/metrics/sprint-N-import.json`:
   - Start from the MCP metrics response (`sprint-N-metrics.json`) as the base
   - Add these fields:
     ```json
     {{
       "project": "{slug}",
       "sprint": N,
       "label": {label_example},
       "phase": "[phase name from roadmap]",
       "metrics": {{
         "...everything from sprint-N-metrics.json...",
         "tests_total": "<current test count>",
         "tests_added": "<tests added this sprint>",
         "coverage_pct": "<current coverage % or null>",
         "lint_errors": 0,
         "gates_first_pass": "<true|false>",
         "gates_first_pass_note": "<note if false, empty string if true>",
         "loc_added": "<LOC from git diff --stat>",
         "loc_added_approx": false,
         "task_type": "<feature|bugfix|refactor|infra|planning|hardening>",
         "rework_rate": "<from sprint-N-metrics.json, or null>",
         "judge_score": "<[scope, test_quality, gate_integrity, convention, diff_hygiene] 1-5 each, or null>",
         "judge_blocked": "<true if judge prevented stopping, false otherwise, or null>",
         "judge_block_reason": "<reason string if blocked, or null>",
         "coderabbit_issues": "<number of CodeRabbit issues on PR, or null>",
         "coderabbit_issues_valid": "<number human agreed were real, or null>",
         "mutation_score_pct": "<mutation score if run, or null>"
       }},
       "hypotheses": [
         // Use IDs and names from ~/.flowstate/hypotheses.json
         // Valid results: confirmed, partially_confirmed, inconclusive, falsified
         {{"id": "H1", "name": "<from hypotheses.json>", "result": "...", "evidence": "..."}},
         {{"id": "H5", "name": "<from hypotheses.json>", "result": "...", "evidence": "..."}},
         {{"id": "H7", "name": "<from hypotheses.json>", "result": "...", "evidence": "..."}}
       ]
     }}
     ```
   - The schema matches `sprints.json` entries exactly -- same field names, same types
   - Validate: call `mcp__flowstate__import_sprint` with dry_run=true
   - Fix any errors before proceeding. Warnings (auto-corrections) are ok.

3. **Write retrospective** at `~/.flowstate/{slug}/retrospectives/sprint-N.md`:
   - What was built (deliverables, test count, files changed, LOC)
   - Metrics comparison vs previous sprint
   - What worked / what failed, with evidence
   - H7 audit: check the 5 instructions listed in the baseline
   - Hypothesis results table (include at minimum H1, H5, H7)
   - Change proposals as diffs (with `- Before` / `+ After` blocks)

4. **Do NOT apply skill changes** -- proposals stay in the retro for human review

5. **Commit**: `git add -A && git commit -m "sprint N: [description]"`

6. **Write next baseline** at `~/.flowstate/{slug}/metrics/baseline-sprint-{{N+1}}.md`:
   - Current git SHA, test count, coverage %, lint error count
   - Gate commands and current status
   - 5 H7 instructions to audit next sprint (rotate from skills)

7. **Update roadmap**: mark this phase done in `docs/ROADMAP.md`, update Current State section

8. **Write progress file** at `~/.flowstate/{slug}/progress.md`:
   - What was completed this sprint (list of deliverables)
   - What failed or was deferred (and why)
   - What the next session should do first
   - Any blocked items or external dependencies awaiting resolution
   - Current gate status (all passing? which ones?)
   This is operational state for the next agent session, not analysis. Overwrite any previous progress.md.

9. **Completion check** -- print this checklist with [x] or [MISSING] for each:
   - metrics/sprint-N-metrics.json exists (raw MCP metrics response)
   - metrics/sprint-N-import.json exists (complete import-ready JSON, validated via MCP dry_run)
   - retrospectives/sprint-N.md has hypothesis table (H1, H5, H7) and change proposals
   - metrics/baseline-sprint-{{N+1}}.md exists with SHA, tests, coverage, gates, H7 instructions
   - progress.md written (current state for next session)
   - docs/ROADMAP.md updated
   - Code committed
   Fix any MISSING items before declaring done.

## Conventions

- Start each sprint in a fresh session. One sprint = one session.

<!-- TODO: Sprint 0 fills in language-specific conventions below -->
"""


def generate_claude_md_tier2(name, description, slug, gates, label_prefix, language):
    gate_lines = "\n".join(f"  {i + 1}. `{cmd}`" for i, cmd in enumerate(gates))

    # Gate TODO marker if language wasn't detected
    gate_note = ""
    if not language:
        gate_note = "\n<!-- TODO: Gate commands are placeholders. Sprint 0 should verify and update these. -->"

    return f"""# {name}

{description}

## Flowstate Sprint Workflow (Tier 2)

This project uses the Flowstate sprint process (Tier 2: skills + structure, no automated metrics). Metrics are agent-estimated. The retro produces a sanitized export that the human brings back to the Flowstate repo.

### File Locations

- **Flowstate dir**: `~/.flowstate/{slug}/`
- **Config**: `~/.flowstate/{slug}/flowstate.config.md` (quality gates, agent strategy)
- **Baselines**: `~/.flowstate/{slug}/metrics/baseline-sprint-N.md`
- **Retrospectives**: `~/.flowstate/{slug}/retrospectives/sprint-N.md`
- **Progress**: `~/.flowstate/{slug}/progress.md` (operational state for next session)
- **Roadmap**: `docs/ROADMAP.md` (in this repo -- create if missing)
- **Skills**: `.claude/skills/` (in this repo)

### How to Determine the Next Sprint

1. If no `docs/ROADMAP.md` exists, this is Sprint 0 (see below).
2. Read `docs/ROADMAP.md` -- find the first phase not marked done.
3. Find the highest-numbered baseline in `~/.flowstate/{slug}/metrics/` -- that's your sprint number.
4. Read that baseline for starting state, gate commands, and H7 audit instructions.

### Sprint 0: Project Setup (planning only -- no code)

Sprint 0 is a dedicated planning sprint. It produces the roadmap, baseline, and conventions that all future sprints depend on. No code is written.

**Phase 1+2: RESEARCH then PLAN**

Read these files:
- `PRD.md` (fully -- every section)
- `~/.flowstate/{slug}/flowstate.config.md`
- All files in `.claude/skills/`
- `~/.flowstate/hypotheses.json`

Then do ALL of the following:

1. **Verify gate commands.** Run each gate command below. If any don't work for this project (wrong tool, missing dependency), update them in this file AND in `~/.flowstate/{slug}/flowstate.config.md`. Record what works and what doesn't.
{gate_lines}{gate_note}

2. **Create `docs/ROADMAP.md`.**
   - Break PRD milestones into sprint-sized phases. Each phase = one sprint.
   - Right-sizing guide: a phase should be deliverable in 10-60 minutes of active agent time, produce 500-2500 LOC, and have a clear "done" state that gates can verify.
   - Phases that are mostly research or refactoring will be smaller. Phases that build new features from scratch will be larger.
   - Number phases starting from 1 (Sprint 0 is this planning sprint).
   - Include a "Current State" section at the top (tests, coverage, LOC, milestone status).

3. **Fill in the Conventions section** at the bottom of this file:
   - Language, framework, test runner
   - Lint rules and coverage floors
   - Coding standards specific to this stack
   - Any constraints from the PRD (e.g., "no .unwrap() on network data", "strict mode")

4. **Write the initial baseline** at `~/.flowstate/{slug}/metrics/baseline-sprint-1.md`:
   - Current git SHA, test count (0 if greenfield), coverage status
   - Gate commands and whether each passes right now
   - 5 H7 instructions picked from `.claude/skills/` to audit in Sprint 1

5. **Commit**: `git add -A && git commit -m "sprint 0: project setup"`

When done, say: "Ready for Phase 3: SHIP whenever you want to proceed."

**Phase 3: SHIP**

Sprint 0's Phase 3:
1. Write `~/.flowstate/{slug}/retrospectives/sprint-0.md` (what was planned, gate verification results, any issues found)
2. Hypothesis results: at minimum H1 and H11 (does the process work for this project type?)
3. Produce a SANITIZED EXPORT (see Phase 3 below for format)
4. Write progress file at `~/.flowstate/{slug}/progress.md`
5. Completion check (see Phase 3 below)

---

### Phase 1+2: THINK then EXECUTE (Sprint 1+)

Read these files first:
- `PRD.md`
- `docs/ROADMAP.md` (find this sprint's phase)
- The current baseline (see above)
- `~/.flowstate/{slug}/progress.md` (if exists -- operational state from last session)
- `~/.flowstate/{slug}/flowstate.config.md`
- The previous sprint's retro (if exists)
- All files in `.claude/skills/`
- `~/.flowstate/hypotheses.json` (canonical hypothesis IDs, names, valid results)

**THINK**: Acting as a consensus agent with all 5 skill perspectives (PM, UX, Architect, Production Engineer, Security Auditor):
0. FEASIBILITY CHECK: List new external dependencies, verify they exist in the registry, run a minimal spike on the highest-risk task. Flag unverified or experimental deps with a fallback plan. If the spike fails, revise scope before proceeding. Confirm a formatter AND linter are configured as gates -- if either is missing, set one up now.
1. Write acceptance criteria in Gherkin format for the phase scope
2. Produce a wave-based implementation plan (group tasks by file dependency; parallel where no shared files)
3. For each task: files to read, files to write, agent model (haiku for mechanical, sonnet for reasoning)

**EXECUTE**: Immediately after planning -- do NOT wait for human approval:
- Spawn subagents per wave
- Each subagent gets file path references (not content), task scope, relevant skill context
- Commit atomically after each wave (single commit is acceptable for sequential waves sharing no files)
- Do NOT read full implementation files into orchestrator context -- delegate to subagents
- Run quality gates IN ORDER after all waves:
{gate_lines}{gate_note}
- If bash is available, save gate output to `~/.flowstate/{slug}/metrics/sprint-N-gates.log`
- If not, paste the gate output into the retrospective under a "## Gate Log" section
- If any gate fails: classify as REGRESSION or FEATURE, fix, re-run, max 3 cycles

When all gates pass, say: "Ready for Phase 3: SHIP whenever you want to proceed."

### Phase 3: SHIP

1. **Write retrospective** at `~/.flowstate/{slug}/retrospectives/sprint-N.md`:
   - What was built (deliverables, test count, files changed)
   - What worked / what failed, with evidence
   - H7 audit: check the 5 instructions listed in the baseline
   - Change proposals as diffs (with `- Before` / `+ After` blocks). Prefer removing or simplifying instructions over adding new ones.

2. **Hypothesis results table** (include at minimum H1, H5, H7)

3. **Sanitized export** -- produce a markdown document starting with "# Flowstate Sanitized Sprint Export". This will leave this environment, so it must contain NO proprietary code, architecture details, file paths, business logic, or project-specific content. Only include:
   - Sprint number, language/framework, generalized scope description
   - Metrics: estimate your active session time, count subagents spawned, count tests added, gate pass/fail
   - Task type: feature, bugfix, refactor, infra, planning, or hardening
   - Hypothesis results: H1 (3-phase worked?), H5 (gates caught issues?), H7 (X/5 compliance)
   - Skill change proposals GENERALIZED: strip project-specific details, describe the pattern not the implementation
   - Process observations: did the single prompt work? friction points? what would you change?

4. **Do NOT apply skill changes** -- proposals stay in the retro for human review

5. **Commit**: `git add -A && git commit -m "sprint N: [generalized description]"`

6. **Write next baseline** at `~/.flowstate/{slug}/metrics/baseline-sprint-{{N+1}}.md`:
   - Current git SHA, test count, coverage %, lint error count
   - Gate commands and current status
   - 5 H7 instructions to audit next sprint (rotate from skills)

7. **Update roadmap**: mark this phase done in `docs/ROADMAP.md`, update Current State section

8. **Write progress file** at `~/.flowstate/{slug}/progress.md`:
   - What was completed this sprint (list of deliverables)
   - What failed or was deferred (and why)
   - What the next session should do first
   - Any blocked items or external dependencies awaiting resolution
   - Current gate status (all passing? which ones?)
   This is operational state for the next agent session, not analysis. Overwrite any previous progress.md.

9. **Completion check** -- print this checklist with [x] or [MISSING] for each:
   - retrospectives/sprint-N.md has hypothesis table (H1, H5, H7) and change proposals
   - Sanitized export produced (starting with "# Flowstate Sanitized Sprint Export")
   - metrics/baseline-sprint-{{N+1}}.md exists with SHA, tests, coverage, gates, H7 instructions
   - progress.md written (current state for next session)
   - docs/ROADMAP.md updated
   - Code committed
   Fix any MISSING items before declaring done.

## Conventions

- Start each sprint in a fresh session. One sprint = one session.

<!-- TODO: Sprint 0 fills in language-specific conventions below -->
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    project_dir = os.getcwd()

    # Parse --tier flag
    tier = 1
    args = sys.argv[1:]
    if "--tier" in args:
        idx = args.index("--tier")
        if idx + 1 < len(args) and args[idx + 1] in ("1", "2"):
            tier = int(args[idx + 1])
        else:
            print("\n  ERROR: --tier requires 1 or 2 (e.g., --tier 2)")
            sys.exit(1)

    # Check PRD.md exists
    prd_path = os.path.join(project_dir, "PRD.md")
    if not os.path.exists(prd_path):
        print("\n  ERROR: PRD.md not found in current directory.")
        print(f"  Looked in: {project_dir}")
        print("\n  Create PRD.md first, then run this script again.")
        sys.exit(1)

    # Parse PRD
    prd = parse_prd(prd_path)
    name = prd["name"]
    description = prd["description"]
    language = prd["language"]
    slug = make_slug(name)
    label_prefix = make_label_prefix(name)

    # Get gate commands
    if language and language in GATE_PRESETS:
        gates = GATE_PRESETS[language]
    else:
        gates = [
            "echo 'TODO: build/typecheck command'",
            "echo 'TODO: lint command'",
            "echo 'TODO: test command'",
            "echo 'TODO: coverage command'",
        ]

    flowstate_dir = os.path.join(FLOWSTATE_HOME, slug)

    # Print what we inferred
    print(f"\n  Flowstate Tier {tier} Bootstrap")
    print(f"  PRD: {prd_path}\n")
    print(f"    Name:        {name}")
    print(f"    Slug:        {slug}")
    print(f"    Label:       {label_prefix} S0, {label_prefix} S1, ...")
    print(f"    Language:    {language or 'not detected'}")
    print(
        f"    Gates:       {len(gates)} ({'inferred' if language else 'TODO placeholders'})"
    )
    print(
        f"    Description: {description[:70]}{'...' if len(description) > 70 else ''}"
    )

    # Check for existing files
    if os.path.exists(os.path.join(project_dir, "CLAUDE.md")):
        print(f"\n  WARNING: CLAUDE.md already exists.")
        confirm = input("  Overwrite? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Aborted.")
            sys.exit(0)

    if os.path.exists(flowstate_dir):
        print(f"\n  WARNING: {flowstate_dir} already exists.")
        confirm = input("  Continue anyway? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Aborted.")
            sys.exit(0)

    # --- Create ~/.flowstate/{slug}/ ---
    print(f"\n  Creating files...\n")
    metrics_dir = os.path.join(flowstate_dir, "metrics")
    retro_dir = os.path.join(flowstate_dir, "retrospectives")
    os.makedirs(metrics_dir, exist_ok=True)
    os.makedirs(retro_dir, exist_ok=True)

    # flowstate.config.md
    config_path = os.path.join(flowstate_dir, "flowstate.config.md")
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write(generate_config(gates, language))
        print(f"    ~/.flowstate/{slug}/flowstate.config.md")
    else:
        print(f"    ~/.flowstate/{slug}/flowstate.config.md (exists, skipped)")

    # collect.sh (Tier 1 only) — symlink to repo so updates propagate automatically
    if tier == 1:
        collect_src = os.path.join(FLOWSTATE_REPO, "tier-1", "collect.sh")
        collect_dst = os.path.join(metrics_dir, "collect.sh")
        if os.path.exists(collect_dst) or os.path.islink(collect_dst):
            os.remove(collect_dst)
        os.symlink(collect_src, collect_dst)
        print(f"    ~/.flowstate/{slug}/metrics/collect.sh -> {collect_src}")

    # retrospectives/
    print(f"    ~/.flowstate/{slug}/retrospectives/")

    # --- Deploy hypotheses.json (shared) ---
    hypo_src = os.path.join(FLOWSTATE_REPO, "hypotheses.json")
    hypo_dst = os.path.join(FLOWSTATE_HOME, "hypotheses.json")
    if not os.path.exists(hypo_dst):
        shutil.copy2(hypo_src, hypo_dst)
        print(f"    ~/.flowstate/hypotheses.json")
    else:
        print(f"    ~/.flowstate/hypotheses.json (exists, skipped)")

    # --- Copy skills ---
    skills_src = os.path.join(FLOWSTATE_REPO, "skills")
    skills_dst = os.path.join(project_dir, ".claude", "skills")
    os.makedirs(skills_dst, exist_ok=True)
    skill_count = 0
    for fname in sorted(os.listdir(skills_src)):
        if fname.endswith(".md"):
            shutil.copy2(
                os.path.join(skills_src, fname), os.path.join(skills_dst, fname)
            )
            skill_count += 1
    print(f"    .claude/skills/ ({skill_count} files)")

    # --- Generate CLAUDE.md ---
    if tier == 2:
        claude_md = generate_claude_md_tier2(
            name, description, slug, gates, label_prefix, language
        )
    else:
        claude_md = generate_claude_md(
            name, description, slug, gates, label_prefix, language
        )
    claude_path = os.path.join(project_dir, "CLAUDE.md")
    with open(claude_path, "w") as f:
        f.write(claude_md)
    print(f"    CLAUDE.md")

    # --- Deploy slash commands ---
    commands_src = os.path.join(FLOWSTATE_REPO, "commands")
    commands_dst = os.path.join(project_dir, ".claude", "commands")
    os.makedirs(commands_dst, exist_ok=True)
    cmd_count = 0
    for fname in sorted(os.listdir(commands_src)):
        if fname.endswith(".md"):
            with open(os.path.join(commands_src, fname)) as f:
                content = f.read()
            # Substitute project slug
            content = content.replace("{SLUG}", slug)
            with open(os.path.join(commands_dst, fname), "w") as f:
                f.write(content)
            cmd_count += 1
    print(f"    .claude/commands/ ({cmd_count} commands: /sprint, /ship)")

    # --- Generate .claude/settings.json (LLM-as-judge Stop hook) ---
    settings_path = os.path.join(project_dir, ".claude", "settings.json")
    if not os.path.exists(settings_path):
        with open(settings_path, "w") as f:
            f.write(generate_project_settings())
            f.write("\n")
        print(f"    .claude/settings.json (LLM-as-judge hook)")
    else:
        print(f"    .claude/settings.json (exists, skipped)")

    # --- Summary ---
    print(
        f"\n  Done. Next: open a fresh Claude Code session and run /sprint."
    )
    print(f"  The agent will read the PRD, create the roadmap, and run Sprint 0.")
    print(f"  After gates pass, run /ship for Phase 3.\n")

    if not language:
        print(
            f"  NOTE: Language not detected from PRD. Gate commands are placeholders."
        )
        print(f"  The agent will discover and update them during Sprint 0.\n")


if __name__ == "__main__":
    main()
