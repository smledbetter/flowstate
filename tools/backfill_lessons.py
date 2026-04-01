#!/usr/bin/env python3
"""Backfill lessons from progress.md files across all Flowstate projects.

Usage:
    python3 tools/backfill_lessons.py [--db PATH] [--dry-run]

Scans ~/.flowstate/*/progress.md for Learnings sections and imports them
into the DuckDB lessons table. Deduplicates by word overlap (Jaccard > 0.7).
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. Run: pip install duckdb")
    sys.exit(1)

DEFAULT_DB = os.path.expanduser("~/.flowstate/flowstate.duckdb")
FLOWSTATE_DIR = os.path.expanduser("~/.flowstate")

# Category keywords for auto-classification
CATEGORY_PATTERNS = {
    "gate": ["lint", "swiftlint", "golangci", "ruff", "biome", "eslint", "clippy",
             "gate", "coverage", "format"],
    "framework": ["swift", "react", "svelte", "go ", "rust", "typescript", "python",
                  "spm", "npm", "cargo", "docker", "kubernetes", "api"],
    "testing": ["test", "mock", "fixture", "assert", "coverage", "spy", "stub",
                "@test", "vitest", "jest", "pytest"],
    "performance": ["cache", "buffer", "flush", "timeout", "latency", "memory",
                    "batch", "concurrent"],
    "convention": ["pattern", "prefer", "avoid", "always", "never", "must",
                   "should", "naming", "style", "convention"],
    "tooling": ["install", "simulator", "xcode", "brew", "pip", "tool",
                "command", "cli", "config"],
}


def classify_lesson(text):
    """Auto-classify a lesson into a category based on keyword matching."""
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return "convention"  # default


def jaccard(a, b):
    """Word-level Jaccard similarity."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def extract_learnings(progress_path):
    """Extract learning lines from a progress.md file."""
    with open(progress_path) as f:
        content = f.read()

    # Find the Learnings section
    match = re.search(r"^## Learnings\s*\n", content, re.MULTILINE)
    if not match:
        return []

    # Extract from Learnings heading to next heading or EOF
    start = match.end()
    next_heading = re.search(r"^## ", content[start:], re.MULTILINE)
    if next_heading:
        section = content[start:start + next_heading.start()]
    else:
        section = content[start:]

    learnings = []
    for line in section.strip().split("\n"):
        line = line.strip()
        if line.startswith("- "):
            text = line[2:].strip()
            if len(text) > 10:  # skip trivially short entries
                learnings.append(text)
    return learnings


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Backfill lessons from progress.md files")
    parser.add_argument("--db", default=DEFAULT_DB, help="DuckDB file path")
    parser.add_argument("--dry-run", action="store_true", help="Print lessons without writing")
    args = parser.parse_args()

    db_path = os.path.expanduser(args.db)
    if not args.dry_run and not os.path.exists(db_path):
        print(f"ERROR: DuckDB not found at {db_path}. Run migrate_to_duckdb.py first.")
        sys.exit(1)

    # Scan all projects
    all_lessons = []
    for project_dir in sorted(Path(FLOWSTATE_DIR).iterdir()):
        if not project_dir.is_dir():
            continue
        progress_path = project_dir / "progress.md"
        if not progress_path.exists():
            continue

        project = project_dir.name
        learnings = extract_learnings(str(progress_path))
        for text in learnings:
            category = classify_lesson(text)
            all_lessons.append({
                "text": text,
                "category": category,
                "source_project": project,
                "source_sprint": 0,  # backfill — exact sprint unknown
            })

    print(f"Found {len(all_lessons)} learnings across {len(set(l['source_project'] for l in all_lessons))} projects")

    if args.dry_run:
        for l in all_lessons:
            print(f"  [{l['category']:12s}] [{l['source_project']:15s}] {l['text'][:100]}")
        return

    # Insert with deduplication
    con = duckdb.connect(db_path)

    # Load existing lessons for dedup
    existing = con.execute("SELECT id, text FROM lessons WHERE status = 'active'").fetchall()

    inserted = 0
    deduped = 0
    for lesson in all_lessons:
        # Check for duplicates
        is_dup = False
        for eid, etext in existing:
            if jaccard(lesson["text"], etext) > 0.7:
                is_dup = True
                deduped += 1
                break
        if is_dup:
            continue

        con.execute(
            """INSERT INTO lessons (text, category, source_project, source_sprint)
               VALUES (?, ?, ?, ?)""",
            [lesson["text"], lesson["category"], lesson["source_project"], lesson["source_sprint"]],
        )
        # Add to existing for subsequent dedup checks
        lid = con.execute("SELECT MAX(id) FROM lessons").fetchone()[0]
        existing.append((lid, lesson["text"]))
        inserted += 1

    con.close()

    print(f"Inserted: {inserted}, Deduplicated: {deduped}")
    print(f"Total lessons in DB: {inserted + len([e for e in existing if e[0] is not None])}")


if __name__ == "__main__":
    main()
