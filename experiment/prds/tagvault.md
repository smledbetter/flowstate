# tagvault — Bookmark Manager

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
