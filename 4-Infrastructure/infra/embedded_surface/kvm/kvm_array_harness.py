#!/usr/bin/env python3
"""Run a small array of minimal KVM boot surfaces."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BIN = ROOT / "build" / "gcl_kvm_boot"
OUT_DIR = ROOT / "build" / "array"

REQUIRED_LINES = (
    "GCLKVM v0.1",
    "surface=node kind=kvm.boot op=recover",
    "kvm memslot=0 guest_phys=0x00000000 entry=0x00001000 io=0x00E9",
    "ot1 op=0x0D source=0x002A route=0x0001 seq=0x0001",
    "gcl admission=admitted invariant=recovery_subset",
    "BOOT_OK",
)


@dataclass
class RunResult:
    index: int
    status: str
    elapsed: float
    log_path: Path
    error: str | None = None


def validate(text: str) -> str | None:
    missing = [line for line in REQUIRED_LINES if line not in text]
    if missing:
        return "missing line(s): " + ", ".join(missing)
    if text.count("BOOT_OK") != 1:
        return f"expected one BOOT_OK marker, saw {text.count('BOOT_OK')}"
    return None


def run_one(index: int, timeout: float) -> RunResult:
    log_path = OUT_DIR / f"node-{index:02d}.log"
    start = time.monotonic()
    proc = subprocess.run(
        [str(BIN)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    elapsed = time.monotonic() - start
    log_path.write_text(proc.stdout, encoding="ascii")
    if proc.returncode != 0:
        return RunResult(index, "FAIL", elapsed, log_path, proc.stderr.strip()[-400:])
    error = validate(proc.stdout)
    return RunResult(index, "FAIL" if error else "OK", elapsed, log_path, error)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()

    subprocess.run(["make", "build/gcl_kvm_boot"], cwd=ROOT, check=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    failures = 0
    for result in [run_one(i, args.timeout) for i in range(args.count)]:
        print(f"node-{result.index:02d} {result.status} {result.elapsed:.4f}s {result.log_path.relative_to(ROOT)}")
        if result.error:
            failures += 1
            print(f"  {result.error}")

    if failures:
        print(f"kvm array result: {failures}/{args.count} failed", file=sys.stderr)
        return 1
    print(f"kvm array result: {args.count}/{args.count} minimal KVM surfaces emitted recovery pulses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
