#!/usr/bin/env bash
# mapgen.sh — Generate codebase map for the next sprint
#
# Usage: ./mapgen.sh <project-dir> <flowstate-dir> <sprint-number>
#
# Produces a compact (<80 line) codebase map with:
#   - File tree with one-line descriptions
#   - Module dependency graph
#   - Key patterns extracted from conventions
#   - Recent changes summary
#
# Supports: TypeScript, Python, Go, Rust

set -euo pipefail

PROJECT_DIR="${1:?Usage: mapgen.sh <project-dir> <flowstate-dir> <sprint-number>}"
FLOWSTATE_DIR="${2:?Usage: mapgen.sh <project-dir> <flowstate-dir> <sprint-number>}"
SPRINT_NUM="${3:?Usage: mapgen.sh <project-dir> <flowstate-dir> <sprint-number>}"
OUTPUT="$FLOWSTATE_DIR/codebase-map.md"
MAX_LINES=80

cd "$PROJECT_DIR"

# Detect stack
detect_stack() {
    if [ -f "tsconfig.json" ] || [ -f "package.json" ]; then
        echo "typescript"
    elif [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        echo "python"
    elif [ -f "go.mod" ]; then
        echo "go"
    elif [ -f "Cargo.toml" ]; then
        echo "rust"
    else
        echo "unknown"
    fi
}

STACK=$(detect_stack)

# --- File Tree with Descriptions ---

get_description_ts() {
    local file="$1"
    # First JSDoc comment or first // comment
    head -20 "$file" 2>/dev/null | grep -m1 -oP '(?<=/\*\*\s).*?(?=\s*\*/)' 2>/dev/null \
        || head -10 "$file" 2>/dev/null | grep -m1 -oP '(?<=//\s).*' 2>/dev/null \
        || echo ""
}

get_description_py() {
    local file="$1"
    # Module docstring (first triple-quoted string)
    python3 -c "
import ast, sys
try:
    with open('$file') as f:
        tree = ast.parse(f.read())
    doc = ast.get_docstring(tree)
    if doc:
        print(doc.split(chr(10))[0][:80])
except:
    pass
" 2>/dev/null || echo ""
}

get_description_go() {
    local file="$1"
    # Package comment
    head -20 "$file" 2>/dev/null | grep -m1 -oP '(?<=//\s).*' 2>/dev/null || echo ""
}

get_description_rust() {
    local file="$1"
    # Module doc comment (//!)
    head -20 "$file" 2>/dev/null | grep -m1 -oP '(?<=//!\s).*' 2>/dev/null || echo ""
}

generate_tree() {
    local src_pattern=""
    local test_pattern=""
    case "$STACK" in
        typescript) src_pattern="src/**/*.ts"; test_pattern="tests/**/*.ts" ;;
        python)     src_pattern="src/**/*.py"; test_pattern="tests/**/*.py" ;;
        go)         src_pattern="**/*.go"; test_pattern="" ;;  # tests are alongside source in Go
        rust)       src_pattern="src/**/*.rs"; test_pattern="tests/**/*.rs" ;;
        *)          src_pattern="src/**/*"; test_pattern="tests/**/*" ;;
    esac

    echo "## File Tree"
    echo ""

    # Source files
    local src_files
    src_files=$(find . -path "./$src_pattern" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" -not -path "*/.git/*" -type f 2>/dev/null | sort || true)

    if [ -n "$src_files" ]; then
        local current_dir=""
        while IFS= read -r file; do
            local rel="${file#./}"
            local dir
            dir=$(dirname "$rel")
            local base
            base=$(basename "$rel")

            # Print directory header if changed
            if [ "$dir" != "$current_dir" ]; then
                echo "${dir}/"
                current_dir="$dir"
            fi

            # Get description
            local desc=""
            case "$STACK" in
                typescript) desc=$(get_description_ts "$file") ;;
                python)     desc=$(get_description_py "$file") ;;
                go)         desc=$(get_description_go "$file") ;;
                rust)       desc=$(get_description_rust "$file") ;;
            esac

            if [ -n "$desc" ]; then
                printf "  %-28s — %s\n" "$base" "$desc"
            else
                printf "  %s\n" "$base"
            fi
        done <<< "$src_files"
    fi

    # Test summary (count per test file, not full listing)
    if [ -n "$test_pattern" ]; then
        echo ""
        local test_files
        test_files=$(find . -path "./$test_pattern" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" -type f 2>/dev/null | sort || true)
        if [ -n "$test_files" ]; then
            local test_count
            test_count=$(echo "$test_files" | wc -l | tr -d ' ')
            echo "tests/ ($test_count test files)"
        fi
    fi
}

# --- Dependencies ---

generate_deps_ts() {
    echo ""
    echo "## Module Dependencies"
    echo ""
    find . -path "./src/**/*.ts" -not -path "*/node_modules/*" -type f 2>/dev/null | sort | while IFS= read -r file; do
        local base
        base=$(basename "$file" .ts)
        local imports
        imports=$(grep -oP "from ['\"]\.\/(\w+)['\"]|from ['\"]\.\.\/(\w+)['\"]" "$file" 2>/dev/null | grep -oP "(?<=\.\/)\w+|(?<=\.\.\/)\w+" | sort -u | tr '\n' ', ' | sed 's/,$//')
        if [ -n "$imports" ]; then
            echo "$base -> $imports"
        fi
    done
}

generate_deps_py() {
    echo ""
    echo "## Module Dependencies"
    echo ""
    find . -path "./src/**/*.py" -not -name "__init__.py" -not -path "*/__pycache__/*" -type f 2>/dev/null | sort | while IFS= read -r file; do
        local base
        base=$(basename "$file" .py)
        # Find relative imports
        local imports
        imports=$(grep -oP "from \.\w* import|from \.(\w+)" "$file" 2>/dev/null | grep -oP "\.(\w+)" | sed 's/^\.//' | sort -u | tr '\n' ', ' | sed 's/,$//')
        if [ -n "$imports" ]; then
            echo "$base -> $imports"
        fi
    done
}

generate_deps_go() {
    echo ""
    echo "## Package Dependencies"
    echo ""
    find . -name "*.go" -not -name "*_test.go" -not -path "*/.git/*" -type f 2>/dev/null | sort | while IFS= read -r file; do
        local dir
        dir=$(dirname "$file")
        local pkg
        pkg=$(basename "$dir")
        local imports
        imports=$(grep -oP '"[^"]*internal/(\w+)"' "$file" 2>/dev/null | grep -oP 'internal/(\w+)' | sed 's/internal\///' | sort -u | tr '\n' ', ' | sed 's/,$//')
        if [ -n "$imports" ]; then
            echo "$pkg -> $imports"
        fi
    done | sort -u
}

generate_deps_rust() {
    echo ""
    echo "## Module Dependencies"
    echo ""
    find . -path "./src/**/*.rs" -type f 2>/dev/null | sort | while IFS= read -r file; do
        local base
        base=$(basename "$file" .rs)
        local imports
        imports=$(grep -oP "use crate::(\w+)" "$file" 2>/dev/null | sed 's/use crate:://' | sort -u | tr '\n' ', ' | sed 's/,$//')
        if [ -n "$imports" ]; then
            echo "$base -> $imports"
        fi
    done
}

# --- Key Patterns ---

generate_patterns() {
    echo ""
    echo "## Key Patterns"
    echo ""

    # Extract from CLAUDE.md conventions if exists
    if [ -f "CLAUDE.md" ]; then
        # Look for conventions section
        sed -n '/## Conventions/,/^## /p' CLAUDE.md 2>/dev/null | head -15 | grep -E '^\s*-' | head -5
    fi

    # Infer error handling pattern
    case "$STACK" in
        typescript)
            if grep -rq "extends.*Error" src/ 2>/dev/null; then
                echo "- Custom error classes (extends Error)"
            fi
            if grep -rq "async function\|async (" src/ 2>/dev/null; then
                echo "- Async/await throughout (no callbacks)"
            fi
            ;;
        python)
            if grep -rq "class.*Exception\|class.*Error" src/ 2>/dev/null; then
                echo "- Custom exception hierarchy"
            fi
            if grep -rq "async def" src/ 2>/dev/null; then
                echo "- Async handlers (FastAPI/asyncio)"
            fi
            ;;
    esac
}

# --- Recent Changes ---

generate_recent() {
    echo ""
    echo "## Recent Changes (sprint $SPRINT_NUM)"
    echo ""
    # Get stats from the last sprint's commit(s)
    local last_tag="sprint-${SPRINT_NUM}"
    # Use git log for last sprint's changes
    git log --oneline -5 2>/dev/null | while IFS= read -r line; do
        echo "- $line"
    done

    echo ""
    # Summary stats
    local tests_count coverage
    case "$STACK" in
        typescript)
            tests_count=$(grep -r "it(" tests/ src/ 2>/dev/null | wc -l | tr -d ' ' || echo "?")
            ;;
        python)
            tests_count=$(grep -r "def test_" tests/ 2>/dev/null | wc -l | tr -d ' ' || echo "?")
            ;;
        go)
            tests_count=$(grep -r "func Test" . --include="*_test.go" 2>/dev/null | wc -l | tr -d ' ' || echo "?")
            ;;
        rust)
            tests_count=$(grep -r "#\[test\]" . 2>/dev/null | wc -l | tr -d ' ' || echo "?")
            ;;
    esac
    local loc
    loc=$(find . -path "./src/*" -type f \( -name "*.ts" -o -name "*.py" -o -name "*.go" -o -name "*.rs" \) -not -path "*/node_modules/*" -not -path "*/__pycache__/*" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo "?")
    echo "~${tests_count} tests, ~${loc} LOC (source)"
}

# --- Assemble ---

{
    echo "# Codebase Map (auto-generated after sprint $SPRINT_NUM)"
    echo ""
    generate_tree
    case "$STACK" in
        typescript) generate_deps_ts ;;
        python)     generate_deps_py ;;
        go)         generate_deps_go ;;
        rust)       generate_deps_rust ;;
    esac
    generate_patterns
    generate_recent
} > "$OUTPUT.tmp"

# Truncate to MAX_LINES if needed
head -"$MAX_LINES" "$OUTPUT.tmp" > "$OUTPUT"
rm -f "$OUTPUT.tmp"

echo "Codebase map written to $OUTPUT ($(wc -l < "$OUTPUT") lines)"
