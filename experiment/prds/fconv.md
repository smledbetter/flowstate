# fconv — File Format Converter CLI

**One-liner:** Read CSV/JSON/YAML/TOML files, validate against user-defined schemas, transform between formats with streaming support and error recovery.

**Stack:** Python 3.12+. Dependencies: PyYAML, tomli/tomllib, jsonschema. Test: pytest + pytest-cov. Lint: ruff.

**Quality Gates:** `ruff check .` clean, `pytest` all pass, coverage >= 90%, no type errors (`pyright --project .`).

### Sprint 0 — Project Setup and Schema Design
- Scaffold project: pyproject.toml, src/fconv/, tests/, CLI entry point with argparse
- Define internal data model (records as list-of-dicts, metadata envelope)
- Set up gates: ruff, pyright, pytest with coverage
- Write schema spec: JSON Schema subset for column types (string, int, float, bool, date, email, url) with required/optional
- **AC:** `fconv --help` prints usage, gates pass, 5+ tests for project structure
- **LOC:** ~300

### Sprint 1 — Core Parsers (CSV, JSON)
- CSV reader: handle headers, quoting, custom delimiters, encoding detection (utf-8/latin-1)
- JSON reader: array-of-objects and newline-delimited JSON (NDJSON)
- CSV writer: proper quoting, configurable delimiter
- JSON writer: pretty-print and compact modes
- Round-trip tests: CSV -> internal -> CSV, JSON -> internal -> JSON
- **AC:** `fconv input.csv -o output.json` works, round-trip preserves data, 20+ tests
- **LOC:** ~600

### Sprint 2 — YAML/TOML Parsers and Schema Validation
- YAML reader/writer (multi-document support)
- TOML reader/writer
- Schema validation engine: load schema from .json file, validate each record, collect all errors (not fail-fast)
- Validation report: row number, column, expected type, actual value
- **AC:** All 4 formats read/write correctly, schema validation catches type mismatches, 35+ total tests
- **LOC:** ~700

### Sprint 3 — Transforms and Column Operations
- Column select/rename/reorder via CLI flags
- Type coercion: string-to-int, string-to-date, etc.
- Computed columns: simple expressions (concat, split, upper, lower, trim)
- Filter rows by column value (equality, contains, regex)
- **AC:** `fconv input.csv -o output.json --select name,age --rename age=years --filter "age>30"` works, 50+ total tests
- **LOC:** ~700

### Sprint 4 — Streaming Mode and Error Recovery
- Streaming mode for large files: process row-by-row without loading entire file, activated by `--stream` flag
- Memory-bounded: configurable batch size (default 1000 rows)
- Error recovery: `--on-error skip|stop|collect` flag. Skip writes partial output, collect appends errors to stderr summary
- Progress indicator to stderr (row count, errors so far)
- Final integration tests: 100K row CSV through full pipeline
- **AC:** Streaming processes files larger than available memory (tested with generated data), error recovery produces valid partial output, 65+ total tests, all gates green
- **LOC:** ~700

**Total estimated LOC:** ~3000 (including tests)

---
