# pipesmith — Schema-Driven ETL Pipeline

**One-liner:** Define data transformation pipelines in YAML, process CSV/JSON input through validation and column-level transforms, output to multiple formats.

**Stack:** Python 3.12+. Dependencies: PyYAML, jsonschema. Test: pytest + pytest-cov. Lint: ruff.

**Quality Gates:** `ruff check .` clean, `pytest` all pass, coverage >= 90%, no type errors (`pyright --project .`).

### Sprint 0 — Project Setup and Pipeline Schema
- Scaffold: pyproject.toml, src/pipesmith/, tests/, CLI entry point
- Define pipeline YAML schema: source (file path, format), steps (list of transforms), sink (file path, format)
- Pipeline schema validation with jsonschema (reject invalid pipelines before execution)
- Pipeline loader: parse YAML, validate, return typed pipeline object
- **AC:** `pipesmith --help` prints usage, valid pipeline YAML loads, invalid YAML rejected with clear error, gates pass, 8+ tests
- **LOC:** ~350

### Sprint 1 — Sources and Sinks
- CSV source: configurable delimiter, headers, encoding, skip rows
- JSON source: array-of-objects, newline-delimited
- CSV sink: configurable delimiter, header row
- JSON sink: pretty or compact, array or NDJSON
- YAML sink: list of mappings
- Source/sink registry: extensible dict mapping format names to reader/writer classes
- **AC:** Read CSV and JSON, write CSV/JSON/YAML, round-trip preserves data, 25+ tests
- **LOC:** ~600

### Sprint 2 — Transform Steps
- Column transforms: rename, drop, select, reorder
- Value transforms: uppercase, lowercase, trim, replace (regex), default (fill nulls)
- Type coercion: to_int, to_float, to_date (with format string), to_bool
- Computed columns: concat (join multiple columns), split (split column into multiple), template (f-string style)
- Each transform is a class with validate() and apply() methods
- **AC:** Pipeline with mixed transforms produces correct output, type errors caught at validation, 45+ total tests
- **LOC:** ~700

### Sprint 3 — Validation Rules and Error Handling
- Row validation: required fields, type checks, regex patterns, min/max values, enum (allowed values)
- Validation modes: strict (fail on first error), lenient (collect errors, output valid rows), report (output all rows + error column)
- Validation summary: total rows, valid, invalid, errors by rule
- Pipeline error handling: source not found, schema mismatch, transform failure — all produce structured error messages
- Dry-run mode: `pipesmith run pipeline.yaml --dry-run` validates pipeline and samples first 5 rows without full execution
- **AC:** Validation catches bad data, lenient mode outputs partial results, dry-run works, 60+ total tests
- **LOC:** ~700

### Sprint 4 — Pipeline Composition and CLI Polish
- Pipeline chaining: output of one pipeline feeds into another via `chain` keyword in YAML
- Conditional steps: `when` clause on transforms (apply only if column matches condition)
- Variables in pipeline YAML: `${INPUT_FILE}` resolved from CLI args (`--var INPUT_FILE=data.csv`)
- `pipesmith validate pipeline.yaml` checks schema without running
- `pipesmith describe pipeline.yaml` prints human-readable pipeline summary (sources, N steps, sinks)
- Verbose mode: `--verbose` logs each step with row counts and timing
- **AC:** Chained pipelines execute in sequence, conditionals apply selectively, variables resolve, describe outputs summary, all gates green, 75+ total tests
- **LOC:** ~650

**Total estimated LOC:** ~3000 (including tests)

---
