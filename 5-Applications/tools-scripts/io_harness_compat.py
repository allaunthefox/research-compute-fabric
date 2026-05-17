#!/usr/bin/env python3
"""Compatibility helpers for Warden-bounded scripts.

Several tool scripts were rewritten to route process spawning and network
fetches through this module. The module is intentionally tiny: it centralizes
the boundary without changing each caller's payload logic.
"""
from __future__ import annotations

import subprocess
import urllib.request
from collections.abc import Mapping, Sequence
from typing import Any


def spawn_isolated_process(
    argv: Sequence[str],
    *,
    timeout: float | None = None,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    input: bytes | None = None,
) -> tuple[int, bytes, bytes]:
    """Run a subprocess without a shell and return ``(code, stdout, stderr)``."""
    result = subprocess.run(
        list(argv),
        input=input,
        capture_output=True,
        timeout=timeout,
        cwd=cwd,
        env=dict(env) if env is not None else None,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def fetch_network_resource(
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    timeout: float | None = None,
    method: str = "GET",
    data: bytes | None = None,
    **_unused: Any,
) -> bytes:
    """Fetch a URL and return response bytes."""
    req = urllib.request.Request(
        url,
        data=data,
        headers=dict(headers or {}),
        method=method,
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()
