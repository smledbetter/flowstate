# notegrep — Markdown Note Search (Extended)

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

### Sprint 2 — Full-Text Search Engine
- Full-text search: substring match on title and body, ranked by frequency
- Fuzzy search: fuse.js on title + first 200 chars of body, configurable threshold
- Tag search: `notegrep search --tag cooking` filters by tag (exact match)
- Combined queries: `notegrep search "recipe" --tag cooking --after 2024-01-01`
- Date range filter: --before, --after flags
- Output: list of matching files with title, path, match score, context snippet (30 chars around match)
- **AC:** Full-text finds exact matches, fuzzy finds typos, tag filter narrows results, date range works, 40+ total tests
- **LOC:** ~650

### Sprint 3 — Fuzzy Search and Result Ranking
- Weighted scoring: title matches worth 3x body matches, tag matches worth 2x
- BM25-style ranking for full-text results (term frequency, inverse document frequency)
- Highlight matched terms in context snippets (ANSI bold in CLI output)
- Search result deduplication (same note matched by multiple criteria)
- `notegrep search --sort relevance|date|title` sorting options
- Configurable results limit: `--limit N` (default 20)
- **AC:** Ranking prefers title matches, BM25 ordering is correct, highlights render, sort modes work, 55+ total tests
- **LOC:** ~600

### Sprint 4 — CLI Interface
- `notegrep search QUERY` with all filter flags
- `notegrep list` shows all indexed notes (paginated, sortable)
- `notegrep show FILE` prints note content with metadata header
- `notegrep tags` shows all tags with counts, sorted by frequency
- `notegrep stats` prints index summary (total notes, tags, avg word count, date range)
- Color output with chalk (auto-disabled when piped)
- `--json` flag on all commands for machine-readable output
- **AC:** All commands work, JSON output parses correctly, color disabled in pipes, 70+ total tests
- **LOC:** ~700

### Sprint 5 — TUI Results Browser
- Interactive TUI using Ink: list of search results with scrolling
- Preview pane: shows first 20 lines of selected note
- Open note: press Enter to print file path (for piping to editor), or press 'o' to open in $EDITOR
- Filter within results: type to narrow displayed results
- Keyboard shortcuts: j/k scroll, / to filter, q to quit, Tab to toggle preview
- Status bar: result count, current position, active filters
- **AC:** TUI renders search results, preview shows content, Enter outputs path, keyboard nav works, 85+ total tests
- **LOC:** ~700

### Sprint 6 — Backlinks and Graph
- Detect wiki-links `[[note-name]]` and markdown links `[text](path.md)` in note bodies
- `notegrep links FILE` shows outgoing and incoming links for a note
- `notegrep orphans` finds notes with no incoming links
- `notegrep graph` outputs DOT format dependency graph (pipe to graphviz)
- Backlink index stored alongside main index (rebuilt incrementally)
- Broken link detection: flag links pointing to non-existent notes
- **AC:** Both link syntaxes detected, orphans found, DOT output valid, broken links flagged, 100+ total tests
- **LOC:** ~650

### Sprint 7 — Boolean Queries and Advanced Filters
- Boolean operators: `notegrep search "recipe AND italian NOT pasta"`
- Parenthetical grouping: `"(recipe OR cookbook) AND italian"`
- Query parser: tokenize, parse to AST, evaluate against index
- Field-specific search: `title:recipe`, `tag:cooking`, `body:ingredients`
- Negation filter: `--exclude-tag draft` removes notes with specific tags
- Heading-level filter: `--heading "Introduction"` finds notes with matching headings
- **AC:** Boolean queries evaluate correctly, field-specific works, negation filters, parser handles edge cases, 120+ total tests
- **LOC:** ~750

### Sprint 8 — File Watching and Live Index
- `notegrep watch` monitors directory for file changes (fs.watch with debounce)
- On change: incrementally update index, log what changed
- Watch integrates with TUI: results auto-refresh when index updates
- Debounce: batch rapid changes (50ms window) to avoid thrashing
- Graceful shutdown on SIGINT/SIGTERM
- Ignore patterns: respect .gitignore plus .notegrepignore
- **AC:** Watch detects new/modified/deleted files, TUI refreshes, debounce batches correctly, graceful shutdown works, 135+ total tests
- **LOC:** ~600

### Sprint 9 — Export and Conversion
- `notegrep export --format json|csv|html QUERY` exports search results
- JSON export: full note metadata + body
- CSV export: path, title, tags (comma-joined), date, word count
- HTML export: rendered markdown with metadata table, search highlights preserved
- `notegrep report QUERY --template summary` generates a markdown report summarizing matched notes
- Template system: built-in templates (summary, table, full), custom templates from .notegreprc.yaml
- **AC:** All 3 export formats correct, HTML renders markdown, report templates work, 150+ total tests
- **LOC:** ~650

### Sprint 10 — Performance and Large Corpus Handling
- Benchmark suite: measure index build time and search latency at 100, 1000, 10000 notes
- Streaming index build: don't load entire corpus into memory
- Search result pagination: internal cursor-based pagination for large result sets
- Index compression: gzip the JSON index file, transparent decompress on load
- Parallel indexing: use worker_threads for CPU-bound frontmatter parsing
- Cache: LRU cache for recent searches (configurable size, invalidated on index update)
- **AC:** 10K note corpus indexes in <10s, search returns in <100ms, memory stays under 200MB, cache hit rate >50% on repeated queries, all gates green, 165+ total tests
- **LOC:** ~700

**Total estimated LOC:** ~6900 (including tests)
