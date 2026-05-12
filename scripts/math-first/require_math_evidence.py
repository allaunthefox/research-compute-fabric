#!/usr/bin/env python3
"""Require math evidence alongside math-track edits.

When a commit (or PR) touches files under one of the math-track surfaces,
this script asserts that at least one file under a math-evidence surface is
also part of the same change set. The two surfaces are configurable -- the
defaults below match ``docs/math-first-tooling.md`` and the pre-commit hook
declared in ``.pre-commit-config.yaml``.

Math-track surfaces (need evidence):
  - 0-Core-Formalism/lean/Semantics/...
  - 6-Documentation/docs/distilled/...
  - shared-data/data/stack_solidification/...

Math-evidence surfaces (accepted as evidence):
  - shared-data/artifacts/deepseek_review/*.receipt.json
  - 0-Core-Formalism/lean/Semantics/...   (a Lean change in the same commit
                                            counts because Lean is the source
                                            of truth per AGENTS.md)
  - claims.yaml                            (registry update)

Usage:
    scripts/math-first/require_math_evidence.py [FILES ...]
    scripts/math-first/require_math_evidence.py --staged
    scripts/math-first/require_math_evidence.py --from-git-diff BASE_REF

If no input mode is supplied the script exits 0 with a noop. Pre-commit
invokes it with ``--staged`` so the script sees the entire staged set
regardless of pre-commit's own ``files`` filter; CI invokes it with
``--from-git-diff origin/<base>``.

Exit code:
    0  evidence present, nothing to do, or no math-track files changed.
    1  math-track files changed without accompanying evidence.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Only used for logging/help -- *not* as the subprocess ``cwd`` for the git
# calls below. Hardcoding the subprocess cwd to this path caused the
# regression test in ``test_require_math_evidence.py`` to pass vacuously
# because the test stages files in a *temp* repo and expects ``git diff
# --cached`` to query that temp repo, not the real one. Pre-commit and CI
# both happen to invoke the script from inside the repo root, so letting
# the git subprocess inherit cwd is correct in every real-world case.
REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_toplevel(cwd: Path | None = None) -> Path:
    """Return the absolute path of the git working tree containing ``cwd``.

    Defaults to the current working directory. The script never assumes the
    git repo lives at ``REPO_ROOT`` because that would be wrong when the
    script is run from a different working tree -- notably, the temp repo
    set up by ``test_require_math_evidence.py``.
    """
    cmd = ["git", "rev-parse", "--show-toplevel"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=str(cwd) if cwd is not None else None,
        )
    except subprocess.CalledProcessError as exc:
        print(
            f"error: `{' '.join(cmd)}` failed: {exc.stderr.strip()}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return Path(result.stdout.strip())


MATH_TRACK_PREFIXES: tuple[str, ...] = (
    "0-Core-Formalism/lean/Semantics/",
    "6-Documentation/docs/distilled/",
    "shared-data/data/stack_solidification/",
)

EVIDENCE_PREFIXES: tuple[str, ...] = (
    "shared-data/artifacts/deepseek_review/",
    "0-Core-Formalism/lean/Semantics/",
)

EVIDENCE_FILES: tuple[str, ...] = (
    "claims.yaml",
)


def _normalise(path: str) -> str:
    return path.replace("\\", "/")


def _is_math_track(path: str) -> bool:
    norm = _normalise(path)
    return any(norm.startswith(prefix) for prefix in MATH_TRACK_PREFIXES)


def _is_evidence(path: str) -> bool:
    norm = _normalise(path)
    if norm in EVIDENCE_FILES:
        return True
    if any(norm.startswith(prefix) for prefix in EVIDENCE_PREFIXES):
        # A *new or updated* receipt counts. A bare Lean kernel edit also
        # counts because Lean is treated as the source of truth -- the change
        # itself is the evidence.
        if norm.startswith("shared-data/artifacts/deepseek_review/"):
            return norm.endswith(".receipt.json") or norm.endswith(".md")
        return True
    return False


def _files_from_git_diff(base_ref: str) -> list[str]:
    cwd = _git_toplevel()
    cmd = ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=str(cwd)
        )
    except subprocess.CalledProcessError as exc:
        print(f"error: `{' '.join(cmd)}` failed: {exc.stderr.strip()}", file=sys.stderr)
        raise SystemExit(2)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _files_from_staged() -> list[str]:
    """Return the staged file list via ``git diff --cached --name-only``.

    Used by the pre-commit hook so the script sees every staged file --
    math-track *and* evidence -- regardless of pre-commit's per-hook
    ``files`` filter. This is important because pre-commit otherwise strips
    receipts and ``claims.yaml`` from the argv before the script ever sees
    them, which would cause the evidence check to falsely fail.

    The subprocess cwd is the actual git toplevel containing the *current*
    working directory, not a hardcoded path -- so the script works
    correctly inside the regression test's temp repo too.
    """
    cwd = _git_toplevel()
    cmd = ["git", "diff", "--cached", "--name-only"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=str(cwd)
        )
    except subprocess.CalledProcessError as exc:
        print(f"error: `{' '.join(cmd)}` failed: {exc.stderr.strip()}", file=sys.stderr)
        raise SystemExit(2)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files",
        nargs="*",
        help="Explicit list of files to check (typically supplied by pre-commit).",
    )
    parser.add_argument(
        "--from-git-diff",
        metavar="BASE_REF",
        help="Compute the file list from `git diff --name-only BASE_REF...HEAD`.",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Compute the file list from `git diff --cached --name-only` "
        "(use this from pre-commit so the entire staged set is visible).",
    )
    args = parser.parse_args(argv)

    if sum(bool(x) for x in (args.from_git_diff, args.staged, args.files)) > 1:
        parser.error("--from-git-diff, --staged, and explicit FILES are mutually exclusive")

    if args.from_git_diff:
        files = _files_from_git_diff(args.from_git_diff)
    elif args.staged:
        files = _files_from_staged()
    else:
        files = list(args.files)

    if not files:
        return 0

    math_track = sorted({f for f in files if _is_math_track(f)})
    evidence = sorted({f for f in files if _is_evidence(f)})

    if not math_track:
        return 0

    if evidence:
        print("math-evidence check: OK")
        print("  math-track files:")
        for path in math_track:
            print(f"    - {path}")
        print("  evidence files:")
        for path in evidence:
            print(f"    - {path}")
        return 0

    print("math-evidence check: FAIL", file=sys.stderr)
    print("  math-track files changed without accompanying evidence:", file=sys.stderr)
    for path in math_track:
        print(f"    - {path}", file=sys.stderr)
    print(
        "\n  Add at least one of:\n"
        "    - a DeepSeek review receipt under shared-data/artifacts/deepseek_review/\n"
        "    - a Lean change under 0-Core-Formalism/lean/Semantics/\n"
        "    - a claims.yaml update\n"
        "  See docs/math-first-tooling.md.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
