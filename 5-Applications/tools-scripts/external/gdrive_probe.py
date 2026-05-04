#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""tunnel probe: bidirectional omnitoken-welded pipeline against rclone FUSE Drive.

Ingress  — GDrive FUSE files → tunnel register → clone into local tunnel_cache
Egress   — probe result sidecars written back to Drive (--egress-dir)
Surface  — egress_surface.json surface_bus patched with 'gdrive_fuse_bidir' domain

Each file under --drive-dir is fed into decide_tunnel_generalist() as a
tunnel_source_file node. Both directions are registered in the omnitoken surface
so the weld sees GDrive as a bidirectional transport domain.

Usage:
    python 5-Applications/scripts/tunnel_gdrive_probe.py
    python 5-Applications/scripts/tunnel_gdrive_probe.py --top-n 5 --inject-surface
    python 5-Applications/scripts/tunnel_gdrive_probe.py --one-line --one-line-delim ";"
    python 5-Applications/scripts/tunnel_gdrive_probe.py --no-egress  # ingress-only, no write-back
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import os
import sys
import zlib
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from scripts.weld_omnitoken_surface import (
        decide_tunnel_generalist,
        TUNNEL_REGISTER_TTL_SECONDS,
        OMNI_SURFACE_PATH,
        utc_now,
        assert_surface_write_safe,
    )
except ImportError:
    from weld_omnitoken_surface import (  # type: ignore
        decide_tunnel_generalist,
        TUNNEL_REGISTER_TTL_SECONDS,
        OMNI_SURFACE_PATH,
        utc_now,
        assert_surface_write_safe,
    )

DEFAULT_DRIVE_DIR = Path.home() / "Gdrive" / "Research Documents"
DEFAULT_EGRESS_DIR = Path.home() / "Gdrive" / "_omnitoken_probe"
DEFAULT_TOP_N = 20


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024  # type: ignore[assignment]
    return str(n)


def collect_files(drive_dir: Path, top_n: int) -> List[Path]:
    """Collect up to top_n regular files from drive_dir (recursive)."""
    files: List[Path] = []
    try:
        # Using rglob('*') to get everything recursively
        # Note: glob/rglob handles hidden files differently depending on OS/Version,
        # but usually '*' doesn't match dotfiles. We can use a pattern or just walk.
        for entry in sorted(drive_dir.rglob('*')):
            if entry.is_file():
                files.append(entry)
            if len(files) >= top_n:
                break
    except PermissionError as e:
        print(f"ERROR accessing {drive_dir}: {e}", file=sys.stderr)
        sys.exit(1)
    return files


def probe_file(path: Path, ttl_seconds: int) -> Dict[str, Any]:
    node: Dict[str, Any] = {
        "name": f"gdrive::{path.name}",
        "tunnel_source_file": str(path),
    }
    result = decide_tunnel_generalist(node, foam_profile="balanced", tunnel_ttl_seconds=ttl_seconds)
    result["_probe_filename"] = path.name
    result["_probe_path"] = str(path)
    result["_probe_size_bytes"] = path.stat().st_size if path.exists() else 0
    result["_direction"] = "ingress"
    return result


def _compress_bytes(data: bytes, algo: str) -> bytes:
    if algo == "zlib":
        return zlib.compress(data)
    if algo == "gzip":
        return gzip.compress(data)
    # default fallback
    return data


def _compress_and_b64url(data: bytes) -> str:
    comp = zlib.compress(data)
    b64 = base64.urlsafe_b64encode(comp).rstrip(b"=")
    return b64.decode("ascii")


def write_egress_sidecar(result: Dict[str, Any], egress_dir: Path, compress: bool = False, algo: str = "zlib") -> str:
    """Write probe result back to Drive as a JSON sidecar (egress direction).

    Returns the path written, or empty string on failure.
    """
    egress_dir.mkdir(parents=True, exist_ok=True)
    fname = result.get("_probe_filename", "unknown")
    sidecar_name = f"{fname}.tunnel_probe.json"
    sidecar_path = egress_dir / sidecar_name

    wavestate = result.get("wavestate")
    payload: Dict[str, Any] = {
        "schema": "tunnel-probe-egress/v1",
        "direction": "egress",
        "source_file": result.get("_probe_path", ""),
        "status": result.get("status", "?"),
        "register_id": result.get("register_id", ""),
        "register_state": result.get("register_state", ""),
        "register_expires_utc": result.get("register_expires_utc", ""),
        "generalist_decision": result.get("generalist_decision", ""),
        "wavestate": wavestate if isinstance(wavestate, dict) else {},
        "rebuilt_path": result.get("rebuilt_path", ""),
        "written_utc": utc_now(),
    }
    text = json.dumps(payload, indent=2) + "\n"
    try:
        # Always write human-readable JSON sidecar for compatibility
        sidecar_path.write_text(text, encoding="utf-8")
    except OSError:
        return ""

    # Optionally write compressed sidecar alongside the JSON
    if compress:
        try:
            if algo == "zlib+b64":
                # write base64url(zlib(json)) as text file
                b64text = _compress_and_b64url(text.encode("utf-8"))
                comp_path = egress_dir / (sidecar_name + ".zlib.b64")
                comp_path.write_text(b64text + "\n", encoding="utf-8")
                return str(comp_path)
            else:
                comp_bytes = _compress_bytes(text.encode("utf-8"), algo)
                comp_ext = "zlib" if algo == "zlib" else "gz"
                comp_path = egress_dir / (sidecar_name + f".{comp_ext}")
                comp_path.write_bytes(comp_bytes)
                return str(comp_path)
        except OSError:
            # if compression write fails, fall back to JSON path
            return str(sidecar_path)

    return str(sidecar_path)


def inject_surface_domain(
    probe_results: List[Dict[str, Any]],
    drive_dir: Path,
    egress_dir: Path,
) -> None:
    """Patch egress_surface.json to register GDrive FUSE as a bidirectional domain.

    Adds surface_bus.domains.gdrive_fuse_bidir so the omnitoken weld sees the
    Drive mount as both an ingress source and egress destination.
    """
    if not OMNI_SURFACE_PATH.exists():
        # Surface not yet generated; nothing to patch — weld needs to run first
        return

    try:
        surface: Dict[str, Any] = json.loads(OMNI_SURFACE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    ok_count = sum(1 for r in probe_results if r.get("status") == "ok")
    err_count = len(probe_results) - ok_count

    surface_bus: Dict[str, Any] = dict(surface.get("surface_bus") or {})
    domains: Dict[str, Any] = dict(surface_bus.get("domains") or {})

    domains["gdrive_fuse_bidir"] = {
        "domain": "gdrive_fuse_bidir",
        "direction": "bidirectional",
        "fuse_backend": "rclone",
        "rclone_remote": "Gdrive",
        "mount_point": str(drive_dir.parent),
        "ingress_path": str(drive_dir),
        "egress_path": str(egress_dir),
        "transport": "tunnel",
        "files_probed": len(probe_results),
        "files_committed_ingress": ok_count,
        "files_errored": err_count,
        "updated_utc": utc_now(),
    }

    surface_bus["schema"] = str(surface_bus.get("schema") or "omnitoken-surface-bus/v1")
    surface_bus["agnostic"] = True
    surface_bus["domains"] = domains
    surface["surface_bus"] = surface_bus
    surface["updated_utc"] = utc_now()

    assert_surface_write_safe(surface, scope="gdrive_fuse_probe_injection")
    OMNI_SURFACE_PATH.write_text(json.dumps(surface, indent=2) + "\n", encoding="utf-8")


def render_table(results: List[Dict[str, Any]], egress_written: List[str]) -> None:
    print(f"\n{'FILE':<42}  {'STATUS':<12}  {'TRANSITIONS':<52}  {'SIZE':>8}  {'EGRESS':>6}  {'EXPIRES_UTC'}")
    print("-" * 148)
    for idx, r in enumerate(results):
        fname = r.get("_probe_filename", "")[:41]
        status = r.get("status", "?")
        size_str = _fmt_bytes(int(r.get("_probe_size_bytes", 0)))
        expires = r.get("register_expires_utc", "–")
        transitions = r.get("register_state_transitions", [])
        trans_str = " → ".join(t.get("state", "?") for t in transitions) if transitions else r.get("reason", "–")
        wrote = "ok" if idx < len(egress_written) and egress_written[idx] else "skip"
        print(f"{fname:<42}  {status:<12}  {trans_str:<52}  {size_str:>8}  {wrote:>6}  {expires}")
    print()


def render_one_line(results: List[Dict[str, Any]], egress_written: List[str], delim: str) -> None:
    for rank, r in enumerate(results, 1):
        fname = r.get("_probe_filename", "")
        status = r.get("status", "?")
        transitions = r.get("register_state_transitions", [])
        final_state = transitions[-1].get("state", "–") if transitions else r.get("reason", "–")
        register_id = r.get("register_id", "–")
        expires = r.get("register_expires_utc", "–")
        size_str = _fmt_bytes(int(r.get("_probe_size_bytes", 0)))
        wavestate = r.get("wavestate")
        sha: str
        if isinstance(wavestate, dict) and "sha256" in wavestate:
            sha = f"{wavestate['sha256']}"[:16]
        else:
            sha = "–"
        wrote = "egress_ok" if rank - 1 < len(egress_written) and egress_written[rank - 1] else "egress_skip"
        parts: List[str] = [str(rank), fname, status, final_state, size_str, sha, wrote, expires, register_id]
        print(delim.join(parts))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drive-dir", default=str(DEFAULT_DRIVE_DIR), metavar="PATH",
                    help="Ingress: Drive directory to probe (default: %(default)s)")
    ap.add_argument("--egress-dir", default=str(DEFAULT_EGRESS_DIR), metavar="PATH",
                    help="Egress: Drive directory to write probe sidecars back to (default: %(default)s)")
    ap.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, metavar="N",
                    help="Max files to probe (default: %(default)s)")
    ap.add_argument("--ttl", type=int, default=TUNNEL_REGISTER_TTL_SECONDS, metavar="SECONDS",
                    help="tunnel register TTL in seconds (default: %(default)s)")
    ap.add_argument("--no-egress", action="store_true",
                    help="Skip writing sidecar JSONs back to Drive (ingress-only mode)")
    ap.add_argument("--inject-surface", action="store_true",
                    help="Patch egress_surface.json surface_bus with gdrive_fuse_bidir domain")
    ap.add_argument("--compress", action="store_true",
                    help="Also write a compressed sidecar alongside the JSON")
    ap.add_argument("--compress-algo", choices=["zlib", "gzip", "zlib+b64"], default="zlib",
                    help="Compression algorithm for sidecars (default: %(default)s)")
    ap.add_argument("--one-line", action="store_true",
                    help="Pipe-friendly one-line-per-file output")
    ap.add_argument("--one-line-delim", default=";", metavar="CHAR",
                    help="Delimiter for --one-line mode (default: %(default)r)")
    args = ap.parse_args()

    drive_dir = Path(os.path.expanduser(args.drive_dir))
    egress_dir = Path(os.path.expanduser(args.egress_dir))

    if not drive_dir.exists():
        print(f"ERROR: drive dir not found: {drive_dir}", file=sys.stderr)
        print("Is the rclone FUSE mount running? Check: systemctl --user status rclone-gdrive.service", file=sys.stderr)
        sys.exit(1)

    files = collect_files(drive_dir, args.top_n)
    if not files:
        print(f"No files found in {drive_dir}", file=sys.stderr)
        sys.exit(0)

    if not args.one_line:
        mode_str = "ingress-only" if args.no_egress else "bidirectional"
        print(f"[{mode_str}] Probing {len(files)} files")
        print(f"  ingress : {drive_dir}")
        if not args.no_egress:
            print(f"  egress  : {egress_dir}")
        print(f"  cache   : {ROOT / 'out' / 'omnitoken_bridge' / 'tunnel_cache'}")
        print(f"  TTL     : {args.ttl}s")
        if args.inject_surface:
            print(f"  surface : {OMNI_SURFACE_PATH}")

    # Ingress: probe each file through the tunnel pipeline
    results: List[Dict[str, Any]] = []
    for f in files:
        results.append(probe_file(f, args.ttl))

    # Egress: write sidecar JSONs back to Drive
    egress_written: List[str] = []
    if not args.no_egress:
        for r in results:
            egress_written.append(write_egress_sidecar(r, egress_dir, compress=args.compress, algo=args.compress_algo))
    else:
        egress_written = ["" for _ in results]

    # Surface injection: register both directions in egress_surface.json
    if args.inject_surface:
        inject_surface_domain(results, drive_dir, egress_dir)
        if not args.one_line:
            print("  surface patched with gdrive_fuse_bidir domain")

    if args.one_line:
        render_one_line(results, egress_written, args.one_line_delim)
    else:
        render_table(results, egress_written)

        ok = sum(1 for r in results if r.get("status") == "ok")
        err = len(results) - ok
        egress_ok = sum(1 for p in egress_written if p)
        print(f"Ingress: {ok} committed  |  {err} unavailable/error")
        if not args.no_egress:
            print(f"Egress : {egress_ok}/{len(results)} sidecars written to Drive")
        print()


if __name__ == "__main__":
    main()
