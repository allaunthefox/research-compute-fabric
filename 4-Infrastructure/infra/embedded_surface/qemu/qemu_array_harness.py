#!/usr/bin/env python3
"""
Run an array of tiny GCL boot surfaces under QEMU.

The harness builds the boot sector once, launches N independent QEMU instances,
captures each serial log, and validates the recovery pulse. It is designed to
expose concurrency, boot drift, malformed pulse, and timeout bugs early.
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
BOOT_BIN = BUILD_DIR / "gcl_boot.bin"
ARRAY_DIR = BUILD_DIR / "array"

REQUIRED_LINES = (
    "GCLBOOT v0.1",
    "surface=node kind=qemu.boot op=recover",
    "ot1 op=0x0D source=0x002A route=0x0001 seq=0x0001",
    "gcl admission=admitted invariant=recovery_subset",
    "BOOT_OK",
)


@dataclass
class NodeRun:
    index: int
    attempt: int
    log_path: Path
    process: subprocess.Popen[bytes]
    started_at: float
    boot_ok_at: float | None = None
    error: str | None = None


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def verify_boot_image() -> None:
    if not BOOT_BIN.exists():
        raise RuntimeError(f"missing boot image: {BOOT_BIN}")
    data = BOOT_BIN.read_bytes()
    if len(data) != 512:
        raise RuntimeError(f"boot image must be 512 bytes, got {len(data)}")
    if data[510:512] != b"\x55\xaa":
        raise RuntimeError("boot image is missing BIOS 0x55AA signature")


def spawn_node(index: int, attempt: int, memory: str) -> NodeRun:
    log_path = ARRAY_DIR / f"node-{index:02d}.attempt-{attempt:02d}.serial.log"
    log_path.unlink(missing_ok=True)
    cmd = [
        "qemu-system-x86_64",
        "-machine",
        "accel=tcg",
        "-m",
        memory,
        "-display",
        "none",
        "-no-reboot",
        "-drive",
        f"format=raw,file={BOOT_BIN},if=floppy,readonly=on",
        "-serial",
        f"file:{log_path}",
        "-monitor",
        "none",
        "-no-shutdown",
    ]
    return NodeRun(
        index=index,
        attempt=attempt,
        log_path=log_path,
        process=subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE),
        started_at=time.monotonic(),
    )


def read_log(path: Path) -> str:
    try:
        return path.read_text(encoding="ascii", errors="replace")
    except FileNotFoundError:
        return ""


def mutate_observation(
    text: str,
    corrupt_rate: float,
    duplicate_rate: float,
    truncate_rate: float,
    rng: random.Random,
) -> str:
    if text and truncate_rate > 0.0 and rng.random() < truncate_rate:
        text = text[: rng.randrange(0, len(text))]
    if text and duplicate_rate > 0.0 and rng.random() < duplicate_rate:
        text += "BOOT_OK\r\n"
    if text and corrupt_rate > 0.0 and rng.random() < corrupt_rate:
        edits = (
            ("BOOT_OK", "B00T_OK"),
            ("op=recover", "op=unknown"),
            ("admission=admitted", "admission=quarantined"),
            ("source=0x002A", "source=0xFFFF"),
        )
        old, new = rng.choice(edits)
        text = text.replace(old, new, 1)
    return text


def observed_log(
    path: Path,
    drop_rate: float,
    stale_rate: float,
    corrupt_rate: float,
    duplicate_rate: float,
    truncate_rate: float,
    cache: dict[Path, str],
    rng: random.Random,
) -> str:
    if drop_rate > 0.0 and rng.random() < drop_rate:
        return ""
    if stale_rate > 0.0 and path in cache and rng.random() < stale_rate:
        return cache[path]
    text = read_log(path)
    text = mutate_observation(text, corrupt_rate, duplicate_rate, truncate_rate, rng)
    cache[path] = text
    return text


def validate_log(text: str) -> str | None:
    missing = [line for line in REQUIRED_LINES if line not in text]
    if missing:
        return "missing serial line(s): " + ", ".join(missing)
    if text.count("BOOT_OK") != 1:
        return f"expected one BOOT_OK marker, saw {text.count('BOOT_OK')}"
    if "op=recover" not in text:
        return "missing recovery op"
    if "admission=admitted" not in text:
        return "missing GCL admission"
    return None


def stop_node(node: NodeRun) -> None:
    if node.process.poll() is None:
        node.process.terminate()
        try:
            node.process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            node.process.kill()
            node.process.wait(timeout=1.0)


def stderr_tail(node: NodeRun) -> str:
    if node.process.stderr is None:
        return ""
    try:
        data = node.process.stderr.read() or b""
    except ValueError:
        return ""
    return data.decode("utf-8", errors="replace").strip()[-400:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=10, help="QEMU instances to launch")
    parser.add_argument("--timeout", type=float, default=5.0, help="seconds per node")
    parser.add_argument("--memory", default="8M", help="guest memory per node")
    parser.add_argument(
        "--scenario",
        choices=("clean", "finicky", "dodgy"),
        default="clean",
        help="test profile; dodgy simulates a bargain-bin control plane",
    )
    parser.add_argument("--seed", type=int, default=510510, help="deterministic jitter seed")
    parser.add_argument("--retries", type=int, default=0, help="extra attempts per node")
    parser.add_argument("--quorum", type=int, default=None, help="minimum successful nodes")
    parser.add_argument("--start-jitter", type=float, default=0.0, help="max launch delay per node")
    parser.add_argument("--poll-min", type=float, default=0.05, help="minimum polling delay")
    parser.add_argument("--poll-max", type=float, default=0.05, help="maximum polling delay")
    parser.add_argument("--observe-drop-rate", type=float, default=0.0, help="chance to miss a log read")
    parser.add_argument("--observe-stale-rate", type=float, default=0.0, help="chance to reuse old observer data")
    parser.add_argument("--observe-corrupt-rate", type=float, default=0.0, help="chance to corrupt observer data")
    parser.add_argument("--observe-duplicate-rate", type=float, default=0.0, help="chance to duplicate BOOT_OK")
    parser.add_argument("--observe-truncate-rate", type=float, default=0.0, help="chance to truncate observer data")
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be >= 1")
    if args.retries < 0:
        parser.error("--retries must be >= 0")
    if not 0.0 <= args.observe_drop_rate <= 1.0:
        parser.error("--observe-drop-rate must be between 0 and 1")
    for rate_name in (
        "observe_stale_rate",
        "observe_corrupt_rate",
        "observe_duplicate_rate",
        "observe_truncate_rate",
    ):
        if not 0.0 <= getattr(args, rate_name) <= 1.0:
            parser.error(f"--{rate_name.replace('_', '-')} must be between 0 and 1")
    if args.poll_min <= 0.0 or args.poll_max < args.poll_min:
        parser.error("--poll-min/--poll-max must be positive and ordered")

    if args.scenario in ("finicky", "dodgy"):
        args.count = 12 if args.count == 10 else args.count
        args.timeout = 0.45 if args.timeout == 5.0 else args.timeout
        args.retries = 3 if args.retries == 0 else args.retries
        args.quorum = args.count if args.quorum is None else args.quorum
        args.start_jitter = 0.25 if args.start_jitter == 0.0 else args.start_jitter
        args.poll_min = 0.02 if args.poll_min == 0.05 else args.poll_min
        args.poll_max = 0.22 if args.poll_max == 0.05 else args.poll_max
        args.observe_drop_rate = 0.35 if args.observe_drop_rate == 0.0 else args.observe_drop_rate
    if args.scenario == "dodgy":
        args.count = 16 if args.count == 12 else args.count
        args.timeout = 0.30 if args.timeout == 0.45 else args.timeout
        args.retries = 6 if args.retries == 3 else args.retries
        args.quorum = 12 if args.quorum == args.count else args.quorum
        args.start_jitter = 0.40 if args.start_jitter == 0.25 else args.start_jitter
        args.poll_max = 0.35 if args.poll_max == 0.22 else args.poll_max
        args.observe_drop_rate = 0.45 if args.observe_drop_rate == 0.35 else args.observe_drop_rate
        args.observe_stale_rate = 0.25 if args.observe_stale_rate == 0.0 else args.observe_stale_rate
        args.observe_corrupt_rate = 0.18 if args.observe_corrupt_rate == 0.0 else args.observe_corrupt_rate
        args.observe_duplicate_rate = 0.12 if args.observe_duplicate_rate == 0.0 else args.observe_duplicate_rate
        args.observe_truncate_rate = 0.20 if args.observe_truncate_rate == 0.0 else args.observe_truncate_rate

    quorum = args.count if args.quorum is None else args.quorum
    if quorum < 1 or quorum > args.count:
        parser.error("--quorum must be between 1 and --count")

    rng = random.Random(args.seed)

    run(["make", "build/gcl_boot.bin"])
    verify_boot_image()
    ARRAY_DIR.mkdir(parents=True, exist_ok=True)

    current: dict[int, NodeRun] = {}
    final: dict[int, NodeRun] = {}
    attempts = {index: 0 for index in range(args.count)}
    history: dict[int, list[str]] = {index: [] for index in range(args.count)}
    observer_cache: dict[Path, str] = {}

    def launch(index: int) -> None:
        if args.start_jitter > 0.0:
            time.sleep(rng.uniform(0.0, args.start_jitter))
        current[index] = spawn_node(index, attempts[index], args.memory)

    for node_index in range(args.count):
        launch(node_index)

    try:
        while current:
            now = time.monotonic()
            for index, node in list(current.items()):
                text = observed_log(
                    node.log_path,
                    args.observe_drop_rate,
                    args.observe_stale_rate,
                    args.observe_corrupt_rate,
                    args.observe_duplicate_rate,
                    args.observe_truncate_rate,
                    observer_cache,
                    rng,
                )
                timed_out = (now - node.started_at) >= args.timeout
                if "BOOT_OK" in text:
                    node.boot_ok_at = now
                    node.error = validate_log(text)
                    stop_node(node)
                    del current[index]
                    if node.error and attempts[index] < args.retries:
                        history[index].append(f"attempt-{node.attempt:02d}: {node.error}")
                        attempts[index] += 1
                        launch(index)
                    else:
                        final[index] = node
                elif node.process.poll() is not None:
                    node.error = f"qemu exited early with {node.process.returncode}: {stderr_tail(node)}"
                    del current[index]
                    if attempts[index] < args.retries:
                        history[index].append(f"attempt-{node.attempt:02d}: {node.error}")
                        attempts[index] += 1
                        launch(index)
                    else:
                        final[index] = node
                elif timed_out:
                    visible_text = read_log(node.log_path)
                    if "BOOT_OK" in visible_text:
                        node.error = "observer missed BOOT_OK before timeout"
                    else:
                        node.error = f"timeout after {args.timeout:.2f}s"
                    stop_node(node)
                    del current[index]
                    if attempts[index] < args.retries:
                        history[index].append(f"attempt-{node.attempt:02d}: {node.error}")
                        attempts[index] += 1
                        launch(index)
                    else:
                        final[index] = node
            if current:
                time.sleep(rng.uniform(args.poll_min, args.poll_max))
    finally:
        for node in current.values():
            stop_node(node)

    failures = [node for node in final.values() if node.error]
    successes = [node for node in final.values() if not node.error]
    for node in [final[index] for index in sorted(final)]:
        elapsed = (node.boot_ok_at or time.monotonic()) - node.started_at
        status = "FAIL" if node.error else "OK"
        print(
            f"node-{node.index:02d} attempt-{node.attempt:02d} {status} "
            f"{elapsed:.3f}s {node.log_path.relative_to(ROOT)}"
        )
        for event in history[node.index]:
            print(f"  recovered: {event}")
        if node.error:
            print(f"  {node.error}")
            text = read_log(node.log_path).strip()
            if text:
                print("  serial:")
                for line in text.splitlines()[-8:]:
                    print(f"    {line}")

    if len(successes) < quorum:
        print(
            f"array result: quorum failed, {len(successes)}/{args.count} succeeded "
            f"(quorum {quorum})",
            file=sys.stderr,
        )
        return 1

    print(
        f"array result: {len(successes)}/{args.count} booted and emitted valid "
        f"recovery pulses under {args.scenario} visibility"
    )
    if failures:
        print(f"array warning: {len(failures)} node(s) failed after retries but quorum held")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
