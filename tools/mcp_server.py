#!/usr/bin/env python3
"""Flowstate Metrics MCP Server.

A Model Context Protocol server that provides sprint metrics collection,
session log parsing, and proxied access to the centralized Flowstate API.

Local tools (stdio, need filesystem access):
  - list_sessions: List available Claude Code session logs for a project
  - collect_metrics: Parse JSONL session logs and return structured metrics
  - sprint_boundary: Find the commit timestamp boundary for --after filtering

Centralized tools (proxied to VPS HTTP API, fallback to local DuckDB):
  - import_sprint: Validate and import sprint JSON
  - query_metrics: Run read-only SQL against DuckDB
  - get_composite_score: Get composite score trend for a project
  - record_lesson: Record a cross-project learning
  - get_lessons: Retrieve cross-project lessons for a sprint
  - record_gate_failure: Log a gate failure with error details and fix
  - get_gate_failures: Retrieve recent gate failures for a project
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# --- Centralized API proxy ---

FLOWSTATE_API = os.environ.get("FLOWSTATE_API", "http://100.87.64.104:8071/api/flowstate")
FLOWSTATE_PIN = os.environ.get("FLOWSTATE_PIN", "1701")

_pin_hash = hashlib.sha256(FLOWSTATE_PIN.encode()).hexdigest() if FLOWSTATE_PIN else ""


def api_call(path, method="GET", data=None, params=None):
    """Call the centralized Flowstate API on VPS. Returns parsed JSON or raises."""
    url = f"{FLOWSTATE_API}{path}"
    if params:
        qs = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items() if v is not None)
        if qs:
            url = f"{url}?{qs}"
    headers = {"Content-Type": "application/json"}
    if _pin_hash:
        headers["Cookie"] = f"mc_auth={_pin_hash}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        try:
            return json.loads(error_body)
        except (json.JSONDecodeError, ValueError):
            raise RuntimeError(f"API error {e.code}: {error_body[:200]}")


def api_available():
    """Check if the centralized API is reachable."""
    try:
        api_call("/score", params={"last_n": "1"})
        return True
    except Exception:
        return False


# --- Local DuckDB fallback ---

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

DB_PATH = os.path.expanduser("~/.flowstate/flowstate.duckdb")


def get_db(read_only=False):
    """Get a local DuckDB connection. Raises if not available."""
    if not HAS_DUCKDB:
        raise RuntimeError("DuckDB not installed. Run: pip install duckdb")
    if not os.path.exists(DB_PATH):
        raise RuntimeError(f"DuckDB not found at {DB_PATH}. Run: python3 tools/migrate_to_duckdb.py")
    return duckdb.connect(DB_PATH, read_only=read_only)

# All logging goes to stderr (stdout is the JSON-RPC transport)
def log(msg):
    print(f"[flowstate-mcp] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 over stdio
# ---------------------------------------------------------------------------

SERVER_INFO = {
    "name": "flowstate",
    "version": "1.2.0",
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
        "description": "Validate and optionally import a sprint JSON file into sprints.json and DuckDB. Use dry_run=true to validate without writing.",
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
    {
        "name": "query_metrics",
        "description": "Run a read-only SQL query against the Flowstate DuckDB database. Returns results as JSON. Use sprint_analytics view for derived metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL query (SELECT only, no mutations)",
                },
            },
            "required": ["sql"],
        },
    },
    {
        "name": "get_composite_score",
        "description": "Get the composite score trend for a project (or all projects). Score is 0-1, higher is better, weighted: quality 40%, token efficiency 30%, time 15%, autonomy 15%.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project slug (optional, all projects if omitted)",
                },
                "last_n": {
                    "type": "integer",
                    "description": "Number of recent sprints to return (default 10)",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "record_lesson",
        "description": "Record a cross-project learning in DuckDB. Deduplicates by word overlap.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The lesson text (one clear, actionable sentence)",
                },
                "category": {
                    "type": "string",
                    "enum": ["gate", "framework", "testing", "performance", "convention", "tooling"],
                    "description": "Lesson category",
                },
                "source_project": {
                    "type": "string",
                    "description": "Project slug where this was learned",
                },
                "source_sprint": {
                    "type": "integer",
                    "description": "Sprint number where this was learned",
                },
            },
            "required": ["text", "category", "source_project", "source_sprint"],
        },
    },
    {
        "name": "get_lessons",
        "description": "Retrieve cross-project lessons ranked by confidence. Excludes lessons from the specified project (those are already in progress.md).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Current project slug (to exclude same-project lessons)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max lessons to return (default 15)",
                    "default": 15,
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter",
                },
            },
            "required": ["project"],
        },
    },
    {
        "name": "record_gate_failure",
        "description": "Log a gate failure with error details and the fix applied.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project slug"},
                "sprint": {"type": "integer", "description": "Sprint number"},
                "gate_type": {
                    "type": "string",
                    "enum": ["build", "lint", "test", "coverage"],
                    "description": "Type of gate that failed",
                },
                "error_summary": {
                    "type": "string",
                    "description": "One-line classification of the error",
                },
                "error_detail": {
                    "type": "string",
                    "description": "Full error text (optional, truncated to 2000 chars)",
                },
                "fix_applied": {
                    "type": "string",
                    "description": "What fixed the issue",
                },
            },
            "required": ["project", "sprint", "gate_type", "error_summary"],
        },
    },
    {
        "name": "get_gate_failures",
        "description": "Retrieve recent gate failures for a project, ordered by most recent first.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project slug"},
                "limit": {
                    "type": "integer",
                    "description": "Max failures to return (default 10)",
                    "default": 10,
                },
            },
            "required": ["project"],
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
    if os.path.abspath(import_path) != os.path.abspath(str(archive_path)):
        shutil.copy2(import_path, archive_path)

    result["imported"] = True
    result["sprint_count_after"] = len(data["sprints"])
    result["archived_to"] = str(archive_path)

    # Write to centralized API (best-effort, fallback to local DuckDB)
    score = _composite_score(m)
    result["composite_score"] = score
    try:
        api_result = api_call("/import", "POST", {"entry": entry, "dry_run": False})
        result["api"] = "written"
        result["api_score"] = api_result.get("composite_score")
    except Exception as e:
        result["api"] = f"unavailable: {e}"
        # Fallback to local DuckDB
        if HAS_DUCKDB and os.path.exists(DB_PATH):
            try:
                sys.path.insert(0, str(REPO_ROOT / "tools"))
                from migrate_to_duckdb import insert_sprint as db_insert
                con = duckdb.connect(DB_PATH)
                db_insert(con, entry)
                con.close()
                result["local_duckdb"] = "written (fallback)"
            except Exception as e2:
                result["local_duckdb"] = f"warning: {e2}"

    return result


# ---------------------------------------------------------------------------
# v1.2 Tools: DuckDB analytics, lessons, gate failures
# ---------------------------------------------------------------------------


def _composite_score(m):
    """Compute composite score from sprint metrics dict. Returns 0-1."""
    gates = m.get("gates_first_pass")
    quality = 1.0 if gates is True else (0.0 if gates is False else 0.5)

    nw = m.get("new_work_tokens")
    loc = m.get("loc_added") or 0
    if nw and loc > 0:
        token_score = max(0.0, 1.0 - ((nw / loc) / 1000))
    else:
        token_score = 0.5

    time_s = m.get("active_session_time_s")
    time_score = max(0.0, 1.0 - (time_s / 3600)) if time_s is not None else 0.5

    compressions = m.get("context_compressions") or 0
    autonomy = max(0.0, 1.0 - (compressions / 5))

    return round(0.40 * quality + 0.30 * token_score + 0.15 * time_score + 0.15 * autonomy, 4)


def tool_query_metrics(params):
    try:
        return api_call("/query", "POST", {"sql": params["sql"]})
    except Exception as e:
        log(f"API unavailable for query_metrics, falling back to local: {e}")
        sql = params["sql"].strip()
        first_word = re.split(r'\s+', sql.lstrip('( '))[0].upper()
        if first_word not in ("SELECT", "WITH", "EXPLAIN", "DESCRIBE", "SHOW"):
            return {"error": f"Only read-only queries allowed. Got: {first_word}"}
        con = get_db(read_only=True)
        try:
            result = con.execute(sql)
            cols = [d[0] for d in result.description]
            rows = result.fetchall()
            records = [dict(zip(cols, row)) for row in rows]
            return {"rows": records, "count": len(records), "_source": "local"}
        finally:
            con.close()


def tool_get_composite_score(params):
    try:
        p = {"last_n": str(params.get("last_n", 10))}
        if params.get("project"):
            p["project"] = params["project"]
        return api_call("/score", params=p)
    except Exception as e:
        log(f"API unavailable for get_composite_score, falling back to local: {e}")
        con = get_db(read_only=True)
        try:
            project = params.get("project")
            last_n = params.get("last_n", 10)
            if project:
                rows = con.execute(
                    "SELECT project, sprint, composite_score, gates_first_pass FROM sprints WHERE project = ? ORDER BY sprint DESC LIMIT ?",
                    [project, last_n],
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT project, sprint, composite_score, gates_first_pass FROM sprints ORDER BY imported_at DESC LIMIT ?",
                    [last_n],
                ).fetchall()
            cols = ["project", "sprint", "composite_score", "gates_first_pass"]
            records = [dict(zip(cols, row)) for row in rows]
            scores = [r["composite_score"] for r in records if r["composite_score"] is not None]
            return {"sprints": records, "summary": {"avg_score": round(sum(scores)/len(scores), 4) if scores else None, "count": len(records)}, "_source": "local"}
        finally:
            con.close()


def tool_record_lesson(params):
    try:
        return api_call("/lessons", "POST", {
            "text": params["text"],
            "category": params["category"],
            "source_project": params["source_project"],
            "source_sprint": params["source_sprint"],
        })
    except Exception as e:
        log(f"API unavailable for record_lesson, falling back to local: {e}")
        con = get_db()
        try:
            con.execute(
                "INSERT INTO lessons (text, category, source_project, source_sprint) VALUES (?, ?, ?, ?)",
                [params["text"], params["category"], params["source_project"], params["source_sprint"]],
            )
            lid = con.execute("SELECT MAX(id) FROM lessons").fetchone()[0]
            return {"recorded": True, "lesson_id": lid, "_source": "local"}
        finally:
            con.close()


def tool_get_lessons(params):
    try:
        p = {"project": params["project"], "limit": str(params.get("limit", 15))}
        if params.get("category"):
            p["category"] = params["category"]
        return api_call("/lessons", params=p)
    except Exception as e:
        log(f"API unavailable for get_lessons, falling back to local: {e}")
        con = get_db(read_only=True)
        try:
            rows = con.execute(
                "SELECT id, text, category, confidence, source_project, source_sprint, times_applied FROM lessons WHERE status = 'active' AND source_project != ? ORDER BY confidence DESC LIMIT ?",
                [params["project"], params.get("limit", 15)],
            ).fetchall()
            cols = ["id", "text", "category", "confidence", "source_project", "source_sprint", "times_applied"]
            return {"lessons": [dict(zip(cols, row)) for row in rows], "count": len(rows), "_source": "local"}
        finally:
            con.close()


def tool_record_gate_failure(params):
    try:
        return api_call("/gate-failures", "POST", {
            "project": params["project"],
            "sprint": params["sprint"],
            "gate_type": params["gate_type"],
            "error_summary": params["error_summary"],
            "error_detail": params.get("error_detail"),
            "fix_applied": params.get("fix_applied"),
        })
    except Exception as e:
        log(f"API unavailable for record_gate_failure, falling back to local: {e}")
        con = get_db()
        try:
            con.execute(
                "INSERT INTO gate_failures (project, sprint, gate_type, error_summary, error_detail, fix_applied) VALUES (?, ?, ?, ?, ?, ?)",
                [params["project"], params["sprint"], params["gate_type"], params["error_summary"],
                 (params.get("error_detail") or "")[:2000], params.get("fix_applied")],
            )
            gid = con.execute("SELECT MAX(id) FROM gate_failures").fetchone()[0]
            return {"recorded": True, "id": gid, "_source": "local"}
        finally:
            con.close()


def tool_get_gate_failures(params):
    try:
        return api_call("/gate-failures", params={"project": params["project"], "limit": str(params.get("limit", 10))})
    except Exception as e:
        log(f"API unavailable for get_gate_failures, falling back to local: {e}")
        con = get_db(read_only=True)
        try:
            rows = con.execute(
                "SELECT id, sprint, gate_type, error_summary, fix_applied, created_at FROM gate_failures WHERE project = ? ORDER BY created_at DESC LIMIT ?",
                [params["project"], params.get("limit", 10)],
            ).fetchall()
            cols = ["id", "sprint", "gate_type", "error_summary", "fix_applied", "created_at"]
            records = [dict(zip(cols, row)) for row in rows]
            for r in records:
                if r.get("created_at"):
                    r["created_at"] = str(r["created_at"])
            return {"failures": records, "_source": "local"}
        finally:
            con.close()


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

TOOL_HANDLERS = {
    "list_sessions": tool_list_sessions,
    "collect_metrics": tool_collect_metrics,
    "sprint_boundary": tool_sprint_boundary,
    "import_sprint": tool_import_sprint,
    "query_metrics": tool_query_metrics,
    "get_composite_score": tool_get_composite_score,
    "record_lesson": tool_record_lesson,
    "get_lessons": tool_get_lessons,
    "record_gate_failure": tool_record_gate_failure,
    "get_gate_failures": tool_get_gate_failures,
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
