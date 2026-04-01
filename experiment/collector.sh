#!/usr/bin/env bash
# collector.sh — Collect metrics from a completed experiment build
#
# Usage:
#   ./collector.sh <product> <condition>
#   ./collector.sh --all           # collect all completed builds
#   ./collector.sh --summary       # print summary table
#
# Imports sprint metrics, checks lint activation logs, and writes results.

set -euo pipefail

EXPERIMENT_DIR="/home/dev/experiment"
FLOWSTATE_DIR="$HOME/.flowstate"
RESULTS_FILE="$(cd "$(dirname "$0")" && pwd)/results.json"

collect_build() {
    local product="$1"
    local condition="$2"
    local build_name="${product}-${condition}"
    local build_dir="${EXPERIMENT_DIR}/${build_name}"
    local fs_dir="${FLOWSTATE_DIR}/exp-${build_name}"

    if [ ! -d "$build_dir" ]; then
        echo "SKIP: $build_name (directory not found)"
        return
    fi

    echo "=== Collecting: $build_name ==="

    # Count sprints (by import JSONs)
    local sprint_count=0
    local import_files=()
    for f in "$fs_dir/metrics"/sprint-*-import.json; do
        [ -f "$f" ] && import_files+=("$f") && sprint_count=$((sprint_count + 1))
    done

    if [ $sprint_count -eq 0 ]; then
        echo "  No sprint imports found. Build may not be complete."
        return
    fi

    echo "  Sprints: $sprint_count"

    # Import each sprint (best-effort — skip already imported)
    for f in "${import_files[@]}"; do
        local sprint_num
        sprint_num=$(python3 -c "import json; print(json.load(open('$f'))['sprint'])")
        echo "  Importing sprint $sprint_num..."
        python3 -c "
import sys, json
sys.path.insert(0, '$(dirname "$0")/../tools')
from mcp_server import tool_import_sprint
r = tool_import_sprint({'import_json_path': '$f', 'dry_run': False})
if 'error' in r:
    print(f'    SKIP: {r.get(\"error\", r.get(\"detail\", \"unknown\"))}')
else:
    print(f'    OK: score={r.get(\"composite_score\", \"?\")}, api={r.get(\"api\", \"?\")}')" 2>/dev/null || echo "    WARN: import failed"
    done

    # Collect lint activation logs (conditions C, D, E)
    local lint_activated=0
    local lint_total=0
    for f in "$fs_dir/metrics"/sprint-*-lint-log.txt; do
        [ -f "$f" ] || continue
        lint_total=$((lint_total + 1))
        if grep -q "lint_activated: true" "$f" 2>/dev/null; then
            lint_activated=$((lint_activated + 1))
        fi
    done

    # Get final git stats
    local total_loc
    total_loc=$(cd "$build_dir" && git log --format= --numstat | awk '{s+=$1} END {print s+0}')
    local commit_count
    commit_count=$(cd "$build_dir" && git rev-list --count HEAD)

    echo "  Total LOC: $total_loc"
    echo "  Commits: $commit_count"
    if [ $lint_total -gt 0 ]; then
        echo "  Lint activated: $lint_activated/$lint_total sprints"
    fi

    # Write to results JSON (append)
    python3 << PYEOF
import json, os

results_file = "$RESULTS_FILE"
if os.path.exists(results_file):
    with open(results_file) as f:
        data = json.load(f)
else:
    data = {"builds": []}

# Remove existing entry for this build if any
data["builds"] = [b for b in data["builds"] if b.get("build_name") != "$build_name"]

data["builds"].append({
    "build_name": "$build_name",
    "product": "$product",
    "condition": "$condition",
    "sprint_count": $sprint_count,
    "total_loc": $total_loc,
    "commit_count": $commit_count,
    "lint_activated": $lint_activated,
    "lint_total": $lint_total,
})

with open(results_file, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

print(f"  Written to {results_file}")
PYEOF
}

print_summary() {
    if [ ! -f "$RESULTS_FILE" ]; then
        echo "No results file found. Run collector on builds first."
        return
    fi

    python3 << 'PYEOF'
import json
with open("RESULTS_FILE_PLACEHOLDER") as f:
    data = json.load(f)

builds = data.get("builds", [])
if not builds:
    print("No builds collected yet.")
    exit()

print(f"{'Build':<25s} {'Cond':>4s} {'Sprints':>7s} {'LOC':>6s} {'Lint':>8s}")
print("-" * 55)
for b in sorted(builds, key=lambda x: (x["product"], x["condition"])):
    lint = f"{b['lint_activated']}/{b['lint_total']}" if b['lint_total'] > 0 else "n/a"
    print(f"{b['build_name']:<25s} {b['condition']:>4s} {b['sprint_count']:>7d} {b['total_loc']:>6d} {lint:>8s}")
PYEOF
}

# Main
case "${1:-}" in
    --all)
        for dir in "$EXPERIMENT_DIR"/*/; do
            build_name=$(basename "$dir")
            product="${build_name%-*}"
            condition="${build_name##*-}"
            if [[ "$condition" =~ ^[a-e]$ ]]; then
                collect_build "$product" "$condition"
                echo ""
            fi
        done
        ;;
    --summary)
        print_summary
        ;;
    *)
        product="${1:?Usage: ./collector.sh <product> <condition> | --all | --summary}"
        condition="${2:?Usage: ./collector.sh <product> <condition>}"
        collect_build "$product" "$condition"
        ;;
esac
