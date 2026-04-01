# presskit — Static Site Generator

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
