# Flowstate v1.2 Experiment — Product PRDs

Eight self-contained products for the v1.2 factorial experiment. Each PRD is a complete build specification for an AI coding agent. All products follow Flowstate sprint conventions: gates are non-negotiable, one phase per sprint after Sprint 0.

---

## 1. fconv — File Format Converter CLI

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

## 2. presskit — Static Site Generator

**One-liner:** Transform a directory of Markdown files with YAML frontmatter into a themed HTML site using Handlebars templates, with asset copying and a live-reload dev server.

**Stack:** TypeScript 5+, Node 20+. Dependencies: marked (markdown), handlebars, gray-matter (frontmatter), chokidar (file watching), ws (websocket for live reload). Test: vitest. Lint: eslint + typescript-eslint.

**Quality Gates:** `npx tsc --noEmit` clean, `npx eslint .` clean, `npx vitest run` all pass, coverage >= 85%.

### Sprint 0 — Project Setup and Content Model
- Scaffold: package.json, tsconfig.json, src/, tests/, bin/presskit entry point
- Define content model: Page (title, date, tags, slug, template, body), SiteConfig (title, baseUrl, outputDir)
- Site config from `presskit.yaml` in project root
- Set up gates: tsc, eslint, vitest with coverage
- **AC:** `npx presskit --help` prints usage, gates pass, 5+ tests
- **LOC:** ~350

### Sprint 1 — Markdown Parsing and HTML Generation
- Parse markdown files from `content/` directory recursively
- Extract YAML frontmatter with gray-matter
- Convert markdown body to HTML with marked
- Default HTML template: page title, body, navigation list
- Write output to `dist/` directory preserving folder structure
- **AC:** `npx presskit build` generates HTML from markdown, frontmatter populates template variables, 20+ tests
- **LOC:** ~600

### Sprint 2 — Handlebars Templates and Layouts
- Template loading from `templates/` directory
- Layout system: base layout wraps page templates, `{{{body}}}` placeholder
- Partials: header, footer, nav loaded from `templates/partials/`
- Handlebars helpers: `formatDate`, `slugify`, `excerpt` (first N chars of body)
- Page-level template override via frontmatter `template: custom`
- **AC:** Custom templates render correctly, layouts wrap content, partials include, 35+ total tests
- **LOC:** ~650

### Sprint 3 — Asset Pipeline and Index Pages
- Copy static assets from `assets/` to `dist/assets/` (CSS, images, JS)
- Fingerprint assets: append content hash to filename for cache busting
- Auto-generate index pages: list of all pages sorted by date, grouped by tag
- Tag index pages: one page per tag listing tagged content
- RSS feed generation (valid XML, 20 most recent items)
- **AC:** Assets copied with fingerprinted names, index and tag pages generated, RSS validates, 50+ total tests
- **LOC:** ~700

### Sprint 4 — Dev Server with Live Reload
- HTTP server on localhost (configurable port, default 3000)
- Serve files from `dist/` directory
- File watcher on `content/`, `templates/`, `assets/` directories using chokidar
- On change: incremental rebuild (only changed files + dependents), notify browser via WebSocket
- Browser-injected script connects to WebSocket, triggers reload on message
- Graceful shutdown on SIGINT
- **AC:** `npx presskit serve` starts server, editing a markdown file triggers browser reload within 1 second, 60+ total tests
- **LOC:** ~700

### Sprint 5 — Polish, CLI Ergonomics, Edge Cases
- `presskit init` scaffolds a new site (creates content/, templates/, assets/ with example files)
- `presskit build --clean` removes dist/ before building
- `presskit build --drafts` includes frontmatter `draft: true` files
- Handle edge cases: missing frontmatter, empty files, broken markdown links (log warnings)
- Performance: skip unchanged files using mtime comparison
- **AC:** Init creates working scaffold, drafts flag works, edge cases produce warnings not crashes, all gates green, 75+ total tests
- **LOC:** ~500

**Total estimated LOC:** ~3500 (including tests)

---

## 3. tagvault — Bookmark Manager

**One-liner:** REST API over localhost with SQLite storage for bookmarks, supporting hierarchical tags, full-text search via FTS5, and import/export in multiple formats.

**Stack:** Go 1.22+. Dependencies: standard library + mattn/go-sqlite3 (CGo SQLite driver). Test: go test. Lint: golangci-lint.

**Quality Gates:** `go build ./...` clean, `golangci-lint run` clean, `go test ./...` all pass, coverage >= 85%.

### Sprint 0 — Project Setup and Data Model
- Scaffold: go.mod, cmd/tagvault/main.go, internal/ packages (store, api, model)
- SQLite schema: bookmarks (id, url, title, description, created_at, updated_at), tags (id, name, parent_id for hierarchy), bookmark_tags (junction table), FTS5 virtual table on title+description+url
- Database migration on startup (create tables if not exist)
- Set up gates: go build, golangci-lint, go test with coverage
- **AC:** Binary compiles, database initializes on first run, gates pass, 5+ tests
- **LOC:** ~400

### Sprint 1 — CRUD API for Bookmarks
- HTTP server on localhost (configurable port, default 8080)
- Endpoints: POST /bookmarks, GET /bookmarks/:id, PUT /bookmarks/:id, DELETE /bookmarks/:id, GET /bookmarks (list with pagination)
- Request/response as JSON
- Input validation: URL format, title required, max lengths
- Pagination: `?page=1&per_page=20`, response includes total count
- **AC:** All CRUD operations work via curl, validation rejects bad input with 400 status, pagination returns correct pages, 25+ tests
- **LOC:** ~700

### Sprint 2 — Hierarchical Tags
- Endpoints: POST /tags, GET /tags (tree structure), DELETE /tags/:id
- Assign tags to bookmarks: POST /bookmarks/:id/tags, DELETE /bookmarks/:id/tags/:tag_id
- Tag hierarchy: parent_id creates tree, GET /tags returns nested JSON
- Filter bookmarks by tag: GET /bookmarks?tag=name (includes child tags)
- Prevent circular parent references
- **AC:** Tags form tree, filtering by parent tag includes children, circular refs rejected, 40+ total tests
- **LOC:** ~600

### Sprint 3 — Full-Text Search
- FTS5 index on bookmark title, description, URL
- Search endpoint: GET /search?q=term with ranking by relevance
- Highlight matched terms in results (FTS5 snippet function)
- Combined filtering: search + tag filter simultaneously
- Search suggestions: GET /search/suggest?q=prefix returns top 5 title matches
- **AC:** Search returns relevant results ranked by score, highlights work, combined search+tag filters correctly, 55+ total tests
- **LOC:** ~500

### Sprint 4 — Import/Export and CLI
- Export: GET /export?format=json|csv|html (HTML as bookmarks.html compatible with browsers)
- Import: POST /import with JSON, CSV, or Netscape bookmarks.html format
- Deduplicate on import by URL (skip or update existing)
- CLI mode: `tagvault add URL`, `tagvault search TERM`, `tagvault export --format json` (calls API internally)
- CLI reads server address from config file or env var
- **AC:** Export/import round-trips without data loss, browser bookmarks.html imports correctly, CLI commands work, 70+ total tests
- **LOC:** ~700

### Sprint 5 — Polish and Performance
- Bulk operations: POST /bookmarks/bulk (create/update multiple), DELETE /bookmarks/bulk
- Bookmark health check: `tagvault check` validates URLs return 200 (concurrent, rate-limited) — test with localhost mock server only
- Database backup: `tagvault backup` copies SQLite file with WAL checkpoint
- Request logging middleware with structured JSON output
- Graceful shutdown with in-flight request draining
- **AC:** Bulk operations handle 100+ bookmarks, health check reports dead links, backup creates valid copy, all gates green, 85+ total tests
- **LOC:** ~600

**Total estimated LOC:** ~3500 (including tests)

---

## 4. ledgertui — Personal Finance TUI

**One-liner:** Terminal UI for tracking personal transactions with categories, running balances, monthly/yearly summary reports, and CSV import.

**Stack:** Rust (2021 edition). Dependencies: ratatui + crossterm (TUI), serde + serde_json (storage), chrono (dates), csv (import). Test: cargo test. Lint: cargo clippy.

**Quality Gates:** `cargo build` clean, `cargo clippy -- -D warnings` clean, `cargo test` all pass, coverage >= 80% (via cargo-tarpaulin or llvm-cov).

### Sprint 0 — Project Setup and Data Model
- Scaffold: Cargo.toml, src/main.rs, src/lib.rs, modules (model, store, tui, report)
- Data model: Transaction (id, date, amount_cents, description, category, account), Account (name, type: checking/savings/credit), Category (name, parent for hierarchy)
- JSON file storage: ledger.json in XDG data dir or current directory
- Set up gates: cargo build, clippy, test
- **AC:** Binary compiles, data model serializes/deserializes, gates pass, 8+ tests
- **LOC:** ~400

### Sprint 1 — TUI Framework and Transaction List
- Terminal UI with ratatui: full-screen layout with header, transaction list, status bar
- Transaction list: scrollable table with date, description, amount, category, running balance
- Color coding: green for income, red for expenses
- Keyboard navigation: j/k or arrow keys to scroll, q to quit
- Load/save transactions from JSON file on startup/exit
- **AC:** TUI renders transaction list, scrolling works, data persists between sessions, 20+ tests (logic tested without terminal)
- **LOC:** ~700

### Sprint 2 — Transaction Entry and Editing
- Add transaction: press 'a', modal form with fields (date, amount, description, category, account)
- Tab between fields, Enter to save, Esc to cancel
- Edit transaction: press 'e' on selected row, same form pre-populated
- Delete transaction: press 'd', confirmation prompt
- Input validation: date format (YYYY-MM-DD), amount as decimal (stored as cents), required fields
- Category autocomplete: type to filter existing categories
- **AC:** Add/edit/delete transactions via TUI, validation rejects bad input, autocomplete filters categories, 35+ total tests
- **LOC:** ~800

### Sprint 3 — Accounts and Categories
- Account management: press 'A' to switch to accounts view, add/edit/delete accounts
- Per-account transaction filtering: press 'f' to filter by account
- Category hierarchy: parent/child categories, display as "Food > Groceries"
- Category management screen: press 'C', add/rename/reparent/delete categories
- Transfer between accounts: press 't', creates paired transactions (debit + credit)
- **AC:** Multiple accounts with independent balances, category tree works, transfers balance correctly, 50+ total tests
- **LOC:** ~700

### Sprint 4 — Reports
- Monthly summary: press 'm', table showing income/expenses/net by category for selected month
- Yearly summary: press 'y', month-by-month bar chart (text-based) showing income vs expenses
- Category breakdown: pie-chart style percentage display per category
- Date range filter: press '/' to set custom date range for all views
- Export report to CSV: press 'x' from any report view
- **AC:** Monthly/yearly summaries compute correctly, bar chart renders, CSV export is valid, 65+ total tests
- **LOC:** ~700

### Sprint 5 — CSV Import and Polish
- CSV import: `ledgertui import file.csv` with column mapping (interactive prompt for which column is date, amount, etc.)
- Auto-detect common bank CSV formats (date formats, negative amounts as debits)
- Duplicate detection: skip transactions matching date+amount+description within same account
- Search transactions: press '/' in list view, fuzzy match on description
- Help overlay: press '?' to show all keybindings
- **AC:** CSV import handles 3+ date formats, duplicate detection works, search filters list, help displays, all gates green, 80+ total tests
- **LOC:** ~700

**Total estimated LOC:** ~4000 (including tests)

---

## 5. pipesmith — Schema-Driven ETL Pipeline

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

## 6. notegrep — Markdown Note Search

**One-liner:** Index a directory of Markdown files, extract tags and metadata from frontmatter, and search via full-text and fuzzy matching with a TUI results browser.

**Stack:** TypeScript 5+, Node 20+. Dependencies: gray-matter (frontmatter), fuse.js (fuzzy search), ink + ink-text-input (TUI via React-like components). Test: vitest. Lint: eslint + typescript-eslint.

**Quality Gates:** `npx tsc --noEmit` clean, `npx eslint .` clean, `npx vitest run` all pass, coverage >= 85%.

### Sprint 0 — Project Setup and Index Model
- Scaffold: package.json, tsconfig.json, src/, tests/, bin/notegrep entry point
- Define index model: NoteEntry (path, title, tags, date, headings, body text, word count)
- Index stored as JSON file (.notegrep-index.json) in target directory
- Set up gates: tsc, eslint, vitest with coverage
- **AC:** `npx notegrep --help` prints usage, gates pass, 5+ tests
- **LOC:** ~300

### Sprint 1 — File Indexing and Tag Extraction
- Recursively scan directory for .md files (configurable extensions, respect .gitignore)
- Parse YAML frontmatter: extract title, tags, date, custom fields
- Extract inline tags: #tag syntax within body text
- Extract headings (H1-H6) as structural metadata
- Incremental indexing: only re-index files modified since last index (mtime comparison)
- `notegrep index [dir]` builds/updates index
- **AC:** Index captures frontmatter tags, inline tags, headings, incremental re-index skips unchanged files, 20+ tests
- **LOC:** ~600

### Sprint 2 — Search Engine
- Full-text search: substring match on title and body, ranked by frequency
- Fuzzy search: fuse.js on title + first 200 chars of body, configurable threshold
- Tag search: `notegrep search --tag cooking` filters by tag (exact match)
- Combined queries: `notegrep search "recipe" --tag cooking --after 2024-01-01`
- Date range filter: --before, --after flags
- Output: list of matching files with title, path, match score, context snippet (30 chars around match)
- **AC:** Full-text finds exact matches, fuzzy finds typos, tag filter narrows results, date range works, 40+ total tests
- **LOC:** ~650

### Sprint 3 — TUI Results Browser
- Interactive TUI using Ink: list of search results with scrolling
- Preview pane: shows first 20 lines of selected note
- Open note: press Enter to print file path (for piping to editor), or press 'o' to open in $EDITOR
- Filter within results: type to narrow displayed results
- Tag cloud view: `notegrep tags` shows all tags with counts, select tag to search
- **AC:** TUI renders search results, preview shows content, Enter outputs path, tag cloud displays, 55+ total tests
- **LOC:** ~700

### Sprint 4 — Advanced Features and Polish
- Backlink detection: find notes that link to current note via `[[wiki-links]]` or `[markdown](links)`
- `notegrep links [file]` shows outgoing and incoming links for a note
- Orphan detection: `notegrep orphans` finds notes with no incoming links
- `notegrep stats` prints index summary (total notes, tags, avg word count, date range)
- Watch mode: `notegrep watch` re-indexes on file changes, keeps index fresh
- Config file: `.notegreprc.yaml` for default directory, ignored paths, custom tag patterns
- **AC:** Backlinks detected for both link syntaxes, orphan detection works, stats accurate, watch re-indexes on change, all gates green, 70+ total tests
- **LOC:** ~750

**Total estimated LOC:** ~3000 (including tests)

---

## 7. pollster — Poll and Vote System

**One-liner:** Create polls with multiple question types, collect votes with token-based deduplication, view live results, all backed by SQLite with both CLI and REST API access.

**Stack:** Python 3.12+. Dependencies: FastAPI, uvicorn, SQLite (stdlib). Test: pytest + pytest-cov + httpx (async test client). Lint: ruff.

**Quality Gates:** `ruff check .` clean, `pytest` all pass, coverage >= 90%, no type errors (`pyright --project .`).

### Sprint 0 — Project Setup and Data Model
- Scaffold: pyproject.toml, src/pollster/, tests/, CLI and API entry points
- SQLite schema: polls (id, title, description, created_at, closes_at, status), questions (id, poll_id, text, type: single_choice|multi_choice|ranked|freetext, options JSON), votes (id, question_id, voter_token, response JSON, created_at)
- Database init on startup, migrations via version table
- Set up gates: ruff, pyright, pytest with coverage
- **AC:** CLI and API print help/docs, database initializes, gates pass, 8+ tests
- **LOC:** ~400

### Sprint 1 — Poll CRUD (API + CLI)
- API: POST /polls (create), GET /polls (list), GET /polls/:id (detail), PUT /polls/:id (update), DELETE /polls/:id
- Question types: single_choice (radio), multi_choice (checkbox), ranked (order options), freetext
- CLI: `pollster create --title "Lunch?" --question "Where?" --options "Pizza,Sushi,Tacos" --type single_choice`
- CLI: `pollster list`, `pollster show POLL_ID`
- Poll lifecycle: draft -> open -> closed (manual or by closes_at timestamp)
- **AC:** Create polls with all 4 question types, lifecycle transitions work, CLI mirrors API, 25+ tests
- **LOC:** ~700

### Sprint 2 — Voting System
- API: POST /polls/:id/vote with voter_token and responses
- Voter token: opaque string provided by voter (no auth system, just dedup key)
- Deduplication: one vote per token per poll, second vote returns 409 Conflict
- Vote change: PUT /polls/:id/vote with same token updates previous vote
- Validation: response must match question type (single_choice gets one option, multi_choice gets array, ranked gets ordered array, freetext gets string)
- CLI: `pollster vote POLL_ID --token mytoken --response "Pizza"` (interactive mode for multi-question polls)
- **AC:** Votes recorded, dedup rejects duplicates, vote update works, validation catches mismatched types, 40+ total tests
- **LOC:** ~600

### Sprint 3 — Results and Analytics
- API: GET /polls/:id/results returns aggregated results per question
- Single choice: option counts and percentages
- Multi choice: option counts (each voter can select multiple)
- Ranked: Borda count scoring (first choice gets N points, second gets N-1, etc.)
- Freetext: list of all responses (no aggregation)
- CLI: `pollster results POLL_ID` with formatted table output
- Live results: results endpoint always reflects current votes (no caching)
- Results respect poll status: open polls show partial results, closed polls are final
- **AC:** All 4 question types aggregate correctly, Borda count is correct, CLI displays formatted results, 55+ total tests
- **LOC:** ~600

### Sprint 4 — Export, Import, and Templates
- Export: `pollster export POLL_ID --format json|csv` exports poll structure + all votes
- Import: `pollster import file.json` recreates poll with votes (new IDs)
- Poll templates: `pollster template save POLL_ID --name "team-retro"` saves poll structure (no votes) as reusable template
- `pollster template list`, `pollster template use "team-retro"` creates new poll from template
- Bulk vote import: `pollster import-votes POLL_ID --file votes.csv` (columns: token, question_index, response)
- **AC:** Export/import round-trips, templates create correct polls, bulk import validates all rows, 70+ total tests
- **LOC:** ~600

### Sprint 5 — Polish and Hardening
- Poll sharing: `pollster share POLL_ID` generates a one-line curl command for voting
- Rate limiting middleware: max 60 requests/minute per IP (in-memory counter, resets on restart)
- Request validation: max poll title length, max options per question (20), max questions per poll (10)
- API error responses: consistent JSON error format with code, message, details
- `pollster stats` shows global stats: total polls, total votes, most active poll
- Comprehensive edge case tests: empty polls, polls with no votes, expired polls, concurrent votes
- **AC:** Rate limiting works, validation limits enforced, error format consistent, stats accurate, all gates green, 85+ total tests
- **LOC:** ~500

**Total estimated LOC:** ~3400 (including tests)

---

## 8. gitstory — Git Stats Dashboard

**One-liner:** Parse git log output to compute contributor statistics, file hotspots, churn rates, and time-of-day patterns, then generate a self-contained HTML report.

**Stack:** Go 1.22+. Dependencies: standard library only (no external deps). Test: go test. Lint: golangci-lint.

**Quality Gates:** `go build ./...` clean, `golangci-lint run` clean, `go test ./...` all pass, coverage >= 85%.

### Sprint 0 — Project Setup and Git Log Parser
- Scaffold: go.mod, cmd/gitstory/main.go, internal/ packages (parser, stats, report)
- Git log parser: run `git log --format` with custom format, parse output into Commit structs (hash, author, date, message, files changed, insertions, deletions)
- Parse diff stats from `--numstat` output (file path, lines added, lines deleted per file per commit)
- Handle edge cases: merge commits, binary files, renames
- **AC:** Parser extracts commits with file-level stats from a real git repo, handles merge commits, gates pass, 10+ tests (using fixture data, not live git)
- **LOC:** ~450

### Sprint 1 — Contributor Statistics
- Per-author stats: total commits, lines added, lines deleted, net lines, first/last commit date, active days
- Author aliases: config file (.gitstory.yaml) mapping multiple emails to one author name
- Ranking: sort authors by commits, by net LOC, by active days
- Time range filter: `--since`, `--until` flags
- File type breakdown per author: lines by extension (.go, .ts, .py, etc.)
- **AC:** Author stats compute correctly, aliases merge authors, time filter works, extension breakdown accurate, 25+ tests
- **LOC:** ~600

### Sprint 2 — File Hotspots and Churn Analysis
- File hotspots: files ranked by number of commits touching them (most-changed files)
- Churn rate: lines added + lines deleted per file, normalized by file age
- Complexity proxy: files with high churn AND many authors = high coupling risk
- Directory-level aggregation: roll up file stats to directory level
- Ignore patterns: `--ignore "vendor/*,*.generated.go"` excludes files from analysis
- **AC:** Hotspots identify most-changed files, churn computes correctly, directory aggregation sums children, ignore patterns filter, 40+ total tests
- **LOC:** ~600

### Sprint 3 — Temporal Patterns
- Time-of-day heatmap: commits binned by hour (0-23) and day-of-week (Mon-Sun)
- Timezone handling: parse author timezone from git log, normalize or use `--timezone` flag
- Commit frequency: commits per week/month over project lifetime
- Sprint velocity proxy: LOC added per week, rolling 4-week average
- Streak detection: longest consecutive days with commits per author
- **AC:** Heatmap bins are correct, timezone normalization works, frequency tracks over time, streaks computed accurately, 55+ total tests
- **LOC:** ~550

### Sprint 4 — HTML Report Generation
- Self-contained HTML report: single file, inline CSS and SVG charts (no JavaScript dependencies)
- Sections: summary stats, contributor table, file hotspots table, churn table, time heatmap (SVG grid), commit frequency chart (SVG bar chart)
- SVG chart generation: bar charts, heatmap grid with color scaling, all generated in Go as SVG strings
- Color scheme: configurable via `--theme light|dark`
- Report header: repo name, date range, total commits/authors/files
- `gitstory report [path-to-repo] -o report.html`
- **AC:** HTML report renders in browser, all sections populated, SVG charts display correctly, light/dark themes work, 70+ total tests
- **LOC:** ~800

**Total estimated LOC:** ~3000 (including tests)
