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
    .claude/skills/                (3 planning skills + flowstate workflow skill)
    .claude/commands/              (slash commands: /gate, /sprint-ship)
    .claude/settings.json          (LLM-as-judge Stop hook)
    CLAUDE.md                      (project conventions, gate list, file locations)
"""

import json
import os
import re
import shutil
import sys

FLOWSTATE_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOWSTATE_HOME = os.path.expanduser("~/.flowstate")

# Planning skills to auto-copy (prod-eng and security stay in repo but aren't auto-copied)
PLANNING_SKILLS = ["architect.md", "product-manager.md", "ux-designer.md"]

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
    "go": ["go", "golang", "goroutine", "go module", "go build", "go test"],
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
            # Strip bold markdown
            name = name.replace("**", "")
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
            # Use word boundaries to avoid false matches (e.g., "distrust" matching "rust")
            pattern = r"\b" + re.escape(kw.strip()) + r"\b"
            score += len(re.findall(pattern, search_lower))
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
                pattern = r"\b" + re.escape(kw.strip()) + r"\b"
                score += len(re.findall(pattern, tech_lower))
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
    "No unnecessary reformatting, no dead code left behind?\\n"
    "6. PRODUCTION_SHAPE: If any component runs continuously "
    "(--watch, --daemon, polling loop, persistent connection, long-lived pipeline), "
    "is there at least one test that starts it as a background process, "
    "sends real input, and verifies output arrives within a bounded wait? "
    "Score 5 if N/A (no long-running components). "
    "Score 1-2 if all tests use one-shot/exit mode for a component meant to run continuously.\\n\\n"
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
- coverage_regression_gate: true -- coverage % must be >= baseline
- custom_gates: []

## Agent Strategy
- model: opus
- default_strategy: plan-mode-then-auto-accept
- multi_agent: subagents for independent packages (no shared files)
- teams: 1200+ LOC new features with 3+ independent workstreams

## Notes
- {lang_note}
- Gates may need adjustment after Sprint 0 discovers the actual toolchain
"""


# ---------------------------------------------------------------------------
# CLAUDE.md template
# ---------------------------------------------------------------------------


def generate_claude_md(name, description, slug, gates, label_prefix, language):
    gate_lines = "\n".join(f"- `{cmd}`" for cmd in gates)

    gate_note = ""
    if not language:
        gate_note = "\n<!-- TODO: Gate commands are placeholders. Sprint 0 will verify and update these. -->"

    lang_note = ""
    if language:
        lang_note = f"\n- Language detected: {language}"

    return f"""# {name}

{description}

## Workflow

- Start each sprint in a fresh session. One sprint = one session.
- Sprint workflow auto-loads from `.claude/skills/flowstate/SKILL.md`.
- Run `/gate` after every meaningful change.
- When Phase 1+2 gates pass, run `/sprint-ship N` for Phase 3.
- Use Plan mode first. Iterate until the plan is solid, then switch to auto-accept for implementation.
- Use subagents only for parallel independent work (3+ files, zero overlap). Implement in the main session.

## Quality Gates

Run with `/gate`. Commands are in `~/.flowstate/{slug}/flowstate.config.md`.

{gate_lines}{gate_note}

## Conventions

- Start each sprint in a fresh session. One sprint = one session.
{lang_note}

<!-- TODO: Sprint 0 fills in language-specific conventions below:
  - Language, framework, test runner
  - Lint rules and coverage floors
  - Coding standards specific to this stack
  - Any constraints from the PRD
  - Known issues and gotchas
-->
"""


def generate_claude_md_tier2(name, description, slug, gates, label_prefix, language):
    gate_lines = "\n".join(f"- `{cmd}`" for cmd in gates)

    gate_note = ""
    if not language:
        gate_note = "\n<!-- TODO: Gate commands are placeholders. Sprint 0 will verify and update these. -->"

    lang_note = ""
    if language:
        lang_note = f"\n- Language detected: {language}"

    return f"""# {name}

{description}

## Workflow (Tier 2)

- Start each sprint in a fresh session. One sprint = one session.
- Sprint workflow auto-loads from `.claude/skills/flowstate/SKILL.md`.
- Metrics are agent-estimated. Phase 3 produces a sanitized export.
- Run gates after every meaningful change.
- Use Plan mode first. Iterate until the plan is solid, then switch to auto-accept for implementation.

## Quality Gates

Commands are in `~/.flowstate/{slug}/flowstate.config.md`.

{gate_lines}{gate_note}

## Conventions

- Start each sprint in a fresh session. One sprint = one session.
{lang_note}

<!-- TODO: Sprint 0 fills in language-specific conventions below:
  - Language, framework, test runner
  - Lint rules and coverage floors
  - Coding standards specific to this stack
  - Any constraints from the PRD
  - Known issues and gotchas
-->
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

    # --- Copy planning skills ---
    skills_src = os.path.join(FLOWSTATE_REPO, "skills")
    skills_dst = os.path.join(project_dir, ".claude", "skills")
    os.makedirs(skills_dst, exist_ok=True)
    for fname in PLANNING_SKILLS:
        src = os.path.join(skills_src, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(skills_dst, fname))
    print(f"    .claude/skills/ ({len(PLANNING_SKILLS)} planning skills)")

    # --- Install flowstate workflow skill (with slug substitution) ---
    skill_source_name = "SKILL.md" if tier == 1 else "SKILL-tier2.md"
    flowstate_skill_src = os.path.join(skills_src, "flowstate", skill_source_name)
    flowstate_skill_dst_dir = os.path.join(skills_dst, "flowstate")
    flowstate_skill_dst = os.path.join(flowstate_skill_dst_dir, "SKILL.md")
    os.makedirs(flowstate_skill_dst_dir, exist_ok=True)
    with open(flowstate_skill_src) as f:
        content = f.read()
    content = content.replace("{SLUG}", slug)
    content = content.replace("{FLOWSTATE}", f"~/.flowstate/{slug}")
    content = content.replace("{LABEL_EXAMPLE}", f'"{label_prefix} SN"')
    with open(flowstate_skill_dst, "w") as f:
        f.write(content)
    print(f"    .claude/skills/flowstate/SKILL.md")

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

    # --- Deploy slash commands (with slug substitution) ---
    commands_src = os.path.join(FLOWSTATE_REPO, "commands")
    if os.path.isdir(commands_src):
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
        print(f"    .claude/commands/ ({cmd_count} commands: /gate, /sprint-ship)")
    else:
        print(
            f"    .claude/commands/ (skipped -- commands/ not found in Flowstate repo)"
        )

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
        f'\n  Done. Next: open a fresh Claude Code session and say "start the next sprint".'
    )
    print(
        f"  The flowstate skill auto-loads and guides Sprint 0 (roadmap, baseline, conventions)."
    )
    print(f"  After gates pass in each sprint, run /sprint-ship for Phase 3.\n")

    if not language:
        print(
            f"  NOTE: Language not detected from PRD. Gate commands are placeholders."
        )
        print(f"  The agent will discover and update them during Sprint 0.\n")


if __name__ == "__main__":
    main()
