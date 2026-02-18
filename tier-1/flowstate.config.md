# Flowstate Configuration

## Quality Gates
- build_command: [e.g., npx tsc --noEmit, cargo build, go build ./...]
- test_command: [e.g., npx vitest --run, cargo test, go test ./...]
- lint_command: [e.g., npx tsc --noEmit --noUnusedLocals, cargo clippy -- -D warnings, golangci-lint run]
- coverage_command: [e.g., npx vitest --run --coverage, cargo tarpaulin]
- coverage_threshold: [e.g., 65% statements]
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
- Add project-specific notes here (pre-existing lint errors, excluded directories, etc.)
