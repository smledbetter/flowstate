#!/usr/bin/env bash
# launcher.sh — Set up and launch an experiment build
#
# Usage:
#   ./launcher.sh <product> <condition> [--dry-run]
#
# Example:
#   ./launcher.sh fconv a
#   ./launcher.sh presskit d
#   ./launcher.sh fconv e --dry-run
#
# Creates the project directory, copies PRD and SKILL.md variant,
# initializes git, and launches claude in a tmux session.

set -euo pipefail

EXPERIMENT_DIR="/home/dev/experiment"
FLOWSTATE_DIR="$HOME/.flowstate"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONDITIONS_DIR="$SCRIPT_DIR/conditions"
PRDS_DIR="$SCRIPT_DIR/prds"
LESSONS_SNAPSHOT="$SCRIPT_DIR/lessons-snapshot.json"

PRODUCT="${1:?Usage: ./launcher.sh <product> <condition> [--dry-run]}"
CONDITION="${2:?Usage: ./launcher.sh <product> <condition> [--dry-run]}"
DRY_RUN="${3:-}"

BUILD_NAME="${PRODUCT}-${CONDITION}"
BUILD_DIR="${EXPERIMENT_DIR}/${BUILD_NAME}"
FLOWSTATE_BUILD_DIR="${FLOWSTATE_DIR}/exp-${BUILD_NAME}"
TMUX_SESSION="exp-${BUILD_NAME}"

# Validate condition
if [[ ! "$CONDITION" =~ ^[a-e]$ ]]; then
    echo "ERROR: condition must be a, b, c, d, or e"
    exit 1
fi

# Validate PRD exists
PRD_FILE="${PRDS_DIR}/${PRODUCT}.md"
if [ ! -f "$PRD_FILE" ]; then
    echo "ERROR: PRD not found at $PRD_FILE"
    echo "Available PRDs:"
    ls "$PRDS_DIR"/*.md 2>/dev/null | xargs -I{} basename {} .md
    exit 1
fi

# Validate SKILL.md variant exists
SKILL_FILE="${CONDITIONS_DIR}/condition-${CONDITION}.md"
if [ ! -f "$SKILL_FILE" ]; then
    echo "ERROR: SKILL.md variant not found at $SKILL_FILE"
    exit 1
fi

echo "=== Experiment Build Setup ==="
echo "Product:    $PRODUCT"
echo "Condition:  $CONDITION"
echo "Build dir:  $BUILD_DIR"
echo "Flowstate:  $FLOWSTATE_BUILD_DIR"
echo "Tmux:       $TMUX_SESSION"
echo ""

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "[DRY RUN] Would create directories and launch. Exiting."
    exit 0
fi

# Check for existing build
if [ -d "$BUILD_DIR" ]; then
    echo "ERROR: Build directory already exists: $BUILD_DIR"
    echo "Remove it first if you want to rebuild: rm -rf $BUILD_DIR"
    exit 1
fi

# Create directories
mkdir -p "$BUILD_DIR"
mkdir -p "$FLOWSTATE_BUILD_DIR/metrics"
mkdir -p "$FLOWSTATE_BUILD_DIR/retrospectives"

# Copy PRD
cp "$PRD_FILE" "$BUILD_DIR/PRD.md"

# Create CLAUDE.md with experiment metadata
cat > "$BUILD_DIR/CLAUDE.md" << EOF
# ${PRODUCT}

## Experiment

This build is part of the Flowstate v1.2 experiment.
- **Product**: ${PRODUCT}
- **Condition**: ${CONDITION}
- **Build ID**: exp-${BUILD_NAME}

## Conventions

See PRD.md for the full product specification. Follow the conventions specified there.
EOF

# Set up .claude/skills/flowstate/
mkdir -p "$BUILD_DIR/.claude/skills/flowstate"
cp "$SKILL_FILE" "$BUILD_DIR/.claude/skills/flowstate/SKILL.md"

# Customize SKILL.md placeholders
# Replace {FLOWSTATE} with the actual flowstate directory
sed -i "s|{FLOWSTATE}|${FLOWSTATE_BUILD_DIR}|g" "$BUILD_DIR/.claude/skills/flowstate/SKILL.md" 2>/dev/null || true

# Set up flowstate.config.md (generic — Sprint 0 will customize)
cat > "$FLOWSTATE_BUILD_DIR/flowstate.config.md" << 'CONFIGEOF'
# Flowstate Config

## Quality Gates

Gate commands will be configured during Sprint 0 based on the project's stack.

## Agent Strategy

- Default: sequential implementation
- Use subagents for independent modules (>1200 LOC sprints)
CONFIGEOF

# For conditions B, D, E: seed the lesson corpus
if [[ "$CONDITION" =~ ^[bde]$ ]] && [ -f "$LESSONS_SNAPSHOT" ]; then
    cp "$LESSONS_SNAPSHOT" "$FLOWSTATE_BUILD_DIR/cross-project-lessons.json"
    echo "Seeded lesson corpus ($(wc -l < "$LESSONS_SNAPSHOT") lines)"
fi

# Set up .claude/settings.json for bypass permissions
mkdir -p "$BUILD_DIR/.claude"
cat > "$BUILD_DIR/.claude/settings.json" << 'SETTINGSEOF'
{
  "permissions": {
    "allow": [
      "mcp__acp__Bash",
      "mcp__acp__Edit",
      "mcp__acp__Write"
    ]
  }
}
SETTINGSEOF

# Initialize git
cd "$BUILD_DIR"
git init -q
git add -A
git commit -q -m "experiment setup: ${PRODUCT} condition ${CONDITION}"

echo ""
echo "Build directory ready: $BUILD_DIR"
echo ""

# Launch in tmux
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "WARNING: tmux session $TMUX_SESSION already exists. Attaching..."
    tmux attach -t "$TMUX_SESSION"
else
    echo "Launching claude in tmux session: $TMUX_SESSION"
    tmux new-session -d -s "$TMUX_SESSION" \
        "cd $BUILD_DIR && claude -p --dangerously-skip-permissions 'go'"
    echo "Started. Monitor with: tmux attach -t $TMUX_SESSION"
fi

echo ""
echo "=== Build launched ==="
