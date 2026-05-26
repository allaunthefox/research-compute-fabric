#!/usr/bin/env python3
"""Small HTTP proof server for Lean/Lake checks.

This is intentionally dependency-free so it can run on the Netcup Debian host
without a Python package bootstrap. It is a thin process wrapper around Lean and
Lake; a receipt records exactly what command was run and what output it gave.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import shlex
import subprocess
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


SERVER_NAME = "language-proof-server"
SERVER_VERSION = "0.1.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_REPO = "/srv/research-stack"
DEFAULT_LEAN_ROOT = "0-Core-Formalism/lean/Semantics"
MAX_BODY_BYTES = 2_000_000

last_activity: float = time.time()
_ACTIVITY_FILE = Path("/var/lib/language-proof-server/.last_activity")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bump_activity_file() -> None:
    try:
        _ACTIVITY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _ACTIVITY_FILE.write_text(str(last_activity))
    except Exception:
        pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def json_sha256(data: Any) -> str | None:
    if data is None:
        return None
    return sha256_text(json.dumps(data, sort_keys=True))


def env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser()


def repo_dir() -> Path:
    return env_path("PROOF_REPO_DIR", DEFAULT_REPO)


def lean_root() -> Path:
    configured = Path(os.environ.get("PROOF_LEAN_ROOT", DEFAULT_LEAN_ROOT))
    if configured.is_absolute():
        return configured
    return repo_dir() / configured


def work_dir() -> Path:
    path = env_path("PROOF_WORK_DIR", "/var/lib/language-proof-server/work")
    path.mkdir(parents=True, exist_ok=True)
    return path


def receipt_dir() -> Path:
    path = env_path("PROOF_RECEIPT_DIR", "/var/lib/language-proof-server/receipts")
    path.mkdir(parents=True, exist_ok=True)
    return path


def require_token(handler: BaseHTTPRequestHandler) -> bool:
    token = os.environ.get("PROOF_SERVER_TOKEN")
    if not token:
        return os.environ.get("PROOF_SERVER_ALLOW_NO_TOKEN") == "1"
    got = handler.headers.get("Authorization", "")
    return hmac.compare_digest(got, f"Bearer {token}")


def command_env() -> dict[str, str]:
    env = os.environ.copy()
    home = env.get("HOME", "/root")
    cargo = f"{home}/.cargo/bin"
    elan = f"{home}/.elan/bin"
    env["PATH"] = f"{elan}:{cargo}:{env.get('PATH', '')}"
    return env


def command_prefix() -> list[str]:
    raw = os.environ.get("PROOF_COMMAND_PREFIX", "").strip()
    return shlex.split(raw) if raw else []


def run_command(
    command: list[str],
    cwd: Path,
    input_payload: dict[str, Any],
    timeout_s: int,
) -> dict[str, Any]:
    started = time.time()
    full_command = command_prefix() + command
    command_display = " ".join(shlex.quote(part) for part in full_command)
    try:
        proc = subprocess.run(
            full_command,
            cwd=str(cwd),
            env=command_env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
        timed_out = False
        returncode = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = 124
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        stderr += f"\ncommand timed out after {timeout_s}s"

    elapsed_ms = int((time.time() - started) * 1000)
    ene_context = input_payload.get("ene_context")
    receipt = {
        "schema": "language_proof_server_receipt_v1",
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "generated_at_utc": now_iso(),
        "cwd": str(cwd),
        "command": command_display,
        "command_sha256": sha256_text(command_display),
        "input_sha256": sha256_text(json.dumps(input_payload, sort_keys=True)),
        "remote_addr": input_payload.get("remote_addr"),
        "user_agent": input_payload.get("user_agent"),
        "returncode": returncode,
        "success": returncode == 0 and not timed_out,
        "timed_out": timed_out,
        "elapsed_ms": elapsed_ms,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
        "ene_context": ene_context,
        "ene_context_sha256": json_sha256(ene_context),
    }
    receipt["receipt_sha256"] = sha256_text(json.dumps(receipt, sort_keys=True))

    receipt_path = receipt_dir() / f"{int(time.time() * 1000)}-{receipt['receipt_sha256'][:16]}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    return {
        "ok": receipt["success"],
        "receipt": receipt,
        "receipt_path": str(receipt_path),
        "stdout": stdout,
        "stderr": stderr,
        "ene_context": ene_context,
        "ene_context_sha256": json_sha256(ene_context),
    }


def health() -> dict[str, Any]:
    root = lean_root()
    checks: dict[str, Any] = {
        "repo_dir": str(repo_dir()),
        "lean_root": str(root),
        "proof_command_prefix": command_prefix(),
        "lean_root_exists": root.exists(),
        "lakefile_exists": (root / "lakefile.toml").exists(),
        "lean_toolchain_exists": (root / "lean-toolchain").exists(),
    }
    for command in ("elan", "lean", "lake", "git", "curl"):
        probe = subprocess.run(
            ["bash", "-lc", f"command -v {shlex.quote(command)} || true"],
            env=command_env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        checks[f"{command}_path"] = probe.stdout.strip()
    checks["ok"] = bool(
        checks["lean_root_exists"]
        and checks["lakefile_exists"]
        and checks["lean_path"]
        and checks["lake_path"]
    )
    return {
        "ok": checks["ok"],
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "time_utc": now_iso(),
        "last_activity_utc": datetime.fromtimestamp(last_activity, tz=timezone.utc).isoformat(),
        "checks": checks,
    }


def payload_timeout(payload: dict[str, Any], default: int = 120, maximum: int = 900) -> int:
    raw = payload.get("timeout_s", default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, maximum))


def handle_check(payload: dict[str, Any]) -> dict[str, Any]:
    code = str(payload.get("code") or "")
    if not code.strip():
        return {"ok": False, "error": "missing non-empty 'code'"}

    name = str(payload.get("name") or "agent_check")
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name)
    file_hash = sha256_text(code)[:16]
    path = work_dir() / f"{safe_name}-{file_hash}.lean"
    path.write_text(code)

    return run_command(
        ["lake", "env", "lean", str(path)],
        cwd=lean_root(),
        input_payload={"endpoint": "/lean/check", "path": str(path), **payload},
        timeout_s=payload_timeout(payload),
    )


def handle_lake_build(payload: dict[str, Any]) -> dict[str, Any]:
    target = str(payload.get("target") or "")
    allowed_targets = {
        item.strip()
        for item in os.environ.get("PROOF_ALLOWED_BUILD_TARGETS", "").split(",")
        if item.strip()
    }
    if allowed_targets and target not in allowed_targets:
        return {
            "ok": False,
            "error": "target not in PROOF_ALLOWED_BUILD_TARGETS",
            "target": target,
            "allowed_targets": sorted(allowed_targets),
        }
    command = ["lake", "build"]
    if target:
        command.append(target)
    return run_command(
        command,
        cwd=lean_root(),
        input_payload={"endpoint": "/lake/build", **payload},
        timeout_s=payload_timeout(payload, default=300, maximum=1800),
    )


class Handler(BaseHTTPRequestHandler):
    server_version = f"{SERVER_NAME}/{SERVER_VERSION}"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}", flush=True)

    def send_json(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        global last_activity
        last_activity = time.time()
        _bump_activity_file()
        if self.path.rstrip("/") in ("", "/health"):
            self.send_json(HTTPStatus.OK, health())
            return
        self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        global last_activity
        last_activity = time.time()
        _bump_activity_file()
        if not require_token(self):
            self.send_json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
            return

        length = int(self.headers.get("Content-Length") or "0")
        if length > MAX_BODY_BYTES:
            self.send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"ok": False, "error": "body too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": f"invalid JSON: {exc}"})
            return

        try:
            payload["remote_addr"] = self.client_address[0]
            payload["user_agent"] = self.headers.get("User-Agent")
            if self.path.rstrip("/") == "/lean/check":
                self.send_json(HTTPStatus.OK, handle_check(payload))
            elif self.path.rstrip("/") == "/lake/build":
                self.send_json(HTTPStatus.OK, handle_lake_build(payload))
            else:
                self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
        except Exception as exc:
            self.send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": f"{type(exc).__name__}: {exc}"},
            )


def main() -> None:
    host = os.environ.get("PROOF_SERVER_HOST", DEFAULT_HOST)
    port = int(os.environ.get("PROOF_SERVER_PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((host, port), Handler)
    _bump_activity_file()

    def _heartbeat() -> None:
        while True:
            time.sleep(60)
            _bump_activity_file()

    threading.Thread(target=_heartbeat, daemon=True).start()
    print(f"{SERVER_NAME} listening on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
