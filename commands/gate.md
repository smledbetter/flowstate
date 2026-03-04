Run all quality gates in order. Stop on first failure.

1. Read `~/.flowstate/{SLUG}/flowstate.config.md` to get the current gate commands.
2. Run each gate in order (build/typecheck, lint, test, coverage).
3. If a gate fails: report the failure with exact error output, classify as REGRESSION (test existed before this sprint) or FEATURE (new test), and stop.
4. If all gates pass: report "All gates passed."

$ARGUMENTS
