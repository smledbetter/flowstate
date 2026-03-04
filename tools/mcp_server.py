#!/usr/bin/env python3
"""Flowstate Metrics MCP Server.

A Model Context Protocol server that provides sprint metrics collection,
session log parsing, and sprint data import for Flowstate projects.

Runs over stdio (JSON-RPC 2.0). Zero external dependencies — stdlib only.

Tools:
  - list_sessions: List available Claude Code session logs for a project
  - collect_metrics: Parse JSONL session logs and return structured metrics
  - sprint_boundary: Find the commit timestamp boundary for --after filtering
  - import_sprint: Validate and import sprint JSON into sprints.json
"""

import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# All logging goes to stderr (stdout is the JSON-RPC transport)
def log(msg):
    print(f"[flowstate-mcp] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 over stdio
# ---------------------------------------------------------------------------

SERVER_INFO = {
    "name": "flowstate",
    "version": "1.0.0",
}

TOOLS = [
    {
        "name": "list_sessions",
        "description": "List available Claude Code session logs for a project. Returns session IDs with timestamps and subagent counts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory (e.g. /home/dev/projects/my-app)",
                },
            },
            "required": ["project_path"],
        },
    },
    {
        "name": "collect_metrics",
        "description": "Parse Claude Code JSONL session logs and return structured sprint metrics (tokens, model mix, active time, delegation ratio, rework rate, etc.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory",
                },
                "session_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "One or more session IDs to analyze",
                },
                "after": {
                    "type": "string",
                    "description": "ISO timestamp — only count events after this time (for mid-session sprint starts)",
                },
            },
            "required": ["project_path", "session_ids"],
        },
    },
    {
        "name": "sprint_boundary",
        "description": "Find the git commit timestamp to use as the --after boundary for collect_metrics. Looks at recent commits and finds the one just before the current sprint's work.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to the project directory",
                },
                "sprint_marker": {
                    "type": "string",
                    "description": "A string to identify current sprint commits (e.g. 'M8', 'sprint 2'). The boundary is the last commit BEFORE any commit matching this marker.",
                },
            },
            "required": ["project_path"],
        },
    },
    {
        "name": "import_sprint",
        "description": "Validate and optionally import a sprint JSON file into sprints.json. Use dry_run=true to validate without writing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "import_json_path": {
                    "type": "string",
                    "description": "Path to the sprint import JSON file",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "If true, validate only without writing to sprints.json",
                    "default": True,
                },
            },
            "required": ["import_json_path"],
        },
    },
]


def send_response(id, result):
    msg = {"jsonrpc": "2.0", "id": id, "result": result}
    data = json.dumps(msg)
    sys.stdout.write(data + "\n")
    sys.stdout.flush()


def send_error(id, code, message):
    msg = {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}
    data = json.dumps(msg)
    sys.stdout.write(data + "\n")
    sys.stdout.flush()


def send_notification(method, params=None):
    msg = {"jsonrpc": "2.0", "method": method}
    if params:
        msg["params"] = params
    data = json.dumps(msg)
    sys.stdout.write(data + "\n")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent


def project_slug(project_path):
    """Convert project path to Claude Code's slug format."""
    return project_path.replace("/", "-").replace(" ", "-")


def find_log_dir(project_path):
    """Find the Claude Code log directory for a project."""
    slug = project_slug(project_path)
    log_dir = Path.home() / ".claude" / "projects" / slug
    if not log_dir.is_dir():
        raise FileNotFoundError(f"No Claude Code session logs at {log_dir}")
    return log_dir


def parse_iso(ts_str):
    """Parse ISO timestamp string to datetime."""
    if not ts_str:
        return None
    ts = ts_str.replace("Z", "+00:00")
    # Python 3.9 compat: fromisoformat doesn't handle all ISO formats
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n // 1_000}K"
    return str(n)


# ---------------------------------------------------------------------------
# Tool: list_sessions
# ---------------------------------------------------------------------------

def tool_list_sessions(params):
    project_path = params["project_path"]
    log_dir = find_log_dir(project_path)

    sessions = []
    for f in sorted(log_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
        sid = f.stem
        # Skip if it looks like a subdir name
        if (log_dir / sid).is_dir():
            pass  # still list the session

        first_ts = None
        last_ts = None
        entry_count = 0
        subagent_count = 0

        with open(f) as fp:
            for line in fp:
                entry_count += 1
                try:
                    d = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                ts = d.get("timestamp")
                if ts:
                    if first_ts is None:
                        first_ts = ts
                    last_ts = ts

        # Count subagent logs
        sub_dir = log_dir / sid / "subagents"
        if sub_dir.is_dir():
            subagent_count = len(list(sub_dir.glob("*.jsonl")))

        sessions.append({
            "session_id": sid,
            "start": first_ts,
            "end": last_ts,
            "entry_count": entry_count,
            "subagent_count": subagent_count,
        })

    return sessions


# ---------------------------------------------------------------------------
# Tool: collect_metrics
# ---------------------------------------------------------------------------

IDLE_THRESHOLD = 60  # seconds

def tool_collect_metrics(params):
    project_path = params["project_path"]
    session_ids = params["session_ids"]
    after_ts = params.get("after")

    log_dir = find_log_dir(project_path)

    after_dt = parse_iso(after_ts) if after_ts else None

    # Gather all log files (parent + subagents)
    logfiles = []
    for sid in session_ids:
        parent = log_dir / f"{sid}.jsonl"
        if parent.exists():
            logfiles.append((str(parent), False))
        else:
            return {"error": f"Session log not found: {parent}"}

        sub_dir = log_dir / sid / "subagents"
        if sub_dir.is_dir():
            for sf in sub_dir.glob("*.jsonl"):
                logfiles.append((str(sf), True))

    # Parse all logs
    msg_data = {}  # msg_id -> {usage, model, is_subagent}
    spawn_msgs = set()
    spawn_count = 0
    compact_count = 0
    parent_timestamps = []
    edit_counts = defaultdict(int)
    tool_use_counts = defaultdict(int)
    files_edited = set()
    subagent_details = {}  # agent_id -> {model, tokens, first_ts, last_ts}

    for logfile, is_sub in logfiles:
        agent_id = None
        if is_sub:
            # Extract agent ID from filename: agent-{id}.jsonl
            fname = Path(logfile).stem
            if fname.startswith("agent-"):
                agent_id = fname[6:]

        with open(logfile) as fp:
            for line in fp:
                try:
                    d = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                ts_str = d.get("timestamp")
                if not ts_str:
                    continue

                # Filter by --after
                if after_dt:
                    event_dt = parse_iso(ts_str)
                    if event_dt and event_dt < after_dt:
                        continue

                # Parent timestamps for active time
                if not is_sub:
                    parent_timestamps.append(ts_str)

                # Context compression
                if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
                    if not is_sub:
                        compact_count += 1

                # Assistant messages
                if d.get("type") == "assistant":
                    msg = d.get("message", {})
                    mid = msg.get("id", ts_str)
                    usage = msg.get("usage", {})
                    model = msg.get("model", "unknown")

                    msg_data[mid] = {
                        "usage": usage,
                        "model": model,
                        "is_subagent": is_sub,
                    }

                    # Track subagent details
                    if is_sub and agent_id:
                        inp = usage.get("input_tokens", 0)
                        out = usage.get("output_tokens", 0)
                        cr = usage.get("cache_read_input_tokens", 0)
                        cc = usage.get("cache_creation_input_tokens", 0)
                        msg_total = inp + out + cr + cc
                        if agent_id not in subagent_details:
                            subagent_details[agent_id] = {
                                "model": model.split("-")[1] if "-" in model else model,
                                "tokens": 0,
                                "first_ts": ts_str,
                                "last_ts": ts_str,
                            }
                        subagent_details[agent_id]["tokens"] += msg_total
                        subagent_details[agent_id]["last_ts"] = ts_str

                    # Spawn count
                    if not is_sub and mid not in spawn_msgs:
                        content_blocks = msg.get("content", [])
                        if isinstance(content_blocks, list):
                            for block in content_blocks:
                                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Task":
                                    spawn_count += 1
                                    spawn_msgs.add(mid)
                                    break

                    # Tool use counts + file edits
                    content_blocks = msg.get("content", [])
                    if isinstance(content_blocks, list):
                        for block in content_blocks:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                tool_name = block.get("name", "")
                                # Normalize MCP tool names
                                clean_name = tool_name
                                if "__" in tool_name:
                                    parts = tool_name.split("__")
                                    clean_name = parts[-1]
                                tool_use_counts[clean_name] += 1

                                if clean_name in ("Edit", "Write"):
                                    fp_val = block.get("input", {}).get("file_path", "")
                                    if fp_val:
                                        edit_counts[fp_val] += 1
                                        files_edited.add(fp_val)

    # Aggregate tokens
    input_tokens = 0
    output_tokens = 0
    cache_read = 0
    cache_creation = 0
    model_tokens = defaultdict(lambda: {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0})
    orchestrator_tokens = 0
    subagent_tokens = 0

    for mid, data in msg_data.items():
        usage = data["usage"]
        model = data["model"]
        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        cr = usage.get("cache_read_input_tokens", 0)
        cc = usage.get("cache_creation_input_tokens", 0)
        msg_total = inp + out + cr + cc

        input_tokens += inp
        output_tokens += out
        cache_read += cr
        cache_creation += cc

        model_tokens[model]["input"] += inp
        model_tokens[model]["output"] += out
        model_tokens[model]["cache_read"] += cr
        model_tokens[model]["cache_creation"] += cc

        if data["is_subagent"]:
            subagent_tokens += msg_total
        else:
            orchestrator_tokens += msg_total

    total = input_tokens + output_tokens + cache_read + cache_creation
    new_work = output_tokens + cache_creation
    cache_pct = round(cache_read / total * 100, 1) if total > 0 else None

    # Model percentages
    model_pcts = {}
    for model, counts in model_tokens.items():
        mtotal = counts["input"] + counts["output"] + counts["cache_read"] + counts["cache_creation"]
        model_pcts[model] = round(mtotal / total * 100, 1) if total > 0 else 0

    opus_pct = round(sum(v for k, v in model_pcts.items() if "opus" in k), 1)
    sonnet_pct = round(sum(v for k, v in model_pcts.items() if "sonnet" in k), 1)
    haiku_pct = round(sum(v for k, v in model_pcts.items() if "haiku" in k), 1)

    # Active session time
    parent_timestamps.sort()
    ts_objects = [parse_iso(t) for t in parent_timestamps]
    ts_objects = [t for t in ts_objects if t is not None]
    active_seconds = 0
    for i in range(1, len(ts_objects)):
        gap = (ts_objects[i] - ts_objects[i - 1]).total_seconds()
        if gap <= IDLE_THRESHOLD:
            active_seconds += gap
    active_seconds = int(active_seconds)
    active_mins = active_seconds // 60
    active_secs = active_seconds % 60

    # Rework rate
    total_edits = sum(edit_counts.values())
    unique_files = len(edit_counts)
    rework_rate = round(total_edits / unique_files, 1) if unique_files > 0 else None

    # Delegation ratio
    deleg_pct = round(subagent_tokens / total * 100, 1) if total > 0 and subagent_tokens > 0 else None

    # Subagent details list
    sub_list = []
    for aid, info in subagent_details.items():
        t1 = parse_iso(info["first_ts"])
        t2 = parse_iso(info["last_ts"])
        dur = int((t2 - t1).total_seconds()) if t1 and t2 else 0
        sub_list.append({
            "agent_id": aid,
            "model": info["model"],
            "tokens": info["tokens"],
            "duration_s": dur,
        })

    return {
        "active_session_time_s": active_seconds,
        "active_session_time_display": f"{active_mins}m {active_secs}s",
        "total_tokens": total,
        "total_tokens_display": fmt_tokens(total),
        "new_work_tokens": new_work,
        "new_work_tokens_display": fmt_tokens(new_work),
        "cache_hit_rate_pct": cache_pct,
        "opus_pct": opus_pct,
        "sonnet_pct": sonnet_pct,
        "haiku_pct": haiku_pct,
        "api_calls": len(msg_data),
        "subagents": spawn_count,
        "delegation_ratio_pct": deleg_pct,
        "orchestrator_tokens": orchestrator_tokens,
        "subagent_tokens": subagent_tokens,
        "context_compressions": compact_count,
        "rework_rate": rework_rate,
        "tool_use_counts": dict(tool_use_counts),
        "files_edited": sorted(files_edited),
        "subagent_details": sub_list,
    }


# ---------------------------------------------------------------------------
# Tool: sprint_boundary
# ---------------------------------------------------------------------------

def tool_sprint_boundary(params):
    project_path = params["project_path"]
    marker = params.get("sprint_marker")

    result = subprocess.run(
        ["git", "log", "--format=%aI|%H|%s", "-20"],
        cwd=project_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"error": f"git log failed: {result.stderr.strip()}"}

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({
                "timestamp": parts[0],
                "sha": parts[1][:7],
                "message": parts[2],
            })

    if not commits:
        return {"error": "No commits found"}

    # If marker provided, find the boundary
    if marker:
        marker_lower = marker.lower()
        # Find first commit matching the marker (most recent first)
        first_sprint_idx = None
        for i, c in enumerate(commits):
            if marker_lower in c["message"].lower():
                first_sprint_idx = i
        if first_sprint_idx is not None and first_sprint_idx + 1 < len(commits):
            boundary = commits[first_sprint_idx + 1]
            return {
                "boundary_timestamp": boundary["timestamp"],
                "boundary_commit": boundary["sha"],
                "boundary_message": boundary["message"],
                "sprint_commits": [c for c in commits[:first_sprint_idx + 1] if marker_lower in c["message"].lower()],
            }

    # No marker or no match — return recent commits for manual selection
    return {
        "recent_commits": commits[:10],
        "note": "No sprint_marker match found. Use a commit timestamp from this list as the 'after' parameter in collect_metrics.",
    }


# ---------------------------------------------------------------------------
# Tool: import_sprint
# ---------------------------------------------------------------------------

def tool_import_sprint(params):
    import_path = os.path.expanduser(params["import_json_path"])
    dry_run = params.get("dry_run", True)

    if not os.path.exists(import_path):
        return {"error": f"File not found: {import_path}"}

    with open(import_path) as f:
        entry = json.load(f)

    # Validate required fields
    required_fields = ["project", "sprint", "label", "phase", "metrics", "hypotheses"]
    missing = [fld for fld in required_fields if fld not in entry]
    if missing:
        return {"error": f"Missing required fields: {', '.join(missing)}"}

    required_metrics = [
        "active_session_time_s", "active_session_time_display",
        "total_tokens", "total_tokens_display",
        "new_work_tokens", "new_work_tokens_display",
        "opus_pct", "sonnet_pct", "haiku_pct",
        "subagents", "api_calls",
        "tests_total", "tests_added",
        "coverage_pct", "lint_errors",
        "gates_first_pass", "loc_added",
    ]
    missing_metrics = [fld for fld in required_metrics if fld not in entry["metrics"]]
    if missing_metrics:
        return {"error": f"Missing metrics fields: {', '.join(missing_metrics)}"}

    # Validate hypotheses against registry
    hyp_path = REPO_ROOT / "hypotheses.json"
    warnings = []
    if hyp_path.exists():
        with open(hyp_path) as f:
            hyp_registry = json.load(f)
        # hypotheses.json structure: {"hypotheses": {"H1": "name", ...}, "valid_results": [...]}
        valid_ids = set(hyp_registry.get("hypotheses", {}).keys())
        valid_results = hyp_registry.get("valid_results", [])

        for h in entry.get("hypotheses", []):
            hid = h.get("id")
            if hid and hid not in valid_ids:
                warnings.append(f"Unknown hypothesis ID: {hid}")
            result = h.get("result")
            if result and valid_results and result not in valid_results:
                warnings.append(f"{hid} result '{result}' not in valid results: {valid_results}")

    # Normalize common issues
    m = entry["metrics"]
    if m.get("gates_first_pass_note") == "":
        m["gates_first_pass_note"] = None
        warnings.append("gates_first_pass_note normalized '' to null")

    # Check for duplicate
    sprints_path = REPO_ROOT / "sprints.json"
    if not sprints_path.exists():
        return {"error": f"sprints.json not found at {sprints_path}"}

    with open(sprints_path) as f:
        data = json.load(f)

    existing = [
        s for s in data["sprints"]
        if s["project"] == entry["project"] and s["sprint"] == entry["sprint"]
    ]
    if existing:
        if dry_run:
            return {
                "valid": False,
                "error": f"{entry['project']} sprint {entry['sprint']} already exists in sprints.json",
                "warnings": warnings,
            }
        else:
            return {"error": f"{entry['project']} sprint {entry['sprint']} already exists in sprints.json"}

    result = {
        "valid": True,
        "warnings": warnings,
        "preview": {
            "project": entry["project"],
            "sprint": entry["sprint"],
            "label": entry["label"],
            "phase": entry["phase"],
            "tests": m.get("tests_total"),
            "loc": m.get("loc_added"),
            "hypotheses": len(entry.get("hypotheses", [])),
        },
    }

    if dry_run:
        result["sprint_count_current"] = len(data["sprints"])
        return result

    # Actually import
    data["sprints"].append(entry)
    with open(sprints_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    # Archive
    imports_dir = REPO_ROOT / "imports"
    imports_dir.mkdir(exist_ok=True)
    archive_name = f"{entry['project']}-sprint-{entry['sprint']}-import.json"
    archive_path = imports_dir / archive_name
    import shutil
    shutil.copy2(import_path, archive_path)

    result["imported"] = True
    result["sprint_count_after"] = len(data["sprints"])
    result["archived_to"] = str(archive_path)
    return result


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

TOOL_HANDLERS = {
    "list_sessions": tool_list_sessions,
    "collect_metrics": tool_collect_metrics,
    "sprint_boundary": tool_sprint_boundary,
    "import_sprint": tool_import_sprint,
}


def handle_tool_call(name, arguments):
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")
    try:
        result = handler(arguments)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]
    except FileNotFoundError as e:
        return [{"type": "text", "text": json.dumps({"error": str(e)})}]
    except Exception as e:
        return [{"type": "text", "text": json.dumps({"error": f"{type(e).__name__}: {str(e)}"})}]


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    log("Starting Flowstate Metrics MCP server")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            log(f"Invalid JSON: {line[:100]}")
            continue

        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            send_response(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            })

        elif method == "notifications/initialized":
            # Client notification, no response needed
            pass

        elif method == "tools/list":
            send_response(req_id, {"tools": TOOLS})

        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            content = handle_tool_call(name, arguments)
            send_response(req_id, {"content": content})

        elif method == "ping":
            send_response(req_id, {})

        elif req_id is not None:
            # Unknown method with an id — respond with method not found
            send_error(req_id, -32601, f"Method not found: {method}")

        # Notifications (no id) for unknown methods are silently ignored


if __name__ == "__main__":
    main()
