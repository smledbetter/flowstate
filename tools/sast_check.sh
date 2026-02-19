#!/usr/bin/env bash
# SAST gate: run static application security testing.
# Uses Semgrep with auto-config for language-appropriate rules.
#
# Usage: ./sast_check.sh [--json]
#
# Prerequisites: pip install semgrep (or brew install semgrep)
#
# Exit codes:
#   0 = no findings
#   1 = findings detected
#   2 = semgrep not installed

set -euo pipefail

JSON_OUTPUT=""
if [ "${1:-}" = "--json" ]; then JSON_OUTPUT="1"; shift; fi

if ! command -v semgrep &>/dev/null; then
  if [ -n "$JSON_OUTPUT" ]; then
    echo '{"status": "skipped", "reason": "semgrep not installed"}'
  else
    echo "semgrep not installed. Install: pip install semgrep"
  fi
  exit 2
fi

# Determine source directory
SRC_DIR="src"
if [ ! -d "$SRC_DIR" ]; then
  SRC_DIR="."
fi

if [ -n "$JSON_OUTPUT" ]; then
  semgrep --config auto "$SRC_DIR" --json --quiet 2>/dev/null
  exit $?
else
  echo "Running SAST scan with Semgrep..."
  if semgrep --config auto "$SRC_DIR" --quiet 2>/dev/null; then
    echo "SAST gate passed — no findings."
  else
    echo "SAST gate FAILED — findings detected above."
    exit 1
  fi
fi
