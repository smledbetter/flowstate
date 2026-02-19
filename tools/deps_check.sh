#!/usr/bin/env bash
# Dependency verification gate: detect new/changed dependencies and verify they exist.
# Catches hallucinated packages (slopsquatting) before they ship.
#
# Usage: ./deps_check.sh [--json]
#
# Auto-detects language from project files. Compares current lockfile against
# the last committed version. Any new dependency is verified against the registry.
#
# Exit codes:
#   0 = no new deps, or all new deps verified
#   1 = one or more deps failed verification
#   2 = no lockfile found or unsupported project

set -euo pipefail

JSON_OUTPUT=""
if [ "${1:-}" = "--json" ]; then JSON_OUTPUT="1"; shift; fi

FAILURES=()
VERIFIED=()

verify_npm_package() {
  local pkg="$1"
  if npm view "$pkg" name &>/dev/null; then
    VERIFIED+=("$pkg")
  else
    FAILURES+=("$pkg")
  fi
}

verify_cargo_crate() {
  local crate="$1"
  # cargo search returns results or empty
  if cargo search --limit 1 "$crate" 2>/dev/null | grep -q "^${crate} "; then
    VERIFIED+=("$crate")
  else
    FAILURES+=("$crate")
  fi
}

verify_pip_package() {
  local pkg="$1"
  if pip index versions "$pkg" &>/dev/null; then
    VERIFIED+=("$pkg")
  else
    FAILURES+=("$pkg")
  fi
}

# --- Detect project type and find new deps ---

if [ -f "package-lock.json" ]; then
  # Node/TypeScript project
  NEW_DEPS=$(git diff HEAD -- package.json 2>/dev/null \
    | grep '^\+' | grep -v '^\+\+\+' \
    | grep -oE '"[^"]+"\s*:\s*"[~^]?[0-9]' \
    | grep -oE '"[^"]+"' | tr -d '"' \
    || true)

  if [ -z "$NEW_DEPS" ]; then
    [ -z "$JSON_OUTPUT" ] && echo "No new dependencies detected."
    exit 0
  fi

  for pkg in $NEW_DEPS; do
    verify_npm_package "$pkg"
  done

elif [ -f "Cargo.lock" ]; then
  # Rust project
  NEW_DEPS=$(git diff HEAD -- Cargo.toml 2>/dev/null \
    | grep '^\+' | grep -v '^\+\+\+' \
    | grep -E '^\+[a-zA-Z]' \
    | sed 's/=.*//' | tr -d ' +' \
    | grep -v '^\[' | grep -v '^$' \
    || true)

  if [ -z "$NEW_DEPS" ]; then
    [ -z "$JSON_OUTPUT" ] && echo "No new dependencies detected."
    exit 0
  fi

  for crate in $NEW_DEPS; do
    verify_cargo_crate "$crate"
  done

elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
  # Python project
  LOCK_FILE=""
  if [ -f "requirements.txt" ]; then LOCK_FILE="requirements.txt"; fi
  if [ -f "pyproject.toml" ]; then LOCK_FILE="pyproject.toml"; fi

  NEW_DEPS=$(git diff HEAD -- "$LOCK_FILE" 2>/dev/null \
    | grep '^\+' | grep -v '^\+\+\+' \
    | grep -oE '[a-zA-Z][a-zA-Z0-9_-]+' \
    | head -20 \
    || true)

  if [ -z "$NEW_DEPS" ]; then
    [ -z "$JSON_OUTPUT" ] && echo "No new dependencies detected."
    exit 0
  fi

  for pkg in $NEW_DEPS; do
    verify_pip_package "$pkg"
  done

else
  if [ -n "$JSON_OUTPUT" ]; then
    echo '{"status": "skipped", "reason": "no lockfile found"}'
  else
    echo "No supported lockfile found (package-lock.json, Cargo.lock, requirements.txt, pyproject.toml)."
  fi
  exit 2
fi

# --- Report ---

if [ -n "$JSON_OUTPUT" ]; then
  python3 -c "
import json
verified = $(printf '%s\n' "${VERIFIED[@]:-}" | python3 -c "import sys,json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))")
failures = $(printf '%s\n' "${FAILURES[@]:-}" | python3 -c "import sys,json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))")
print(json.dumps({
    'status': 'fail' if failures else 'pass',
    'verified': verified,
    'failures': failures,
}, indent=2))
"
else
  if [ ${#VERIFIED[@]} -gt 0 ]; then
    echo "Verified deps: ${VERIFIED[*]}"
  fi
  if [ ${#FAILURES[@]} -gt 0 ]; then
    echo "FAILED — unverified deps: ${FAILURES[*]}"
    echo "These packages do not exist in the registry. Check for hallucinated package names."
    exit 1
  fi
  echo "All new dependencies verified."
fi

[ ${#FAILURES[@]} -eq 0 ] || exit 1
