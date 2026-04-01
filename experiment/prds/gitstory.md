# gitstory — Git Stats Dashboard

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
