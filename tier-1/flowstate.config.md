# Flowstate Configuration

## Quality Gates
- build_command: [e.g., npx tsc --noEmit, cargo build, go build ./...]
- lint_command: [e.g., npx tsc --noEmit --noUnusedLocals, cargo clippy -- -D warnings, golangci-lint run]
- test_command: [e.g., npx vitest --run, cargo test, go test ./...]
- coverage_command: [e.g., npx vitest --run --coverage, cargo tarpaulin]
- coverage_threshold: none (establish after Sprint 1)
- coverage_regression_gate: true — coverage % must be >= baseline
- custom_gates: []

## Agent Strategy
- model: opus
- default_strategy: bypass-permissions
- multi_agent: subagents for independent packages (no shared files)
- teams: 1200+ LOC new features with 3+ independent workstreams

## Notes
- Add project-specific notes here (pre-existing lint errors, excluded directories, etc.)
