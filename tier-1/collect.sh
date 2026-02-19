#!/usr/bin/env bash
# Flowstate Sprint Metrics Collector
# Parses Claude Code JSONL session logs for sprint metrics.
#
# Usage: ./metrics/collect.sh [--json] [--after <ISO-timestamp>] <session-id> [session-id...]
#
# The script auto-detects the project log directory from your current working
# directory. It converts `pwd` to the Claude Code project slug format
# (e.g., /Users/foo/Sites/MyProject -> -Users-foo-Sites-MyProject).
#
# Options:
#   --json               Output JSON matching sprints.json metrics schema
#   --after <timestamp>  Only count events after this ISO timestamp.
#                        Use when a sprint started mid-session.
#
# Examples:
#   ./metrics/collect.sh abc123-def456
#   ./metrics/collect.sh --json abc123-def456
#   ./metrics/collect.sh --after 2026-02-18T03:20:00Z abc123-def456

set -euo pipefail

# Auto-detect project log directory from cwd
PROJECT_SLUG=$(pwd | sed 's|/|-|g; s| |-|g')
PROJECT_LOGS="$HOME/.claude/projects/$PROJECT_SLUG"

if [ ! -d "$PROJECT_LOGS" ]; then
  echo "ERROR: No Claude Code session logs found at $PROJECT_LOGS"
  echo "Make sure you're running this from the project root directory."
  exit 1
fi

AFTER_TS=""
JSON_OUTPUT=""

# Parse flags
if [ "${1:-}" = "--json" ]; then
  JSON_OUTPUT="1"
  shift
fi
if [ "${1:-}" = "--after" ]; then
  AFTER_TS="$2"
  shift 2
fi

if [ $# -eq 0 ]; then
  echo "Usage: $0 [--after <ISO-timestamp>] <session-id> [session-id...]"
  echo ""
  echo "Options:"
  echo "  --after <timestamp>  Only count events after this ISO timestamp"
  echo ""
  echo "Project logs: $PROJECT_LOGS"
  echo ""
  echo "Available sessions (most recent first):"
  ls -t "$PROJECT_LOGS"/*.jsonl 2>/dev/null | while read -r f; do
    sid=$(basename "$f" .jsonl)
    first_ts=$(head -1 "$f" | python3 -c "import sys,json; print(json.load(sys.stdin).get('timestamp','?'))" 2>/dev/null)
    last_ts=$(tail -1 "$f" | python3 -c "import sys,json; print(json.load(sys.stdin).get('timestamp','?'))" 2>/dev/null)
    echo "  $sid  ($first_ts -> $last_ts)"
  done | head -20
  exit 1
fi

SESSION_IDS=("$@")

if [ -z "$JSON_OUTPUT" ]; then
  echo "========================================"
  echo "  Flowstate Sprint Metrics Report"
  echo "========================================"
  if [ -n "$AFTER_TS" ]; then
    echo "  (filtered: events after $AFTER_TS)"
  fi
  echo ""
fi

# Collect all JSONL files (parent sessions + their subagents)
LOGFILES=()
for sid in "${SESSION_IDS[@]}"; do
  logfile="$PROJECT_LOGS/$sid.jsonl"
  if [ ! -f "$logfile" ]; then
    echo "WARNING: Session log not found: $logfile"
    continue
  fi
  LOGFILES+=("$logfile")
  # Include subagent session logs
  subdir="$PROJECT_LOGS/$sid/subagents"
  if [ -d "$subdir" ]; then
    for subfile in "$subdir"/*.jsonl; do
      [ -f "$subfile" ] && LOGFILES+=("$subfile")
    done
  fi
done

if [ ${#LOGFILES[@]} -eq 0 ]; then
  echo "ERROR: No valid session logs found."
  exit 1
fi

# --- ALL METRICS via single Python pass ---
python3 -c "
import json, sys
from collections import defaultdict
from datetime import datetime

json_output = True if '$JSON_OUTPUT' else False
after_ts = '$AFTER_TS' if '$AFTER_TS' else None
after_dt = None
if after_ts:
    after_dt = datetime.fromisoformat(after_ts.replace('Z', '+00:00'))

logfiles = sys.argv[1:]

# Per-session wall time
session_times = {}
is_subagent = {}

# Deduplicate by message ID (streaming can log same message multiple times)
# Later events for same msg overwrite — usage values are identical across dupes
msg_data = {}  # msg_id -> {usage, model, is_subagent}
spawn_msgs = set()  # msg_ids that contained a Task spawn

# Counts
spawn_count = 0
compact_count = 0  # context compression events
parent_timestamps = []  # all timestamps from parent sessions, for gap-summed active time
edit_counts = defaultdict(int)  # file_path -> number of Edit/Write operations

for logfile in logfiles:
    sid = logfile.rsplit('/', 1)[-1].replace('.jsonl', '')
    is_sub = '/subagents/' in logfile
    is_subagent[sid] = is_sub
    first_ts = None
    last_ts = None

    with open(logfile) as f:
        for line in f:
            try:
                d = json.loads(line)
            except:
                continue

            ts_str = d.get('timestamp')
            if not ts_str:
                continue

            # Filter by --after
            if after_dt:
                try:
                    event_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    if event_dt < after_dt:
                        continue
                except:
                    continue

            # Track wall time
            if first_ts is None:
                first_ts = ts_str
            last_ts = ts_str

            # Collect parent timestamps for gap-summed active time
            if not is_sub:
                parent_timestamps.append(ts_str)

            # Context compression events
            if d.get('type') == 'system' and d.get('subtype') == 'compact_boundary':
                if not is_sub:
                    compact_count += 1

            # Assistant messages: deduplicate by message ID
            if d.get('type') == 'assistant':
                msg = d.get('message', {})
                mid = msg.get('id', ts_str)
                usage = msg.get('usage', {})
                model = msg.get('model', 'unknown')
                # Always overwrite — later events for same msg have identical usage
                msg_data[mid] = {'usage': usage, 'model': model, 'is_subagent': is_sub}

                # Agent spawn count (only from parent sessions, once per message)
                if not is_sub and mid not in spawn_msgs:
                    content_blocks = msg.get('content', [])
                    if isinstance(content_blocks, list):
                        for block in content_blocks:
                            if isinstance(block, dict) and block.get('type') == 'tool_use' and block.get('name') == 'Task':
                                spawn_count += 1
                                spawn_msgs.add(mid)
                                break

                # Track file edit/write operations for rework rate
                content_blocks = msg.get('content', [])
                if isinstance(content_blocks, list):
                    for block in content_blocks:
                        if isinstance(block, dict) and block.get('type') == 'tool_use':
                            tool_name = block.get('name', '')
                            if tool_name in ('Edit', 'Write', 'mcp__acp__Edit', 'mcp__acp__Write'):
                                fp = block.get('input', {}).get('file_path', '')
                                if fp:
                                    edit_counts[fp] += 1

    if first_ts and last_ts:
        t1 = datetime.fromisoformat(first_ts.replace('Z', '+00:00'))
        t2 = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
        session_times[sid] = (t2 - t1).total_seconds()
    else:
        session_times[sid] = 0

# Aggregate from deduplicated messages
input_tokens = 0
output_tokens = 0
cache_read = 0
cache_creation = 0
model_tokens = defaultdict(lambda: {'input': 0, 'output': 0, 'cache_read': 0, 'cache_creation': 0})
api_count = len(msg_data)

orchestrator_tokens = 0
subagent_tokens = 0

for mid, data in msg_data.items():
    usage = data['usage']
    model = data['model']
    inp = usage.get('input_tokens', 0)
    out = usage.get('output_tokens', 0)
    cr = usage.get('cache_read_input_tokens', 0)
    cc = usage.get('cache_creation_input_tokens', 0)
    msg_total = inp + out + cr + cc
    input_tokens += inp
    output_tokens += out
    cache_read += cr
    cache_creation += cc
    model_tokens[model]['input'] += inp
    model_tokens[model]['output'] += out
    model_tokens[model]['cache_read'] += cr
    model_tokens[model]['cache_creation'] += cc
    if data['is_subagent']:
        subagent_tokens += msg_total
    else:
        orchestrator_tokens += msg_total

IDLE_THRESHOLD = 60  # seconds — gaps larger than this are counted as idle

# --- Output ---

# Compute wall time (needed by both JSON and text output)
parent_seconds = 0
sub_seconds = 0
parent_sessions = []
sub_sessions = []
for sid, secs in session_times.items():
    if is_subagent.get(sid, False):
        sub_sessions.append((sid, secs))
        sub_seconds += secs
    else:
        parent_sessions.append((sid, secs))
        parent_seconds += secs

# Compute shared values
total = input_tokens + output_tokens + cache_read + cache_creation
new_work_tokens = output_tokens + cache_creation
cache_pct = (cache_read / total * 100) if total > 0 else 0

# Model percentages by tokens
model_pcts = {}
for model, counts in model_tokens.items():
    mtotal = counts['input'] + counts['output'] + counts['cache_read'] + counts['cache_creation']
    model_pcts[model] = (mtotal / total * 100) if total > 0 else 0

opus_pct = round(sum(v for k, v in model_pcts.items() if 'opus' in k), 1)
sonnet_pct = round(sum(v for k, v in model_pcts.items() if 'sonnet' in k), 1)
haiku_pct = round(sum(v for k, v in model_pcts.items() if 'haiku' in k), 1)

def fmt_tokens(n):
    if n >= 1_000_000:
        return f'{n / 1_000_000:.1f}M'
    if n >= 1_000:
        return f'{n // 1_000}K'
    return str(n)

# Active session time: sum gaps <= threshold across all parent timestamps
# This correctly handles autonomous sessions where no human messages exist
parent_timestamps.sort()
ts_objects = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in parent_timestamps]
active_seconds = 0
for i in range(1, len(ts_objects)):
    gap = (ts_objects[i] - ts_objects[i-1]).total_seconds()
    if gap <= IDLE_THRESHOLD:
        active_seconds += gap
active_mins = int(active_seconds) // 60
active_secs = int(active_seconds) % 60

# Rework rate: total edits / unique files edited
total_edits = sum(edit_counts.values())
unique_files = len(edit_counts)
rework_rate = round(total_edits / unique_files, 1) if unique_files > 0 else None

if json_output:
    result = {
        'active_session_time_s': int(active_seconds),
        'active_session_time_display': f'{active_mins}m {active_secs}s',
        'total_tokens': total,
        'total_tokens_display': fmt_tokens(total),
        'new_work_tokens': new_work_tokens,
        'new_work_tokens_display': fmt_tokens(new_work_tokens),
        'cache_hit_rate_pct': round(cache_pct, 1) if total > 0 else None,
        'opus_pct': opus_pct,
        'sonnet_pct': sonnet_pct,
        'haiku_pct': haiku_pct,
        'subagents': spawn_count,
        'subagent_note': None,
        'api_calls': api_count,
        'rework_rate': rework_rate,
        'delegation_ratio_pct': round(subagent_tokens / total * 100, 1) if total > 0 and subagent_tokens > 0 else None,
        'orchestrator_tokens': orchestrator_tokens,
        'subagent_tokens': subagent_tokens,
        'context_compressions': compact_count,
    }
    print(json.dumps(result, indent=2))
    sys.exit(0)

print('## Wall Time')
print()

for sid, secs in parent_sessions:
    mins = int(secs) // 60
    s = int(secs) % 60
    print(f'  Parent session {sid[:8]}...: {mins}m {s}s')
print()

active_subs = [(sid, secs) for sid, secs in sub_sessions if secs > 0]
if active_subs:
    print(f'  Subagent sessions: {len(active_subs)}')
    for sid, secs in active_subs:
        mins = int(secs) // 60
        s = int(secs) % 60
        print(f'    {sid[:16]}...: {mins}m {s}s')
    print()

# Wall time = parent session duration (subagents run in parallel within it)
total_mins = int(parent_seconds) // 60
total_secs = int(parent_seconds) % 60
print(f'  WALL TIME: {total_mins}m {total_secs}s  (parent session duration)')

idle_seconds = parent_seconds - active_seconds
idle_mins = int(idle_seconds) // 60
idle_secs = int(idle_seconds) % 60
print(f'  Idle time: {idle_mins}m {idle_secs}s  (gaps > {IDLE_THRESHOLD}s between log entries)')
print(f'  ACTIVE TIME: {active_mins}m {active_secs}s  (sum of gaps <= {IDLE_THRESHOLD}s)')
print()

print('## Token Usage')
print()
total = input_tokens + output_tokens + cache_read + cache_creation
new_work = output_tokens + cache_creation
cache_pct = (cache_read / total * 100) if total > 0 else 0

print(f'  Input tokens:          {input_tokens:>12,}')
print(f'  Output tokens:         {output_tokens:>12,}')
print(f'  Cache read tokens:     {cache_read:>12,}')
print(f'  Cache creation tokens: {cache_creation:>12,}')
print(f'  -----------------------------------')
print(f'  Total tokens:          {total:>12,}')
print(f'  New-work tokens:       {new_work:>12,}  (output + cache_creation)')
print(f'  Cache hit rate:        {cache_pct:>11.1f}%')
print()

print('## Model Mix')
print()
for model, counts in sorted(model_tokens.items()):
    mtotal = counts['input'] + counts['output'] + counts['cache_read'] + counts['cache_creation']
    pct = (mtotal / total * 100) if total > 0 else 0
    print(f'  {model}: {mtotal:>12,} tokens ({pct:.1f}%)')
print()

print('## Agent Spawn Count')
print()
print(f'  Subagents spawned: {spawn_count}')
print()

print('## Context Efficiency')
print()
if subagent_tokens > 0:
    deleg_pct = subagent_tokens / total * 100
    print(f'  Orchestrator tokens: {orchestrator_tokens:>12,} ({orchestrator_tokens / total * 100:.1f}%)')
    print(f'  Subagent tokens:     {subagent_tokens:>12,} ({deleg_pct:.1f}%)')
    print(f'  Delegation ratio:    {deleg_pct:>11.1f}%  (higher = more work delegated)')
else:
    print(f'  Orchestrator tokens: {orchestrator_tokens:>12,} (100% — no subagents)')
    print(f'  Delegation ratio:          N/A  (single-agent sprint)')
print(f'  Context compressions:      {compact_count}  (0 = context fit comfortably)')
print()

print('## API Calls')
print()
print(f'  Total API calls: {api_count}')
print()
" "${LOGFILES[@]}"

if [ -z "$JSON_OUTPUT" ]; then
  echo "========================================"
  echo "  Run these manually:"
  echo "========================================"
  echo ""
  echo "  # LOC delta:"
  echo "  git diff --stat {start-sha}..HEAD"
  echo ""
  echo "  # Test count / coverage:"
  echo "  (use your project's test and coverage commands)"
  echo ""
fi
