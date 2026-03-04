#!/usr/bin/env bash
set -euo pipefail

# Setup Flowstate on a remote server (VPS).
#
# Run from the Flowstate repo clone on the server:
#   git clone https://github.com/smledbetter/Flowstate.git ~/Flowstate
#   bash ~/Flowstate/tools/setup-server.sh
#
# What this does:
#   1. Sets FLOWSTATE_REPO in shell profile so all sessions know where Flowstate lives
#   2. Registers the MCP server with Claude Code (global, all projects)
#   3. Creates ~/.flowstate/ base directory
#   4. Verifies Python 3 is available (stdlib only, no pip needed)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLOWSTATE_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Flowstate Server Setup"
echo "  Repo: $FLOWSTATE_REPO"
echo ""

# 1. Set FLOWSTATE_REPO in shell profile
PROFILE=""
if [[ -f "$HOME/.zshrc" ]]; then
    PROFILE="$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
    PROFILE="$HOME/.bashrc"
elif [[ -f "$HOME/.profile" ]]; then
    PROFILE="$HOME/.profile"
fi

if [[ -n "$PROFILE" ]]; then
    if grep -q "FLOWSTATE_REPO" "$PROFILE" 2>/dev/null; then
        echo "  FLOWSTATE_REPO already in $PROFILE"
    else
        echo "" >> "$PROFILE"
        echo "# Flowstate repo location (used by sprint tools)" >> "$PROFILE"
        echo "export FLOWSTATE_REPO=\"$FLOWSTATE_REPO\"" >> "$PROFILE"
        echo "  Added FLOWSTATE_REPO=$FLOWSTATE_REPO to $PROFILE"
    fi
else
    echo "  WARNING: No shell profile found. Add manually:"
    echo "    export FLOWSTATE_REPO=\"$FLOWSTATE_REPO\""
fi

# Export for this session
export FLOWSTATE_REPO

# 2. Register MCP server with Claude Code
MCP_SERVER="$FLOWSTATE_REPO/tools/mcp_server.py"
if command -v claude &>/dev/null; then
    # Check if already registered
    if claude mcp list 2>/dev/null | grep -q "flowstate"; then
        echo "  Flowstate MCP server already registered"
    else
        claude mcp add -s user flowstate -- python3 "$MCP_SERVER"
        echo "  Registered Flowstate MCP server: python3 $MCP_SERVER"
    fi
else
    echo "  WARNING: claude CLI not found. Register MCP server manually:"
    echo "    claude mcp add -s user flowstate -- python3 $MCP_SERVER"
fi

# 3. Create ~/.flowstate/ base directory
mkdir -p "$HOME/.flowstate"
echo "  ~/.flowstate/ exists"

# 4. Verify Python 3
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1)
    echo "  $PY_VERSION available"
else
    echo "  ERROR: python3 not found. Install it first."
    exit 1
fi

echo ""
echo "Done. Next steps:"
echo "  1. Source your profile: source $PROFILE"
echo "  2. For each project, run init.py from the project dir:"
echo "     cd /path/to/project && python3 $FLOWSTATE_REPO/tools/init.py"
echo "  3. Or if already set up locally, copy ~/.flowstate/<slug>/ from your Mac"
echo ""
echo "Metrics flow:"
echo "  - Sprints run on this server, metrics collected via MCP"
echo "  - sprints.json lives in this Flowstate clone ($FLOWSTATE_REPO/sprints.json)"
echo "  - Auto-import writes to it during continuous flow"
echo "  - git push/pull to sync with your Mac when you want dashboard access"
