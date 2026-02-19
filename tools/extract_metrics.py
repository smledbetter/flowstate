"""
Extract sprint metrics from Claude Code session logs.

Usage: python3 extract_metrics.py [--json] <project-dir> <start-ts> <end-ts>

Scans parent session JSONL files AND subagent logs at:
  ~/.claude/projects/{slug}/{session-id}/subagents/agent-*.jsonl

Deduplicates by message ID (streaming can log the same message multiple times).

With --json: outputs a JSON object matching sprints.json metrics schema.
Without --json: outputs human-readable text report (default).
"""

import glob
import json
import os
import sys
from datetime import datetime

args = sys.argv[1:]
json_output = False
if args and args[0] == "--json":
    json_output = True
    args = args[1:]

if len(args) < 3:
    print(
        "Usage: python3 extract_metrics.py [--json] <project-dir> <start-ts> <end-ts>",
        file=sys.stderr,
    )
    sys.exit(1)

project_dir = args[0]
start_ts = args[1]
end_ts = args[2]

project_slug = project_dir.replace("/", "-").replace(" ", "-")
log_dir = os.path.expanduser(f"~/.claude/projects/{project_slug}")

# Collect ALL jsonl files: parent sessions + subagent logs
all_logfiles = sorted(glob.glob(os.path.join(log_dir, "*.jsonl")))
all_logfiles += sorted(glob.glob(os.path.join(log_dir, "*/subagents/agent-*.jsonl")))

# Deduplicate by message ID — later events for same msg overwrite (cumulative usage)
msg_data = {}  # msg_id -> {usage, model, is_subagent}
spawns = 0
spawn_msgs = set()
timestamps = []

for lf in all_logfiles:
    is_subagent = "/subagents/" in lf
    try:
        f = open(lf)
    except OSError:
        continue
    for line in f:
        try:
            ev = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        ts = ev.get("timestamp", "")
        if ts < start_ts or ts > end_ts:
            continue
        timestamps.append(ts)
        if ev.get("type") == "assistant":
            msg = ev.get("message", {})
            mid = msg.get("id", ts)
            usage = msg.get("usage", {})
            model = msg.get("model", ev.get("model", "unknown"))
            # Always overwrite — later events have same or cumulative usage
            msg_data[mid] = {"usage": usage, "model": model, "is_subagent": is_subagent}
            # Count Task spawns (only from parent, only once per message)
            if not is_subagent and mid not in spawn_msgs:
                for block in msg.get("content", []):
                    if block.get("type") == "tool_use" and block.get("name") == "Task":
                        spawns += 1
                        spawn_msgs.add(mid)
                        break
    f.close()

if not timestamps:
    print("No events found in window!")
    sys.exit(1)

# Aggregate from deduplicated messages
total_input = 0
total_output = 0
total_cache_read = 0
total_cache_create = 0
model_stats = {}
orch_calls = 0
sub_calls = 0

for mid, data in msg_data.items():
    u = data["usage"]
    m = data["model"]
    inp = u.get("input_tokens", 0)
    out = u.get("output_tokens", 0)
    cr = u.get("cache_read_input_tokens", 0)
    cc = u.get("cache_creation_input_tokens", 0)
    total_input += inp
    total_output += out
    total_cache_read += cr
    total_cache_create += cc
    if data["is_subagent"]:
        sub_calls += 1
    else:
        orch_calls += 1
    if m not in model_stats:
        model_stats[m] = {"calls": 0, "gross": 0}
    model_stats[m]["calls"] += 1
    model_stats[m]["gross"] += inp + cr + cc + out

api_calls = len(msg_data)
gross_input = total_input + total_cache_read + total_cache_create
total_tokens = gross_input + total_output
new_work = total_output + total_cache_create
cache_pct = (total_cache_read / gross_input * 100) if gross_input > 0 else 0

timestamps.sort()
ts_list = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t in timestamps]
active_seconds = 0
for i in range(1, len(ts_list)):
    gap = (ts_list[i] - ts_list[i - 1]).total_seconds()
    if gap <= 60:
        active_seconds += gap
mins = int(active_seconds // 60)
secs = int(active_seconds % 60)


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n // 1_000}K"
    return str(n)


# Compute model percentages by tokens
model_pcts = {}
for m in model_stats:
    tok_pct = model_stats[m]["gross"] / total_tokens * 100 if total_tokens > 0 else 0
    model_pcts[m] = round(tok_pct, 1)

opus_pct = sum(v for k, v in model_pcts.items() if "opus" in k)
sonnet_pct = sum(v for k, v in model_pcts.items() if "sonnet" in k)
haiku_pct = sum(v for k, v in model_pcts.items() if "haiku" in k)

if json_output:
    result = {
        "active_session_time_s": int(active_seconds),
        "active_session_time_display": f"{mins}m {secs}s",
        "total_tokens": total_tokens,
        "total_tokens_display": fmt_tokens(total_tokens),
        "new_work_tokens": new_work,
        "new_work_tokens_display": fmt_tokens(new_work),
        "cache_hit_rate_pct": round(cache_pct, 1) if gross_input > 0 else None,
        "opus_pct": opus_pct,
        "sonnet_pct": sonnet_pct,
        "haiku_pct": haiku_pct,
        "subagents": spawns,
        "subagent_note": None,
        "api_calls": api_calls,
    }
    print(json.dumps(result, indent=2))
else:
    print(f"Time window: {timestamps[0]} to {timestamps[-1]}")
    print(f"Active session time: {mins}m {secs}s")
    print(
        f"API calls: {api_calls} ({orch_calls} orchestrator + {sub_calls} subagent, deduplicated)"
    )
    print(f"Total tokens: {total_tokens:,}")
    print(f"  Gross input: {gross_input:,}")
    print(f"    Non-cache: {total_input:,}")
    print(f"    Cache read: {total_cache_read:,}")
    print(f"    Cache create: {total_cache_create:,}")
    print(f"  Output: {total_output:,}")
    print(f"New-work tokens: {new_work:,}")
    print(f"Cache hit rate: {cache_pct:.1f}%")
    print(f"Subagent spawns: {spawns}")
    print()
    print("Model breakdown:")
    for m in sorted(model_stats.keys()):
        d = model_stats[m]
        c = d["calls"]
        pct = c / api_calls * 100
        tok_pct = d["gross"] / total_tokens * 100 if total_tokens > 0 else 0
        print(f"  {m}: {c} calls ({pct:.1f}%), {d['gross']:,} tokens ({tok_pct:.1f}%)")
