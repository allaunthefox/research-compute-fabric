#!/usr/bin/env python3
"""Self-checks for ``validate_deepseek_receipts.py``.

Run with::

    uv run --python 3.11 --with "jsonschema>=4.21" --with "rfc3339-validator" \
        python3 scripts/math-first/test_validate_deepseek_receipts.py

The test builds positive and negative receipt fixtures in a temporary
directory, invokes the validator as a subprocess, and asserts the exit code
matches the expected outcome. The fixtures are derived from
``shared-data/artifacts/deepseek_review/`` so they exercise the same shape
that ships in the repo.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "math-first" / "validate_deepseek_receipts.py"

GOOD_PRIMARY = {
    "schema": "ollama_deepseek_review_receipt_v1",
    "created_at": "2026-05-12T03:35:51+00:00",
    "model": "deepseek-v3.2",
    "endpoint": "https://ollama.com/v1/chat/completions",
    "prompt_sha256": "sha256:" + "a" * 64,
    "answer_sha256": "sha256:" + "b" * 64,
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    "context_files": ["docs/example.md"],
    "answer_path": "shared-data/artifacts/deepseek_review/example.md",
}

GOOD_CONTINUATION = {
    "schema": "ollama_deepseek_review_continuation_receipt_v1",
    "created_at": "2026-05-12T03:38:49+00:00",
    "model": "deepseek-v4-flash",
    "endpoint": "https://ollama.com/v1/chat/completions",
    "prompt_sha256": "sha256:" + "c" * 64,
    "answer_sha256": "sha256:" + "d" * 64,
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    "previous_answer_path": "shared-data/artifacts/deepseek_review/example.md",
    "answer_path": "shared-data/artifacts/deepseek_review/example_continuation.md",
    "message_keys": ["role", "content", "reasoning"],
}


def _write(tmp: Path, name: str, payload: dict | str) -> Path:
    path = tmp / name
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)

        cases: list[tuple[str, dict | str, int]] = [
            ("good_primary.receipt.json", GOOD_PRIMARY, 0),
            ("good_continuation.receipt.json", GOOD_CONTINUATION, 0),
            (
                "bad_sha256.receipt.json",
                {**GOOD_PRIMARY, "prompt_sha256": "not-a-hash"},
                1,
            ),
            (
                "bad_schema_id.receipt.json",
                {**GOOD_PRIMARY, "schema": "made_up_schema_id"},
                1,
            ),
            (
                "bad_missing_usage.receipt.json",
                {k: v for k, v in GOOD_PRIMARY.items() if k != "usage"},
                1,
            ),
            (
                "bad_negative_tokens.receipt.json",
                {**GOOD_PRIMARY, "usage": {"prompt_tokens": -1, "completion_tokens": 1, "total_tokens": 0}},
                1,
            ),
            (
                "bad_answer_path_ext.receipt.json",
                {**GOOD_PRIMARY, "answer_path": "shared-data/artifacts/deepseek_review/example.txt"},
                1,
            ),
            (
                "bad_extra_field.receipt.json",
                {**GOOD_PRIMARY, "stray": 1},
                1,
            ),
            ("bad_not_json.receipt.json", "{not json}", 1),
        ]

        for name, payload, expected in cases:
            path = _write(tmp, name, payload)
            result = _run(path)
            if result.returncode != expected:
                failures.append(
                    f"{name}: expected exit {expected}, got {result.returncode}\n"
                    f"  stdout: {result.stdout.strip()}\n"
                    f"  stderr: {result.stderr.strip()}"
                )
            else:
                print(f"OK   {name} (exit {result.returncode})")

    if failures:
        print("\nFailures:")
        for line in failures:
            print(line)
        return 1
    print("\nAll validator self-checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
