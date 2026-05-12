#!/usr/bin/env python3
"""Self-check suite for ``require_math_evidence.py``.

Covers the classification logic plus the pre-commit-vs-CI regression that
motivated the follow-up fix: pre-commit applies its per-hook ``files``
filter before the script runs, so the script must read the full staged
set itself (via ``--staged``) rather than rely on the argv list.

Exit code:
    0  all cases passed.
    1  at least one case failed.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("require_math_evidence.py")


def _run(args: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    cmd = [sys.executable, str(SCRIPT), *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(cwd),
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        },
    )


CASES: list[tuple[str, list[str], int]] = [
    # (label, argv, expected exit code)
    ("noop_empty", [], 0),
    ("only_evidence_receipt", ["shared-data/artifacts/deepseek_review/x.receipt.json"], 0),
    ("only_evidence_claims", ["claims.yaml"], 0),
    ("only_unrelated", ["README.md", "src/foo.py"], 0),
    ("lean_self_evidence", ["0-Core-Formalism/lean/Semantics/Kernel.lean"], 0),
    ("doc_without_evidence", ["6-Documentation/docs/distilled/Spec.md"], 1),
    (
        "doc_with_receipt",
        [
            "6-Documentation/docs/distilled/Spec.md",
            "shared-data/artifacts/deepseek_review/some.receipt.json",
        ],
        0,
    ),
    (
        "doc_with_claims",
        ["6-Documentation/docs/distilled/Spec.md", "claims.yaml"],
        0,
    ),
    (
        "stack_solidification_without_evidence",
        ["shared-data/data/stack_solidification/foo.json"],
        1,
    ),
    (
        "stack_solidification_with_lean",
        [
            "shared-data/data/stack_solidification/foo.json",
            "0-Core-Formalism/lean/Semantics/Bar.lean",
        ],
        0,
    ),
]


def _run_argv_cases() -> int:
    failures = 0
    for label, argv, expected in CASES:
        code, stdout, stderr = _run(argv)
        if code != expected:
            failures += 1
            print(f"FAIL {label}: expected exit {expected}, got {code}")
            if stdout.strip():
                print(f"  stdout: {stdout.strip()}")
            if stderr.strip():
                print(f"  stderr: {stderr.strip()}")
        else:
            print(f"OK   {label} (exit {code})")
    return failures


def _run_mutex_check() -> int:
    """`--staged` and `--from-git-diff` and explicit FILES are mutually exclusive."""
    failures = 0
    for argv in (
        ["--staged", "--from-git-diff", "main"],
        ["--staged", "claims.yaml"],
        ["--from-git-diff", "main", "claims.yaml"],
    ):
        code, _stdout, stderr = _run(argv)
        if code != 2:
            failures += 1
            print(f"FAIL mutex {argv}: expected exit 2, got {code}")
            if stderr.strip():
                print(f"  stderr: {stderr.strip()}")
        else:
            print(f"OK   mutex {argv} (exit {code})")
    return failures


def _run_staged_regression() -> int:
    """Regression for the pre-commit ``files``-filter bug.

    Builds a throwaway git repo so this test is self-contained -- the
    test does not depend on the state of the real repo's index. The
    script is run with ``cwd=tmp_path`` (NOT via ``runpy``) so that
    ``git rev-parse --show-toplevel`` inside the script resolves to the
    temp repo, and ``git diff --cached`` queries the temp repo's index.

    Three sub-cases:
        (a) math-track-only staged                -> expect exit 1
            (proves the script actually evaluates classification logic;
            without (a) the next sub-case could pass vacuously by
            short-circuiting on an empty diff)
        (b) math-track + receipt staged           -> expect exit 0
            (the original pre-commit ``files``-filter bug)
        (c) math-track + claims.yaml staged       -> expect exit 0
            (verifies the registry-update path)
    """
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp).resolve()
        _git("init", "-q", cwd=tmp_path)

        math_track = tmp_path / "6-Documentation" / "docs" / "distilled" / "Spec.md"
        math_track.parent.mkdir(parents=True, exist_ok=True)
        math_track.write_text("# math claim\n")

        receipt = (
            tmp_path / "shared-data" / "artifacts" / "deepseek_review" / "x.receipt.json"
        )
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text("{}\n")

        claims = tmp_path / "claims.yaml"
        claims.write_text("claims: []\n")

        def _stage_only(*relpaths: str) -> None:
            # Reset the index to a clean state, then stage exactly the
            # supplied paths. ``git reset`` is safe here -- the temp repo
            # has no commits, so there is no "HEAD" to reset against. We
            # instead remove everything currently in the index.
            _git("rm", "--cached", "-rf", "--ignore-unmatch", ".", cwd=tmp_path)
            for relpath in relpaths:
                _git("add", "--", relpath, cwd=tmp_path)

        def _invoke() -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, str(SCRIPT), "--staged"],
                capture_output=True,
                text=True,
                cwd=str(tmp_path),
            )

        def _assert(label: str, expected_exit: int, *staged: str) -> int:
            _stage_only(*staged)
            indexed = _git("diff", "--cached", "--name-only", cwd=tmp_path).stdout.splitlines()
            indexed = [line for line in indexed if line.strip()]
            if sorted(indexed) != sorted(staged):
                print(f"FAIL {label}: index does not match expected staging")
                print(f"  expected: {sorted(staged)}")
                print(f"  actual:   {sorted(indexed)}")
                return 1
            result = _invoke()
            if result.returncode != expected_exit:
                print(
                    f"FAIL {label}: expected exit {expected_exit}, "
                    f"got {result.returncode}"
                )
                if result.stdout.strip():
                    print(f"  stdout: {result.stdout.strip()}")
                if result.stderr.strip():
                    print(f"  stderr: {result.stderr.strip()}")
                return 1
            print(f"OK   {label} (exit {expected_exit})")
            return 0

        failures += _assert(
            "staged_regression_negative (math-only -> FAIL)",
            1,
            "6-Documentation/docs/distilled/Spec.md",
        )
        failures += _assert(
            "staged_regression_positive_receipt (math + receipt -> OK)",
            0,
            "6-Documentation/docs/distilled/Spec.md",
            "shared-data/artifacts/deepseek_review/x.receipt.json",
        )
        failures += _assert(
            "staged_regression_positive_claims (math + claims.yaml -> OK)",
            0,
            "6-Documentation/docs/distilled/Spec.md",
            "claims.yaml",
        )
    return failures


def main() -> int:
    failures = 0
    failures += _run_argv_cases()
    failures += _run_mutex_check()
    failures += _run_staged_regression()
    if failures:
        print(f"\n{failures} case(s) FAILED")
        return 1
    print("\nAll require_math_evidence self-checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
