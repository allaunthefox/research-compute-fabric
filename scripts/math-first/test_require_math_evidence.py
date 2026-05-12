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
    """Regression test: ``--staged`` sees the entire index, not just argv.

    Reproduces the pre-commit ``files`` filter bug. Without ``--staged``
    invoking the script with only the math-track filename (as pre-commit
    would, after filtering) would falsely fail. With ``--staged`` the
    script reads the full index and passes.
    """
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _git("init", "-q", cwd=tmp_path)

        # Lay out a minimal mirror of the math-track and evidence surfaces.
        math_track = tmp_path / "6-Documentation" / "docs" / "distilled" / "Spec.md"
        math_track.parent.mkdir(parents=True, exist_ok=True)
        math_track.write_text("# math claim\n")

        receipt = (
            tmp_path
            / "shared-data"
            / "artifacts"
            / "deepseek_review"
            / "x.receipt.json"
        )
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text("{}\n")

        # Stage both files. (The script does not parse the receipts here --
        # it only classifies by path.)
        _git("add", str(math_track.relative_to(tmp_path)), cwd=tmp_path)
        _git("add", str(receipt.relative_to(tmp_path)), cwd=tmp_path)

        # Run with --staged from inside the temp repo. The script will
        # rebase REPO_ROOT off its own location (the real repo), but the
        # ``git diff --cached`` call uses subprocess cwd, which we override
        # below by chdir-ing.
        # We invoke the script with a small wrapper script so we control cwd.
        wrapper = tmp_path / "run_wrapper.py"
        wrapper.write_text(
            "import os, runpy, sys\n"
            f"os.chdir({str(tmp_path)!r})\n"
            "sys.argv = ['require_math_evidence.py', '--staged']\n"
            f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
        )
        result = subprocess.run(
            [sys.executable, str(wrapper)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        # The script's REPO_ROOT is computed from its own __file__ (the real
        # repo), so it would join 6-Documentation/... onto the real repo
        # path. That's fine -- ``_is_math_track`` and ``_is_evidence``
        # operate on path *strings*, not on disk existence. The relevant
        # invariant is that the staged file list (computed via
        # ``git diff --cached`` in tmp_path) contains BOTH files.
        if result.returncode != 0:
            failures += 1
            print("FAIL staged_regression: expected exit 0, got", result.returncode)
            if result.stdout.strip():
                print(f"  stdout: {result.stdout.strip()}")
            if result.stderr.strip():
                print(f"  stderr: {result.stderr.strip()}")
        else:
            print("OK   staged_regression (math-track + receipt both staged -> exit 0)")
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
