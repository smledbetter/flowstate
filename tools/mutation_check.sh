#!/usr/bin/env bash
# Run mutation testing and report the mutation score.
# Usage: ./mutation_check.sh [--json]
# Auto-detects language from project files.
# This is a diagnostic tool, not a gate -- too expensive to run every sprint.

set -euo pipefail

JSON_OUTPUT=""
if [ "${1:-}" = "--json" ]; then
  JSON_OUTPUT="1"
  shift
fi

if [ -f "Cargo.toml" ]; then
  OUTPUT=$(cargo mutants --timeout 60 2>&1) || true
  echo "$OUTPUT"
  # Parse: "X mutants tested: Y missed, Z caught, W timeout"
  CAUGHT=$(echo "$OUTPUT" | grep -oE '[0-9]+ caught' | grep -oE '[0-9]+' || echo "0")
  MISSED=$(echo "$OUTPUT" | grep -oE '[0-9]+ missed' | grep -oE '[0-9]+' || echo "0")
  TOTAL=$((CAUGHT + MISSED))
  if [ "$TOTAL" -gt 0 ]; then
    SCORE=$(python3 -c "print(round($CAUGHT / $TOTAL * 100, 1))")
  else
    SCORE="0"
  fi
elif [ -f "package.json" ]; then
  OUTPUT=$(npx stryker run 2>&1) || true
  echo "$OUTPUT"
  # Parse: "Mutation score: XX.XX%"
  SCORE=$(echo "$OUTPUT" | grep -oE 'Mutation score: [0-9.]+' | grep -oE '[0-9.]+' || echo "0")
else
  echo "No supported project detected (need Cargo.toml or package.json)."
  exit 1
fi

if [ -n "$JSON_OUTPUT" ]; then
  echo "{\"mutation_score_pct\": $SCORE}"
else
  echo ""
  echo "Mutation score: ${SCORE}%"
fi
