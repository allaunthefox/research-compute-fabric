#!/usr/bin/env python3
"""
Emit Ollama-compatible DeepSeek review answers and receipts.

This is the canonical emitter for receipts with schema
`ollama_deepseek_review_receipt_v1` and
`ollama_deepseek_review_continuation_receipt_v1`.

The integrity rule is deliberately strict: write the answer first, compute
`answer_sha256` from the bytes read back from disk, write the receipt, then
verify the receipt against the answer path before returning success.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = REPO / "shared-data" / "artifacts" / "deepseek_review"
DEFAULT_ENDPOINT = "https://ollama.com/v1/chat/completions"
PROVIDER_TAG = "deepseek"
PRIMARY_SCHEMA = "ollama_deepseek_review_receipt_v1"
CONTINUATION_SCHEMA = "ollama_deepseek_review_continuation_receipt_v1"


@dataclass(frozen=True)
class EmittedReview:
    answer_path: Path
    receipt_path: Path
    answer_sha256: str
    prompt_sha256: str


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def repo_relative(path: Path, repo_root: Path = REPO) -> str:
    path = path.resolve()
    repo_root = repo_root.resolve()
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return slug or "review"


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso_from_stamp(stamp: str) -> str:
    parsed = dt.datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
    return parsed.isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_context_bundle(paths: list[Path], repo_root: Path = REPO) -> tuple[str, list[str]]:
    chunks: list[str] = []
    context_files: list[str] = []
    for path in paths:
        body = read_text(path)
        rel = repo_relative(path, repo_root)
        chunks.append(f"\n\n===== FILE: {rel} =====\n{body}")
        context_files.append(rel)
    return "".join(chunks), context_files


def build_messages(
    prompt: str,
    context_text: str,
    previous_answer_path: Path | None,
) -> list[dict[str, str]]:
    if previous_answer_path is not None:
        previous_answer = read_text(previous_answer_path)
        user_content = (
            f"{previous_answer}\n\n"
            "===== CONTINUATION REQUEST =====\n"
            f"{prompt}"
        )
    else:
        user_content = (
            f"{context_text}\n\n"
            "===== REVIEW REQUEST =====\n"
            f"{prompt}"
        )

    return [
        {
            "role": "system",
            "content": (
                "You are an external mathematical reviewer. Answer only from "
                "the provided context and make arithmetic checks explicit."
            ),
        },
        {"role": "user", "content": user_content},
    ]


def build_request_body(
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    return {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }


def call_ollama_chat(endpoint: str, api_key: str | None, request_bytes: bytes) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif not endpoint.startswith(("http://127.0.0.1", "http://localhost")):
        raise RuntimeError("OLLAMA_API_KEY is required for non-local Ollama endpoints")

    request = urllib.request.Request(
        endpoint,
        data=request_bytes,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama endpoint returned HTTP {exc.code}: {detail}") from exc


def extract_answer(response: dict[str, Any]) -> tuple[str, dict[str, int], list[str]]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("response has no choices")

    message = choices[0].get("message", {})
    if not isinstance(message, dict):
        raise ValueError("response choice has no message object")

    content = message.get("content", "")
    if isinstance(content, str):
        answer_text = content
    else:
        answer_text = json.dumps(content, ensure_ascii=False)

    usage_obj = response.get("usage", {})
    usage = {
        "prompt_tokens": int(usage_obj.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(usage_obj.get("completion_tokens", 0) or 0),
        "total_tokens": int(usage_obj.get("total_tokens", 0) or 0),
    }
    if usage["total_tokens"] == 0:
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

    return answer_text, usage, list(message.keys())


def write_text_and_hash(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return sha256_bytes(path.read_bytes())


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def verify_receipt(receipt_path: Path, repo_root: Path = REPO) -> bool:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    schema = receipt.get("schema")
    if schema not in {PRIMARY_SCHEMA, CONTINUATION_SCHEMA}:
        raise ValueError(f"{receipt_path}: unknown schema {schema!r}")

    answer_path = repo_root / receipt["answer_path"]
    actual = sha256_bytes(answer_path.read_bytes())
    expected = receipt.get("answer_sha256")
    if actual != expected:
        raise ValueError(f"{receipt_path}: answer_sha256 mismatch: {actual} != {expected}")

    if schema == PRIMARY_SCHEMA:
        if not isinstance(receipt.get("context_files"), list):
            raise ValueError(f"{receipt_path}: primary receipt missing context_files")
        if "previous_answer_path" in receipt:
            raise ValueError(f"{receipt_path}: primary receipt must not carry previous_answer_path")
    else:
        if not receipt.get("previous_answer_path"):
            raise ValueError(f"{receipt_path}: continuation receipt missing previous_answer_path")
        if "context_files" in receipt:
            raise ValueError(f"{receipt_path}: continuation receipt must omit context_files")

    return True


def emit_review(
    *,
    topic: str,
    model: str,
    prompt: str,
    context_paths: list[Path],
    previous_answer_path: Path | None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    endpoint: str = DEFAULT_ENDPOINT,
    max_tokens: int = 5000,
    temperature: float = 0.0,
    timestamp: str | None = None,
    api_key: str | None = None,
    response: dict[str, Any] | None = None,
    repo_root: Path = REPO,
) -> EmittedReview:
    stamp = timestamp or utc_timestamp()
    created_at = iso_from_stamp(stamp)
    context_text, context_files = read_context_bundle(context_paths, repo_root)
    messages = build_messages(prompt, context_text, previous_answer_path)
    request_body = build_request_body(model, messages, max_tokens, temperature)
    request_bytes = canonical_json_bytes(request_body)
    prompt_sha256 = sha256_bytes(request_bytes)

    if response is None:
        response = call_ollama_chat(endpoint, api_key or os.getenv("OLLAMA_API_KEY"), request_bytes)

    answer_text, usage, message_keys = extract_answer(response)
    stem = f"{safe_slug(topic)}_{PROVIDER_TAG}_{safe_slug(model)}"
    if previous_answer_path is not None:
        stem += "_continuation"
    stem += f"_{stamp}"

    answer_path = output_dir / f"{stem}.md"
    receipt_path = output_dir / f"{stem}.receipt.json"
    answer_sha256 = write_text_and_hash(answer_path, answer_text)

    receipt: dict[str, Any] = {
        "schema": CONTINUATION_SCHEMA if previous_answer_path else PRIMARY_SCHEMA,
        "created_at": created_at,
        "model": model,
        "endpoint": endpoint,
        "prompt_sha256": prompt_sha256,
        "answer_sha256": answer_sha256,
        "usage": usage,
        "answer_path": repo_relative(answer_path, repo_root),
    }

    if previous_answer_path is None:
        receipt["context_files"] = context_files
    else:
        receipt["previous_answer_path"] = repo_relative(previous_answer_path, repo_root)
        if message_keys:
            receipt["message_keys"] = message_keys

    write_receipt(receipt_path, receipt)
    verify_receipt(receipt_path, repo_root)
    return EmittedReview(answer_path, receipt_path, answer_sha256, prompt_sha256)


def verify_receipt_dir(path: Path, repo_root: Path = REPO) -> int:
    count = 0
    for receipt_path in sorted(path.glob("*.receipt.json")):
        verify_receipt(receipt_path, repo_root)
        count += 1
    return count


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return read_text(Path(args.prompt_file))
    if args.prompt:
        return args.prompt
    return sys.stdin.read()


def _cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?", help="review prompt; stdin is used if omitted")
    parser.add_argument("--prompt-file", help="read review prompt from a file")
    parser.add_argument("--topic", default="review", help="artifact topic slug")
    parser.add_argument("--model", default="deepseek-v3.2")
    parser.add_argument("--endpoint", default=os.getenv("OLLAMA_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--context-file", action="append", default=[], help="primary review context file")
    parser.add_argument("--continue-from", help="previous answer markdown for continuation receipts")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-tokens", type=int, default=5000)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timestamp", help="UTC stamp YYYYMMDDTHHMMSSZ; mainly for tests/replay")
    parser.add_argument("--answer-text-file", help="offline mode: write this answer text instead of calling Ollama")
    parser.add_argument("--verify-only", nargs="*", help="verify receipt paths; with no paths, verify --output-dir")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if args.verify_only is not None:
        if args.verify_only:
            for receipt in args.verify_only:
                verify_receipt(Path(receipt))
                print(f"verified {receipt}")
        else:
            count = verify_receipt_dir(output_dir)
            print(f"verified {count} receipts in {output_dir}")
        return

    prompt = read_prompt(args)
    response = None
    if args.answer_text_file:
        answer_text = read_text(Path(args.answer_text_file))
        response = {
            "choices": [{"message": {"role": "assistant", "content": answer_text}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    emitted = emit_review(
        topic=args.topic,
        model=args.model,
        prompt=prompt,
        context_paths=[Path(p) for p in args.context_file],
        previous_answer_path=Path(args.continue_from) if args.continue_from else None,
        output_dir=output_dir,
        endpoint=args.endpoint,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        timestamp=args.timestamp,
        response=response,
    )
    print(json.dumps({
        "answer_path": repo_relative(emitted.answer_path),
        "receipt_path": repo_relative(emitted.receipt_path),
        "answer_sha256": emitted.answer_sha256,
        "prompt_sha256": emitted.prompt_sha256,
    }, indent=2))


if __name__ == "__main__":
    _cli()
