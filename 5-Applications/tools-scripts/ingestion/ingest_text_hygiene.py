#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Helpers for provenance-safe ingest descriptions.

The index description field should summarize a source, not preserve raw body
text from captions, chat exports, transcript logs, or structured JSON/session
manifests. This module centralizes the heuristics used by 6-Documentation/archive/file ingestors
to derive a safe one-line description.
"""

from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path
from typing import Any

_SUBTITLE_SUFFIXES = {
    ".ass",
    ".lrc",
    ".sbv",
    ".srt",
    ".ssa",
    ".sub",
    ".ttml",
    ".vtt",
}

_CHAT_EXPORT_HINTS = (
    "chatexport",
    "copilot_sessions",
    "messages.html",
    "messages2.html",
    "telegram",
    "whatsapp",
    "discord",
    "slack",
)

_TRANSCRIPT_HINTS = (
    "conversation",
    "conversations_",
    "subtitle",
    "captions",
    "caption",
    "transcript",
    "chatgpt",
    "qwen",
    "gemini",
    "claude",
)

# AI model name tokens — only trigger transcript classification when paired
# with a context token in the same filename stem (prevents discord_api.md,
# gemini_api_note.md, captioning_research.md from being mis-classified).
_AI_MODEL_TOKENS = frozenset({"gemini", "claude", "chatgpt", "qwen", "gpt"})
_TRANSCRIPT_CONTEXT_TOKENS = frozenset({
    "conversation", "conversations", "transcript", "export",
    "chat", "session", "log", "messages",
})

_SUBTITLE_TIMESTAMP_RE = re.compile(
    r"\b\d{1,2}:\d{2}:\d{2}(?:[,.]\d{1,3})?\s*-->\s*"
    r"\d{1,2}:\d{2}:\d{2}(?:[,.]\d{1,3})?\b"
)

_HTML_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")


def _path_tokens(path: Path) -> frozenset[str]:
    """Lowercase word tokens from every part of *path* (dirs + filename)."""
    tokens: set[str] = set()
    for part in path.parts:
        tokens.update(t for t in _TOKEN_SPLIT_RE.split(part.lower()) if t)
    return frozenset(tokens)


def _stem_tokens(path: Path) -> frozenset[str]:
    """Lowercase word tokens from the filename stem only."""
    return frozenset(t for t in _TOKEN_SPLIT_RE.split(path.stem.lower()) if t)


def _dir_tokens(path: Path) -> frozenset[str]:
    """Lowercase word tokens from directory components only (not the filename)."""
    tokens: set[str] = set()
    for part in path.parts[:-1]:
        tokens.update(t for t in _TOKEN_SPLIT_RE.split(part.lower()) if t)
    return frozenset(tokens)


def _clean_line(text: str, max_len: int) -> str:
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _json_string(obj: dict[str, Any], key: str, max_len: int) -> str:
    value = obj.get(key)
    if isinstance(value, str):
        cleaned = _clean_line(value, max_len)
        if len(cleaned) >= 3:
            return cleaned
    return ""


def _description_from_json(path: Path, text: str, max_len: int) -> str:
    try:
        obj = json.loads(text)
    except Exception:
        return ""

    if isinstance(obj, dict):
        for key in (
            "description",
            "title",
            "source_title",
            "summary",
            "capture_reason",
            "expected_use",
        ):
            desc = _json_string(obj, key, max_len)
            if desc:
                return desc
        session_id = obj.get("session_id")
        if isinstance(session_id, str) and session_id.strip():
            return _clean_line(f"Structured session manifest: {session_id}", max_len)
        source_url = obj.get("source_url")
        if isinstance(source_url, str) and source_url.strip():
            return _clean_line(f"Structured web-source manifest: {path.name}", max_len)
        return _clean_line(f"Structured JSON source: {path.name}", max_len)

    if isinstance(obj, list):
        return _clean_line(f"Structured JSON collection: {path.name}", max_len)

    return ""


def _looks_like_subtitle(path: Path, text: str) -> bool:
    if path.suffix.lower() in _SUBTITLE_SUFFIXES:
        return True
    # Token match prevents "captioning_research.md" matching on "caption"
    if _path_tokens(path) & {"subtitle", "captions", "caption"}:
        return True
    if _SUBTITLE_TIMESTAMP_RE.search(text):
        return True
    lines = [line.strip().lower() for line in text.splitlines()[:24] if line.strip()]
    music_markers = sum(1 for line in lines if line in {"[music]", "[applause]", "[laughter]"})
    return music_markers >= 2


def _looks_like_chat_export(path: Path, text: str) -> bool:
    # Platform directory names (discord, slack, telegram, whatsapp) only trigger
    # when they appear in a *directory* component — not the filename.  This
    # prevents "6-Documentation/archive/discord_api.md" from being mis-labelled as a chat export
    # while still catching "discord_exports/messages.html".
    platform_hints = {"discord", "slack", "telegram", "whatsapp"}
    if _dir_tokens(path) & platform_hints:
        return True
    # Filename-level hints that are unambiguous export patterns
    if path.name.lower() in ("messages.html", "messages2.html"):
        return True
    if _path_tokens(path) & {"chatexport", "copilot_sessions"}:
        return True
    lowered = text[:4096].lower()
    return any(
        hint in lowered
        for hint in (
            "joined telegram",
            "===== append start",
            "chatexport",
            "copilot_sessions",
            "conversation_id",
            "<div class=\"message",
        )
    )


def _looks_like_transcript(path: Path, text: str) -> bool:
    stem = _stem_tokens(path)
    all_tokens = _path_tokens(path)

    # Unambiguous filename tokens
    if all_tokens & {"transcript", "conversations_"}:
        return True
    if "conversation" in stem or "conversations" in stem:
        return True

    # AI model names only fire when paired with a transcript-context token in
    # the same stem — prevents "gemini_api_note.md", "claude_sdk.md" from
    # being mis-classified as conversation transcripts.
    if stem & _AI_MODEL_TOKENS and stem & _TRANSCRIPT_CONTEXT_TOKENS:
        return True

    # Content-based fallbacks (unchanged)
    lowered = text[:2048].lower()
    if "thinking\n" in lowered and "web fetch" in lowered:
        return True
    if lowered.startswith("user\n") or lowered.startswith("assistant\n"):
        return True
    return False


def _html_title(text: str, max_len: int) -> str:
    match = _HTML_TITLE_RE.search(text)
    if not match:
        return ""
    title = _clean_line(match.group(1), max_len)
    if not title:
        return ""
    if any(bad in title.lower() for bad in ("joined telegram", "watch live")):
        return ""
    return title


def derive_safe_description(path: Path | str, text: str, max_len: int = 200) -> str:
    """Return a one-line summary safe for indexing as `description`."""
    path = Path(path)
    path_str = str(path).lower()

    if path.suffix.lower() == ".json":
        desc = _description_from_json(path, text, max_len)
        if desc:
            return desc

    if _looks_like_subtitle(path, text):
        return _clean_line(f"Video subtitle/caption source: {path.name}", max_len)

    if _looks_like_chat_export(path, text):
        if path.suffix.lower() == ".jsonl":
            return _clean_line(f"Conversation log archive: {path.name}", max_len)
        return _clean_line(f"Chat export archive: {path.name}", max_len)

    if _looks_like_transcript(path, text):
        return _clean_line(f"Conversation transcript source: {path.name}", max_len)

    if path.suffix.lower() == ".html":
        title = _html_title(text, max_len)
        if title:
            return title

    for line in text.splitlines():
        line = _clean_line(line.strip().lstrip("#").strip(), max_len)
        if len(line) > 8 and not line.startswith(("```", "http", "<")):
            return line

    fallback = path.name if path.name else path_str
    return _clean_line(f"Source artifact: {fallback}", max_len)
