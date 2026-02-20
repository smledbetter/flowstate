Import sprint data into the Flowstate repo.

If an argument is provided ($ARGUMENTS), use it as the explicit path to the import JSON file.

If no argument is provided, scan for unimported sprint JSONs:
1. List all `~/.flowstate/*/metrics/sprint-*-import.json` files
2. Read `sprints.json` to find which project+sprint combos already exist
3. Show the unimported files and ask which to import (or import all if only one)

For each file to import:
1. Validate: call `mcp__flowstate__import_sprint` with `dry_run=true`
2. If valid, import: call `mcp__flowstate__import_sprint` with `dry_run=false`
3. Report the result (sprint count before/after, any warnings)

After all imports:
4. Regenerate tables: `python3 tools/generate_tables.py` — show available subcommands and run the appropriate ones
5. Remind the human to paste updated tables into RESULTS.md if needed
6. If `dashboard/` exists, rebuild: `cd dashboard && npm run build` (skip if dashboard dir doesn't exist)

Report what was imported and any issues found.
