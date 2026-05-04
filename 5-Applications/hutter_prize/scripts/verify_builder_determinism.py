#!/usr/bin/env python3
"""Verify that public-facing builders produce byte-stable output across reruns."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_map(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        files[str(path.relative_to(root))] = sha256_file(path)
    return files


def run_builder(command: list[str], out_dir: Path) -> dict[str, str]:
    cmd = command + ["--out-dir", str(out_dir)]
    subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return file_map(out_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--builder",
        choices=("review-packet", "public-artifact"),
        required=True,
        help="Which builder to verify.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repo root for the review-packet builder. Defaults to the current directory.",
    )
    parser.add_argument(
        "--input",
        help="Input artifact for the public-artifact builder.",
    )
    parser.add_argument(
        "--label",
        help="Optional label passed through to the builder.",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Extra file to include for the review-packet builder.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "text", "json"),
        default="auto",
        help="Mode passed through to the public-artifact builder.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scripts_dir = Path(__file__).resolve().parent

    if args.builder == "review-packet":
        command = [
            sys.executable,
            str(scripts_dir / "build_review_packet.py"),
            "--root",
            str(Path(args.root).resolve()),
        ]
        if args.label:
            command.extend(["--label", args.label])
        for extra in args.include:
            command.extend(["--include", extra])
    else:
        if not args.input:
            print("--input is required for the public-artifact builder.", file=sys.stderr)
            return 2
        command = [
            sys.executable,
            str(scripts_dir / "prepare_public_artifact.py"),
            "--input",
            str(Path(args.input).resolve()),
            "--mode",
            args.mode,
        ]
        if args.label:
            command.extend(["--label", args.label])

    with tempfile.TemporaryDirectory(prefix="hutter_verify_a_") as first_tmp:
        with tempfile.TemporaryDirectory(prefix="hutter_verify_b_") as second_tmp:
            first = run_builder(command, Path(first_tmp))
            second = run_builder(command, Path(second_tmp))

    report = {
        "schema": "hutter_builder_determinism_report_v1",
        "builder": args.builder,
        "stable": first == second,
        "first": first,
        "second": second,
    }
    print(json.dumps(report, indent=2))
    return 0 if report["stable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
