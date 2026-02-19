#!/usr/bin/env bash
# Dead code detection gate: find unused exports, functions, and dependencies.
# Auto-detects language and runs the appropriate tool.
#
# Usage: ./deadcode_check.sh [--json]
#
# Tools used:
#   TypeScript/JS: knip (npx knip)
#   Rust: cargo-udeps (cargo +nightly udeps)
#   Python: vulture
#
# Exit codes:
#   0 = no dead code found (or tool not available — warns but passes)
#   1 = dead code detected
#   2 = unsupported project type

set -euo pipefail

JSON_OUTPUT=""
if [ "${1:-}" = "--json" ]; then JSON_OUTPUT="1"; shift; fi

if [ -f "package.json" ]; then
  # TypeScript / JavaScript
  if ! npx knip --version &>/dev/null 2>&1; then
    if [ -n "$JSON_OUTPUT" ]; then
      echo '{"status": "skipped", "reason": "knip not available"}'
    else
      echo "knip not available. Install: npm install -D knip"
    fi
    exit 0
  fi

  if [ -n "$JSON_OUTPUT" ]; then
    npx knip --reporter json 2>/dev/null || true
  else
    echo "Running dead code detection with knip..."
    if npx knip --no-exit-code 2>/dev/null; then
      echo "Dead code gate passed."
    else
      echo "Dead code gate FAILED — unused exports/dependencies detected above."
      exit 1
    fi
  fi

elif [ -f "Cargo.toml" ]; then
  # Rust
  if ! cargo udeps --version &>/dev/null 2>&1; then
    if [ -n "$JSON_OUTPUT" ]; then
      echo '{"status": "skipped", "reason": "cargo-udeps not installed"}'
    else
      echo "cargo-udeps not installed. Install: cargo install cargo-udeps"
    fi
    exit 0
  fi

  if [ -n "$JSON_OUTPUT" ]; then
    cargo +nightly udeps --output json 2>/dev/null || true
  else
    echo "Running dead code detection with cargo-udeps..."
    if cargo +nightly udeps 2>/dev/null; then
      echo "Dead code gate passed — no unused dependencies."
    else
      echo "Dead code gate FAILED — unused dependencies detected above."
      exit 1
    fi
  fi

elif [ -f "setup.py" ] || [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
  # Python
  if ! command -v vulture &>/dev/null; then
    if [ -n "$JSON_OUTPUT" ]; then
      echo '{"status": "skipped", "reason": "vulture not installed"}'
    else
      echo "vulture not installed. Install: pip install vulture"
    fi
    exit 0
  fi

  SRC_DIR="src"
  [ -d "$SRC_DIR" ] || SRC_DIR="."

  if [ -n "$JSON_OUTPUT" ]; then
    vulture "$SRC_DIR" --min-confidence 80 2>/dev/null || true
  else
    echo "Running dead code detection with vulture..."
    if vulture "$SRC_DIR" --min-confidence 80 2>/dev/null; then
      echo "Dead code gate passed."
    else
      echo "Dead code gate FAILED — unused code detected above."
      exit 1
    fi
  fi

else
  if [ -n "$JSON_OUTPUT" ]; then
    echo '{"status": "skipped", "reason": "unsupported project type"}'
  else
    echo "No supported project type detected."
  fi
  exit 2
fi
