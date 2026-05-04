#!/usr/bin/env python3
"""Emit a machine-readable manifest of the build substrate."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(*args: str) -> str:
    completed = subprocess.run(
        list(args),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Workspace root to inspect.")
    parser.add_argument("--output", required=True, help="Path to the JSON manifest output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    lock_path = root / "components.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))

    tracked = []
    for component in lock["components"]:
        rel_path = component["path"]
        full_path = root / rel_path
        tracked.append(
            {
                "path": rel_path,
                "sha256": sha256_file(full_path),
            }
        )

    os_release_path = Path("/etc/os-release")

    manifest = {
        "schema": "hutter_build_manifest_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "os_release": os_release_path.read_text(encoding="utf-8")
        if os_release_path.is_file()
        else "",
        "tool_versions": {
            "python3": run("python3", "--version"),
            "xz": run("xz", "--version").splitlines()[0],
            "tar": run("tar", "--version").splitlines()[0],
            "gcc": run("gcc", "--version").splitlines()[0],
        },
        "apk_world": run("apk", "info", "-vv"),
        "tracked_components": tracked,
    }

    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote build manifest to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
