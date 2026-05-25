#!/usr/bin/env python3
"""SSH-based remote node probe runner. Connects via Tailscale, executes probe script, returns JSON."""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROBE_DIR = Path(__file__).resolve().parent.parent / "nodes"


@dataclass
class ProbeResult:
    node: str
    ip: str
    optional: bool
    reachable: bool
    error: str | None
    data: dict[str, Any]
    elapsed_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "node": self.node,
            "ip": self.ip,
            "optional": self.optional,
            "reachable": self.reachable,
            "error": self.error,
            "data": self.data,
            "elapsed_ms": self.elapsed_ms,
        }


def run_probe(
    node_name: str,
    ip: str,
    ssh_target: str,
    probe_name: str,
    optional: bool = False,
    timeout: int = 30,
) -> ProbeResult:
    """
    SSH into a node and execute a probe script, returning parsed JSON.
    Uses ssh_target (e.g. 'root@100.102.173.61') directly. 'local' runs locally.
    """
    script_path = PROBE_DIR / f"{probe_name}.sh"
    if not script_path.exists():
        return ProbeResult(
            node=node_name, ip=ip, optional=optional, reachable=False,
            error=f"probe script not found: {script_path}", data={}, elapsed_ms=0,
        )

    t0 = time.monotonic()
    script_text = script_path.read_text()

    if ssh_target == "local":
        try:
            proc = subprocess.run(
                ["bash", "-s"],
                input=script_text,
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return ProbeResult(
                node=node_name, ip=ip, optional=optional, reachable=False,
                error="local timeout", data={},
                elapsed_ms=(time.monotonic() - t0) * 1000,
            )
        except Exception as exc:
            return ProbeResult(
                node=node_name, ip=ip, optional=optional, reachable=False,
                error=str(exc), data={},
                elapsed_ms=(time.monotonic() - t0) * 1000,
            )
        return _parse_output(node_name, ip, optional, proc, (time.monotonic() - t0) * 1000)

    try:
        proc = subprocess.run(
            [
                "ssh",
                "-o", "ConnectTimeout=5",
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", "BatchMode=yes",
                ssh_target,
                "bash -s",
            ],
            input=script_text,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            node=node_name, ip=ip, optional=optional, reachable=False,
            error="SSH timeout", data={},
            elapsed_ms=(time.monotonic() - t0) * 1000,
        )
    except Exception as exc:
        return ProbeResult(
            node=node_name, ip=ip, optional=optional, reachable=False,
            error=str(exc), data={},
            elapsed_ms=(time.monotonic() - t0) * 1000,
        )

    return _parse_output(node_name, ip, optional, proc, (time.monotonic() - t0) * 1000)


def _parse_output(node_name, ip, optional, proc, elapsed_ms):
    if proc.returncode != 0:
        return ProbeResult(
            node=node_name, ip=ip, optional=optional, reachable=False,
            error=f"exit {proc.returncode}: {proc.stderr.strip()[:300]}",
            data={}, elapsed_ms=elapsed_ms,
        )

    raw = proc.stdout.strip()
    if not raw:
        return ProbeResult(
            node=node_name, ip=ip, optional=optional, reachable=True,
            error="probe returned empty output", data={}, elapsed_ms=elapsed_ms,
        )

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        return ProbeResult(
            node=node_name, ip=ip, optional=optional, reachable=True,
            error=f"no JSON in output: {raw[:200]}", data={}, elapsed_ms=elapsed_ms,
        )

    try:
        data = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as exc:
        return ProbeResult(
            node=node_name, ip=ip, optional=optional, reachable=True,
            error=f"JSON parse error: {exc}", data={}, elapsed_ms=elapsed_ms,
        )

    return ProbeResult(
        node=node_name, ip=ip, optional=optional, reachable=True,
        error=None, data=data, elapsed_ms=elapsed_ms,
    )
