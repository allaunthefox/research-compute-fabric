#!/usr/bin/env python3
"""EC2 idle watchdog: shuts down the instance after a configurable idle period."""

import os
import sys
import time
import subprocess


ACTIVITY_FILE = "/var/lib/language-proof-server/.last_activity"
DEFAULT_IDLE_MINUTES = 15


def main() -> int:
    idle_minutes_str = os.environ.get("IDLE_MINUTES", str(DEFAULT_IDLE_MINUTES))
    try:
        idle_minutes = float(idle_minutes_str)
    except ValueError:
        print(f"Invalid IDLE_MINUTES value: {idle_minutes_str!r}", file=sys.stderr)
        return 1

    idle_seconds = idle_minutes * 60
    now = time.time()

    if not os.path.exists(ACTIVITY_FILE):
        print(f"Activity file {ACTIVITY_FILE} missing; instance idle. Scheduling shutdown.")
        subprocess.run(["sudo", "shutdown", "-h", "+1"], check=True)
        return 0

    try:
        with open(ACTIVITY_FILE, "r") as f:
            raw = f.read().strip()
        last_activity = float(raw)
    except (OSError, ValueError) as exc:
        print(f"Cannot read activity file {ACTIVITY_FILE}: {exc}; scheduling shutdown.")
        subprocess.run(["sudo", "shutdown", "-h", "+1"], check=True)
        return 0

    elapsed = now - last_activity
    if elapsed > idle_seconds:
        print(
            f"Instance idle for {elapsed / 60:.1f} minutes "
            f"(threshold {idle_minutes} min). Scheduling shutdown."
        )
        subprocess.run(["sudo", "shutdown", "-h", "+1"], check=True)
        return 0

    print(f"Idle check passed ({elapsed / 60:.1f} min < {idle_minutes} min).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
