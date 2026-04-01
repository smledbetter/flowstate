# pollster — Poll and Vote System

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
