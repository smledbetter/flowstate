# pollster — Poll and Vote System (Extended)

**One-liner:** Create polls with multiple question types, collect votes with token-based deduplication, view live results, all backed by SQLite with both CLI and REST API access.

**Stack:** Python 3.12+. Dependencies: FastAPI, uvicorn, SQLite (stdlib). Test: pytest + pytest-cov + httpx (async test client). Lint: ruff. Type check: pyright.

**Quality Gates:** `python3 -m ruff check .` clean, `python3 -m ruff format --check .` clean, `python3 -m pyright --project .` clean, `python3 -m pytest --tb=short -q --cov=src/pollster --cov-report=term-missing --cov-fail-under=90`.

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

### Sprint 3 — Results Aggregation
- API: GET /polls/:id/results returns aggregated results per question
- Single choice: option counts and percentages
- Multi choice: option counts (each voter can select multiple)
- Ranked: Borda count scoring (first choice gets N points, second gets N-1, etc.)
- Freetext: list of all responses (no aggregation)
- CLI: `pollster results POLL_ID` with formatted table output
- Results respect poll status: open polls show partial results, closed polls are final
- **AC:** All 4 question types aggregate correctly, Borda count is correct, CLI displays formatted results, 55+ total tests
- **LOC:** ~600

### Sprint 4 — Real-Time Results (SSE)
- Server-Sent Events endpoint: GET /polls/:id/results/stream
- On each new vote, push updated results to all connected clients
- CLI: `pollster watch POLL_ID` connects to SSE stream, live-updates terminal display
- Connection management: track active SSE connections, clean up on disconnect
- Heartbeat: send keepalive comment every 15s to detect stale connections
- Graceful shutdown: close all SSE connections on SIGTERM
- **AC:** SSE delivers updates within 1s of vote, CLI live display updates, heartbeat keeps connections alive, graceful shutdown works, 70+ total tests
- **LOC:** ~650

### Sprint 5 — Poll Templates and Bulk Creation
- `pollster template save POLL_ID --name "team-retro"` saves poll structure (no votes) as reusable template
- `pollster template list`, `pollster template use "team-retro"` creates new poll from template
- Templates stored in SQLite (templates table: id, name, structure JSON, created_at)
- API: POST /templates, GET /templates, POST /templates/:id/instantiate
- Bulk creation: `pollster bulk-create --template "team-retro" --count 5 --prefix "Week"` creates "Week 1", "Week 2", etc.
- Template variables: `{date}`, `{n}` placeholders in title/description, resolved at creation
- **AC:** Templates save/load correctly, bulk creates N polls, variables resolve, 85+ total tests
- **LOC:** ~600

### Sprint 6 — Export and Import
- Export: `pollster export POLL_ID --format json|csv` exports poll structure + all votes
- JSON export: full poll with questions, options, all votes, results
- CSV export: one row per vote (columns: voter_token, question, response, timestamp)
- Import: `pollster import file.json` recreates poll with votes (new IDs)
- Bulk vote import: `pollster import-votes POLL_ID --file votes.csv` (columns: token, question_index, response)
- Validation on import: reject malformed data with clear error messages, line numbers for CSV errors
- **AC:** Export/import round-trips, CSV matches schema, bulk import validates all rows, error messages reference line numbers, 100+ total tests
- **LOC:** ~650

### Sprint 7 — Advanced Question Types
- Matrix question: grid of rows (statements) x columns (scale), e.g., satisfaction survey
- Net Promoter Score (NPS): 0-10 scale with automatic promoter/passive/detractor classification
- Conditional questions: show question B only if question A answer matches condition
- Question ordering: randomize option order per voter (stored with seed for reproducibility)
- Schema migration: add matrix_config and nps_config columns, version table bump
- **AC:** Matrix captures grid responses, NPS calculates score correctly, conditionals skip/show as configured, randomization is reproducible, 120+ total tests
- **LOC:** ~750

### Sprint 8 — Rate Limiting and Abuse Prevention
- Rate limiting middleware: max 60 requests/minute per IP (sliding window in SQLite)
- Vote flood protection: max 10 votes per minute per voter token
- Request validation: max poll title length (200), max options per question (20), max questions per poll (20)
- IP logging: store voter IP alongside vote for audit (optional, configurable)
- API key middleware: optional `--require-api-key` flag, keys stored in SQLite
- Abuse report: `pollster audit POLL_ID` shows vote timing patterns, flags suspicious activity
- **AC:** Rate limiting returns 429 with Retry-After header, flood protection works, validation limits enforced, audit detects rapid-fire votes, 135+ total tests
- **LOC:** ~700

### Sprint 9 — Analytics Dashboard
- `pollster analytics POLL_ID` shows detailed analysis
- Response rate over time (hourly/daily buckets)
- Cross-question correlation: which option-A voters also chose option-B
- Completion rate: how many voters answered all questions vs partial
- API: GET /polls/:id/analytics returns all analytics as JSON
- Time-series data: vote counts per hour, cumulative participation curve
- CLI table formatting: aligned columns, percentage bars, color-coded
- **AC:** Analytics calculations correct, time-series buckets accurate, correlation matrix valid, CLI formatting clean, 150+ total tests
- **LOC:** ~700

### Sprint 10 — Performance and Hardening
- Benchmark suite: measure API latency at 100, 1000, 10000 votes per poll
- Query optimization: add indexes for common query patterns, EXPLAIN ANALYZE validation
- Connection pooling: reuse SQLite connections across requests
- Comprehensive error handling: consistent JSON error format with code, message, details
- API documentation: OpenAPI schema auto-generated from FastAPI, validate against actual responses
- Edge case tests: empty polls, polls with no votes, expired polls, concurrent votes, max-size payloads
- `pollster stats` shows global stats: total polls, total votes, most active poll, avg response rate
- **AC:** P95 latency under 50ms at 10K votes, indexes reduce query time >2x, error format consistent, OpenAPI schema validates, all gates green, 165+ total tests
- **LOC:** ~650

**Total estimated LOC:** ~7000 (including tests)
