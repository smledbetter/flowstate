# notegrep — Markdown Note Search

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
