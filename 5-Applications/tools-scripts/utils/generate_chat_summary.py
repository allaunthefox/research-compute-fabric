#!/usr/bin/env python3
"""
Aggregate chat session summaries across Claude, Kimi, Copilot, and curated exports.
Outputs a single markdown file for this session's context ingestion.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = PROJECT_ROOT / "docs" / "chat_logs" / "MASTER_CHAT_SUMMARY.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iso_ts(ts: str) -> Optional[datetime]:
    try:
        # Handle Z suffix
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def unix_ts(ts: float) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        return None


def fmt_dt(dt: Optional[datetime]) -> str:
    return dt.strftime("%Y-%m-%d %H:%M UTC") if dt else "unknown"


def truncate(text: str, max_len: int = 300) -> str:
    text = text.replace("\n", " ")
    if len(text) > max_len:
        return text[:max_len] + " …"
    return text


def extract_file_paths(text: str) -> List[str]:
    # Simple heuristic for absolute or project-relative paths
    if not text:
        return []
    pattern = r"(?:/home/allaun/(?:Research Stack|Documents/Research Stack|\.claude|\.kimi)[^\s\"'`]+)"
    found = re.findall(pattern, text)
    return list(dict.fromkeys(found))[:10]


# ---------------------------------------------------------------------------
# Claude JSONL parser
# ---------------------------------------------------------------------------

def summarize_claude_jsonl(path: Path) -> Dict:
    stats = {
        "source": "Claude Code CLI",
        "path": str(path),
        "name": path.stem,
        "lines": 0,
        "user_msgs": 0,
        "assistant_msgs": 0,
        "tool_calls": 0,
        "attachments": 0,
        "first_dt": None,
        "last_dt": None,
        "topics": [],
        "tools": Counter(),
        "files": [],
    }
    file_mentions: List[str] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stats["lines"] += 1
            if stats["lines"] % 50_000 == 0:
                # progress heartbeat
                pass
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_raw = obj.get("timestamp") or obj.get("createdAt")
            dt = iso_ts(ts_raw) if isinstance(ts_raw, str) else None
            if dt:
                if stats["first_dt"] is None or dt < stats["first_dt"]:
                    stats["first_dt"] = dt
                if stats["last_dt"] is None or dt > stats["last_dt"]:
                    stats["last_dt"] = dt

            t = obj.get("type")
            if t == "user":
                stats["user_msgs"] += 1
                text = ""
                content = obj.get("message", {}).get("content", [])
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text += part.get("text", "")
                if text:
                    if len(stats["topics"]) < 5:
                        stats["topics"].append(truncate(text))
                    file_mentions.extend(extract_file_paths(text))
            elif t == "assistant":
                stats["assistant_msgs"] += 1
            elif t == "tool":
                stats["tool_calls"] += 1
                tool_name = obj.get("toolName") or obj.get("tool", {}).get("name") or "unknown"
                stats["tools"][tool_name] += 1
                # try to grab file paths from tool result
                res = obj.get("result") or obj.get("output") or {}
                if isinstance(res, str):
                    file_mentions.extend(extract_file_paths(res))
                elif isinstance(res, dict):
                    for v in res.values():
                        if isinstance(v, str):
                            file_mentions.extend(extract_file_paths(v))
            elif t == "attachment":
                stats["attachments"] += 1

    stats["files"] = list(dict.fromkeys(file_mentions))[:20]
    return stats


# ---------------------------------------------------------------------------
# Kimi wire JSONL parser
# ---------------------------------------------------------------------------

def summarize_kimi_wire(path: Path) -> Dict:
    stats = {
        "source": "Kimi Code CLI",
        "path": str(path),
        "name": path.parent.name,  # session UUID
        "lines": 0,
        "turns": 0,
        "tool_calls": 0,
        "first_dt": None,
        "last_dt": None,
        "topics": [],
        "tools": Counter(),
        "files": [],
    }
    file_mentions: List[str] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stats["lines"] += 1
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = obj.get("timestamp")
            dt = unix_ts(ts) if isinstance(ts, (int, float)) else None
            if dt:
                if stats["first_dt"] is None or dt < stats["first_dt"]:
                    stats["first_dt"] = dt
                if stats["last_dt"] is None or dt > stats["last_dt"]:
                    stats["last_dt"] = dt

            msg = obj.get("message", {})
            mtype = msg.get("type")
            payload = msg.get("payload", {})

            if mtype == "TurnBegin":
                stats["turns"] += 1
                for inp in payload.get("user_input", []):
                    if isinstance(inp, dict):
                        text = inp.get("text", "")
                    else:
                        text = str(inp)
                    if text:
                        if len(stats["topics"]) < 5:
                            stats["topics"].append(truncate(text))
                        file_mentions.extend(extract_file_paths(text))
            elif mtype == "ToolCall":
                stats["tool_calls"] += 1
                fn = payload.get("function", {})
                tool_name = fn.get("name") or "unknown"
                stats["tools"][tool_name] += 1
                args = fn.get("arguments", "")
                if isinstance(args, str):
                    file_mentions.extend(extract_file_paths(args))
                elif isinstance(args, dict):
                    for v in args.values():
                        if isinstance(v, str):
                            file_mentions.extend(extract_file_paths(v))
            elif mtype == "ToolResult":
                rv = payload.get("return_value", {})
                out = rv.get("output", "")
                if isinstance(out, str):
                    file_mentions.extend(extract_file_paths(out))

    stats["files"] = list(dict.fromkeys(file_mentions))[:20]
    return stats


# ---------------------------------------------------------------------------
# Copilot combined parser
# ---------------------------------------------------------------------------

def summarize_copilot(path: Path) -> Dict:
    stats = {
        "source": "GitHub Copilot",
        "path": str(path),
        "name": "copilot_sessions_combined",
        "lines": 0,
        "sessions": 0,
        "first_dt": None,
        "last_dt": None,
        "topics": [],
        "files": [],
    }
    current_session: Optional[str] = None
    file_mentions: List[str] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stats["lines"] += 1
            line = line.strip()
            if line.startswith("===== APPEND START "):
                # e.g. ===== APPEND START 2026-03-18T23:52:22Z =====
                m = re.search(r"APPEND START ([^=]+)", line)
                if m:
                    dt = iso_ts(m.group(1).strip())
                    if dt:
                        if stats["first_dt"] is None or dt < stats["first_dt"]:
                            stats["first_dt"] = dt
                        if stats["last_dt"] is None or dt > stats["last_dt"]:
                            stats["last_dt"] = dt
                continue
            if line.startswith("----- FILE:"):
                stats["sessions"] += 1
                continue
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Copilot objects are sparse; grab any text we can
            text = ""
            if "request" in obj and isinstance(obj["request"], dict):
                text = obj["request"].get("message", "")
            elif "response" in obj and isinstance(obj["response"], dict):
                text = obj["response"].get("message", "")
            if text and len(stats["topics"]) < 5:
                stats["topics"].append(truncate(text))
                file_mentions.extend(extract_file_paths(text))

    stats["files"] = list(dict.fromkeys(file_mentions))[:20]
    return stats


# ---------------------------------------------------------------------------
# Curated audit sessions parser
# ---------------------------------------------------------------------------

def summarize_audit_file(path: Path) -> Dict:
    stats = {
        "source": "Curated Export",
        "path": str(path),
        "name": path.stem,
        "lines": 0,
        "first_dt": None,
        "last_dt": None,
        "topics": [],
        "tools": Counter(),
        "files": [],
    }
    file_mentions: List[str] = []

    if path.suffix == ".jsonl":
        # These are often Claude-format JSONL dumps
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                stats["lines"] += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts_raw = obj.get("timestamp") or obj.get("createdAt")
                dt = iso_ts(ts_raw) if isinstance(ts_raw, str) else None
                if dt:
                    if stats["first_dt"] is None or dt < stats["first_dt"]:
                        stats["first_dt"] = dt
                    if stats["last_dt"] is None or dt > stats["last_dt"]:
                        stats["last_dt"] = dt
                t = obj.get("type")
                if t == "user":
                    content = obj.get("message", {}).get("content", [])
                    text = ""
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text += part.get("text", "")
                    if text and len(stats["topics"]) < 5:
                        stats["topics"].append(truncate(text))
                        file_mentions.extend(extract_file_paths(text))
                elif t == "tool":
                    tool_name = obj.get("toolName") or obj.get("tool", {}).get("name") or "unknown"
                    stats["tools"][tool_name] += 1
    else:
        # Small JSON metadata files
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                obj = json.load(f)
            text = str(obj)[:500]
            stats["topics"].append(truncate(text))
            file_mentions.extend(extract_file_paths(text))
            # use file mtime as proxy
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            stats["first_dt"] = mtime
            stats["last_dt"] = mtime
        except Exception:
            pass

    stats["files"] = list(dict.fromkeys(file_mentions))[:20]
    return stats


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_summary(sessions: List[Dict]) -> str:
    lines: List[str] = []
    lines.append("# Master Chat Summary — Research Stack")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("## Overview")
    lines.append("")

    total_claude = sum(1 for s in sessions if s["source"] == "Claude Code CLI")
    total_kimi = sum(1 for s in sessions if s["source"] == "Kimi Code CLI")
    total_copilot = sum(1 for s in sessions if s["source"] == "GitHub Copilot")
    total_audit = sum(1 for s in sessions if s["source"] == "Curated Export")

    lines.append(f"- **Claude Code CLI sessions**: {total_claude}")
    lines.append(f"- **Kimi Code CLI sessions**: {total_kimi}")
    lines.append(f"- **GitHub Copilot sessions**: {total_copilot}")
    lines.append(f"- **Curated audit exports**: {total_audit}")
    lines.append("")

    # Collect all topics for a thematic index
    all_topics: List[str] = []
    all_tools: Counter = Counter()
    all_files: List[str] = []
    for s in sessions:
        all_topics.extend(s.get("topics", []))
        all_tools.update(s.get("tools", Counter()))
        all_files.extend(s.get("files", []))

    # Thematic index
    lines.append("## Thematic Index")
    lines.append("")
    if all_topics:
        lines.append("### Sample Topics / Prompts")
        lines.append("")
        for i, topic in enumerate(dict.fromkeys(all_topics[:30]), 1):
            lines.append(f"{i}. {topic}")
        lines.append("")

    if all_tools:
        lines.append("### Most Used Tools")
        lines.append("")
        for tool, count in all_tools.most_common(20):
            lines.append(f"- `{tool}`: {count}")
        lines.append("")

    if all_files:
        lines.append("### Frequently Referenced Paths")
        lines.append("")
        for fp in dict.fromkeys(all_files[:30]):
            lines.append(f"- `{fp}`")
        lines.append("")

    # Per-source breakdown
    lines.append("## Session Breakdown")
    lines.append("")

    def section(title: str, src: str):
        lines.append(f"### {title}")
        lines.append("")
        subset = [s for s in sessions if s["source"] == src]
        if not subset:
            lines.append("No sessions found.")
            lines.append("")
            return
        # sort by first_dt desc
        subset.sort(key=lambda x: x.get("last_dt") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        for s in subset:
            name = s["name"]
            dt_range = f"{fmt_dt(s.get('first_dt'))} → {fmt_dt(s.get('last_dt'))}"
            lines.append(f"**{name}**  ")
            lines.append(f"*Date range*: {dt_range}  ")
            if src == "Claude Code CLI":
                lines.append(
                    f"User msgs: {s.get('user_msgs', 0)} | "
                    f"Assistant msgs: {s.get('assistant_msgs', 0)} | "
                    f"Tool calls: {s.get('tool_calls', 0)} | "
                    f"Attachments: {s.get('attachments', 0)}"
                )
            elif src == "Kimi Code CLI":
                lines.append(
                    f"Turns: {s.get('turns', 0)} | "
                    f"Tool calls: {s.get('tool_calls', 0)}"
                )
            elif src == "GitHub Copilot":
                lines.append(f"Lines: {s.get('lines', 0)} | Sessions: {s.get('sessions', 0)}")
            elif src == "Curated Export":
                lines.append(f"Lines: {s.get('lines', 0)} | Tools: {len(s.get('tools', {}))}")
            if s.get("topics"):
                lines.append(f"Topics: {truncate('; '.join(s['topics']), 200)}")
            if s.get("files"):
                lines.append(f"Files: {', '.join(s['files'][:5])}")
            lines.append("")

    section("Claude Code CLI", "Claude Code CLI")
    section("Kimi Code CLI", "Kimi Code CLI")
    section("GitHub Copilot", "GitHub Copilot")
    section("Curated Exports", "Curated Export")

    lines.append("---")
    lines.append("*End of summary*")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    sessions: List[Dict] = []

    # 1. Claude Code CLI
    claude_dir = Path.home() / ".claude" / "projects" / "-home-allaun-Research-Stack"
    if claude_dir.exists():
        for f in sorted(claude_dir.glob("*.jsonl")):
            print(f"Processing Claude: {f.name} ...")
            sessions.append(summarize_claude_jsonl(f))

    # 2. Kimi Code CLI
    kimi_dir = Path.home() / ".kimi" / "sessions" / "51a59f41af9880b34a14f55f839768fe"
    if kimi_dir.exists():
        for subdir in sorted(kimi_dir.iterdir()):
            wire = subdir / "wire.jsonl"
            if wire.exists():
                print(f"Processing Kimi: {subdir.name} ...")
                sessions.append(summarize_kimi_wire(wire))

    # 3. Copilot
    copilot_path = PROJECT_ROOT / "docs" / "chat_logs" / "copilot_sessions_combined.jsonl"
    if copilot_path.exists():
        print(f"Processing Copilot combined ...")
        sessions.append(summarize_copilot(copilot_path))

    # 4. Curated audit sessions
    audit_dir = PROJECT_ROOT / "audit" / "sessions"
    if audit_dir.exists():
        for f in sorted(audit_dir.iterdir()):
            if f.suffix in (".json", ".jsonl"):
                print(f"Processing audit: {f.name} ...")
                sessions.append(summarize_audit_file(f))

    md = render_summary(sessions)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(md, encoding="utf-8")
    print(f"\nWrote summary to: {OUT_PATH}")


if __name__ == "__main__":
    main()
