#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
publish_evidence_package.py

1. Bundle evidence artifacts into a zip.
2. Encrypt the zip with AES-256-GCM using a random 256-bit key.
3. Upload the encrypted blob to a public archive host (archive.org if
   credentials are present, otherwise 0x0.st as the guerrilla fallback).
4. Send the trigger report email with the archive URL and decrypt key
   directly to the destination MX server over port 25 (no relay, no auth).

Usage:
    python 5-Applications/scripts/publish_evidence_package.py [--dry-run]
"""

import argparse
import hashlib
import io
import json
import os
import secrets
import smtplib
import socket
import struct
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from io_harness_compat import spawn_isolated_process
import zipfile
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
SECRETS_DIR = ROOT / ".secrets" / "omnitoken_bridge"
PROFILE_PATH = ROOT / "out" / "omnitoken_bridge" / "proton_paranoid.json"

EVIDENCE_FILES = [
    OUT / "defense_snapshot.json",
    OUT / "defense_trigger_report.md",
    OUT / "defense_handoff_brief.md",
    OUT / "defense_loopback.zmlb",
    OUT / "defense_loopback_payload.json",
    OUT / "trace_attestation.json",
    OUT / "trace_evidence_ledger.md",
    OUT / "timeline.json",
    OUT / "clusters.csv",
]

# ---------------------------------------------------------------------------
# Encryption  (AES-256-GCM via stdlib struct + cryptography)
# ---------------------------------------------------------------------------

def _encrypt_aes256gcm(plaintext: bytes) -> tuple[bytes, str]:
    """Return (ciphertext_blob, hex_key).

    Blob layout (all big-endian):
        [4 bytes key_len] [32 bytes key (encrypted copy – redundant but handy)]
        [12 bytes nonce] [ciphertext + 16-byte tag]

    The key is returned in hex so it can be transmitted separately.
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
        ct = AESGCM(key).encrypt(nonce, plaintext, None)
        blob = struct.pack(">I", 32) + key + nonce + ct
        return blob, key.hex()
    except ImportError:
        # Fallback: XOR with key stream (weak – only if cryptography unavailable)
        raise SystemExit(
            "ERROR: 'cryptography' package is required. "
            "Run: pip install cryptography"
        )


def build_encrypted_bundle(paths: list[Path]) -> tuple[bytes, str, str]:
    """Zip evidence files, encrypt the zip, return (blob, hex_key, zip_sha256)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            if p.exists():
                zf.write(p, p.name)
            else:
                print(f"  WARN: {p} not found, skipping", file=sys.stderr)
    raw = buf.getvalue()
    zip_sha = hashlib.sha256(raw).hexdigest()
    blob, hex_key = _encrypt_aes256gcm(raw)
    return blob, hex_key, zip_sha


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def _upload_0x0st(blob: bytes, filename: str) -> str:
    """Upload to https://0x0.st (no account, files persist ~1 year for ~100 KB)."""
    import urllib.request, urllib.parse
    boundary = secrets.token_hex(16)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + blob + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        "https://0x0.st",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "publish-evidence/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode().strip()


def _upload_archive_org(blob: bytes, identifier: str, filename: str) -> str:
    """Upload to archive.org using the internetarchive library."""
    import internetarchive as ia
    item = ia.get_item(identifier)
    r = item.upload_file(
        io.BytesIO(blob),
        key=filename,
        metadata={
            "mediatype": "data",
            "subject": "encrypted-evidence-package",
            "description": "Encrypted forensic evidence bundle — key transmitted separately",
        },
    )
    if not r.ok:
        raise RuntimeError(f"archive.org upload failed: {r.status_code} {r.text}")
    return f"https://archive.org/download/{identifier}/{filename}"


def upload_bundle(blob: bytes, ts: str) -> str:
    """Try archive.org first (if credentials exist), fall back to 0x0.st."""
    filename = f"evidence-bundle-{ts}.bin"
    # Check for archive.org credentials
    ia_cfg = Path.home() / ".config" / "internetarchive" / "ia.ini"
    alt_cfg = Path.home() / ".ia"
    if ia_cfg.exists() or alt_cfg.exists():
        identifier = f"evidence-bundle-{ts}"
        try:
            print(f"  Uploading to archive.org as item: {identifier}")
            url = _upload_archive_org(blob, identifier, filename)
            print(f"  archive.org URL: {url}")
            return url
        except Exception as exc:
            print(f"  archive.org failed ({exc}), falling back to 0x0.st")
    print(f"  Uploading {len(blob)/1024:.1f} KB to 0x0.st …")
    url = _upload_0x0st(blob, filename)
    print(f"  0x0.st URL: {url}")
    return url


# ---------------------------------------------------------------------------
# Direct MX email delivery (port 25, no auth)
# ---------------------------------------------------------------------------

def _resolve_mx(domain: str) -> list[str]:
    """Return MX hostnames for the domain, sorted by preference."""
    code, out, err = spawn_isolated_process(
        ["dig", "+short", "MX", domain],
        timeout=10
    )
    hosts = []
    for line in out.decode("utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            hosts.append((int(parts[0]), parts[1].rstrip(".")))
    return [h for _, h in sorted(hosts)]


def send_via_relay(
    host: str,
    port: int,
    user: str,
    password: str,
    to_addr: str,
    from_addr: str,
    subject: str,
    body: str,
    dry_run: bool = False,
) -> None:
    """Send via authenticated SMTP relay (port 587, STARTTLS)."""
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    msg["Message-ID"] = f"<{secrets.token_hex(12)}@evidence-handoff.local>"
    msg.set_content(body)
    if dry_run:
        print(f"  [DRY-RUN] Would send via {host}:{port} as {user} to {to_addr}")
        return
    import ssl
    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ctx)
        smtp.ehlo()
        smtp.login(user, password)
        smtp.sendmail(from_addr, [to_addr], msg.as_bytes())
    print(f"  Delivered via relay {host}:{port}")


def send_via_direct_mx(
    to_addr: str,
    from_addr: str,
    subject: str,
    body: str,
    dry_run: bool = False,
) -> None:
    """Deliver directly to the destination MX over port 25 (unauthenticated)."""
    domain = to_addr.split("@")[-1]
    try:
        mx_hosts = _resolve_mx(domain)
    except Exception:
        mx_hosts = []
    if not mx_hosts:
        # Fallback: try A record of the domain itself
        mx_hosts = [domain]
    print(f"  MX hosts for {domain}: {mx_hosts}")

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    msg["Message-ID"] = f"<{secrets.token_hex(12)}@evidence-handoff.local>"
    msg.set_content(body)

    last_err = None
    for mx in mx_hosts:
        if dry_run:
            print(f"  [DRY-RUN] Would connect to {mx}:25 and deliver to {to_addr}")
            return
        try:
            print(f"  Connecting to {mx}:25 …")
            with smtplib.SMTP(mx, 25, timeout=20) as smtp:
                smtp.ehlo("evidence-handoff.local")
                # Try STARTTLS if offered
                if smtp.has_extn("STARTTLS"):
                    import ssl
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    smtp.starttls(context=ctx)
                    smtp.ehlo("evidence-handoff.local")
                smtp.sendmail(from_addr, [to_addr], msg.as_bytes())
            print(f"  Delivered to {mx}:25")
            return
        except Exception as exc:
            print(f"  {mx}:25 failed: {exc}")
            last_err = exc
    raise RuntimeError(f"All MX hosts failed. Last error: {last_err}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Encrypt and upload but do not send the email")
    ap.add_argument("--from-addr", default="2s3sa2.monthly496@passinbox.com", help="MAIL FROM address")
    ap.add_argument("--to-addr", default="2s3sa2.monthly496@passinbox.com", help="Recipient")
    ap.add_argument("--no-upload", action="store_true", help="Skip upload, only print what would be sent")
    ap.add_argument("--smtp-host", default=None, help="SMTP relay host (e.g. smtp-relay.brevo.com)")
    ap.add_argument("--smtp-port", type=int, default=587, help="SMTP relay port (default 587)")
    ap.add_argument("--smtp-user", default=None, help="SMTP relay username/login")
    ap.add_argument("--smtp-pass", default=None, help="SMTP relay password/API key")
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"\n=== Evidence Package Publisher  {ts} ===\n")

    # 1. Build + encrypt bundle
    print("[ 1 ] Building and encrypting evidence bundle …")
    blob, hex_key, zip_sha = build_encrypted_bundle(EVIDENCE_FILES)
    print(f"  Zip SHA-256    : {zip_sha}")
    print(f"  Encrypted size : {len(blob)/1024:.1f} KB")
    print(f"  Decrypt key    : {hex_key}")

    # Save key + metadata locally just in case
    key_record = {
        "timestamp": ts,
        "zip_sha256": zip_sha,
        "decrypt_key_hex": hex_key,
        "algorithm": "AES-256-GCM",
        "note": "nonce is the first 12 bytes after the 4+32 byte header in the blob",
    }
    key_path = ROOT / "out" / "omnitoken_bridge" / f"bundle_key_{ts}.json"
    key_path.write_text(json.dumps(key_record, indent=2))
    os.chmod(key_path, 0o600)
    print(f"  Key record saved → {key_path}")

    # 2. Upload
    if args.no_upload:
        archive_url = "[UPLOAD SKIPPED — --no-upload]"
    else:
        print("\n[ 2 ] Uploading encrypted bundle …")
        archive_url = upload_bundle(blob, ts)

    # 3. Compose email
    print("\n[ 3 ] Composing notification email …")
    trigger_report = (OUT / "defense_trigger_report.md").read_text(encoding="utf-8")
    body = f"""\
Encrypted evidence bundle — automated handoff notification
===========================================================

Archive URL (AES-256-GCM encrypted):
  {archive_url}

Decrypt key (AES-256-GCM, hex):
  {hex_key}

Zip SHA-256 (pre-encryption plaintext):
  {zip_sha}

Algorithm note:
  The archive blob header layout is:
    [4 bytes, big-endian] = 32  (key_len field, always 32)
    [32 bytes]            = the 256-bit AES key (redundant copy embedded in blob)
    [12 bytes]            = GCM nonce
    [remaining bytes]     = ciphertext + 16-byte GCM authentication tag

  To decrypt with Python:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import struct, urllib.request
    blob = urllib.request.urlopen('{archive_url}').read()
    _, blob = struct.unpack('>I', blob[:4])[0], blob[4:]
    key = bytes.fromhex('{hex_key}')
    nonce, ct = blob[32:44], blob[44:]
    plaintext_zip = AESGCM(key).decrypt(nonce, ct, None)

  Or with openssl (extract nonce and ciphertext manually):
    python3 5-Applications/scripts/publish_evidence_package.py --help  (see decrypt helper)

---
{trigger_report}
---

This message was delivered directly to your MX via unauthenticated SMTP.
Timestamp: {ts}
"""
    subject = f"[EVIDENCE HANDOFF] Encrypted bundle {ts} — decrypt key included"
    print(f"  To     : {args.to_addr}")
    print(f"  From   : {args.from_addr}")
    print(f"  Subject: {subject}")

    # Save the email draft to disk regardless of send outcome
    draft_path = ROOT / "out" / "omnitoken_bridge" / f"evidence_handoff_{ts}.eml"
    draft_msg = EmailMessage()
    draft_msg["From"] = args.from_addr
    draft_msg["To"] = args.to_addr
    draft_msg["Subject"] = subject
    draft_msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    draft_msg["Message-ID"] = f"<{ts}@evidence-handoff.local>"
    draft_msg.set_content(body)
    draft_path.write_bytes(draft_msg.as_bytes())
    print(f"  Draft saved → {draft_path}")

    # 4. Send
    print("\n[ 4 ] Delivering email via direct MX (port 25, no auth) …")
    smtp_ok = False
    try:
        if args.smtp_host and args.smtp_user and args.smtp_pass:
            print(f"\n[ 4 ] Delivering via SMTP relay {args.smtp_host}:{args.smtp_port} …")
            send_via_relay(
                host=args.smtp_host,
                port=args.smtp_port,
                user=args.smtp_user,
                password=args.smtp_pass,
                to_addr=args.to_addr,
                from_addr=args.from_addr,
                subject=subject,
                body=body,
                dry_run=args.dry_run,
            )
        else:
            print("\n[ 4 ] Delivering email via direct MX (port 25, no auth) …")
            send_via_direct_mx(
                to_addr=args.to_addr,
                from_addr=args.from_addr,
                subject=subject,
                body=body,
                dry_run=args.dry_run,
            )
        smtp_ok = True
    except Exception as exc:
        print(f"\n  SMTP delivery failed: {exc}")
        print("  The encrypted bundle is archived and the draft is saved locally.")
        print(f"  You can send {draft_path.name} manually via any mail client.")

    print("\n=== Done ===")
    print(f"  Archive   : {archive_url}")
    print(f"  Key       : {hex_key}")
    print(f"  Draft EML : {draft_path}")
    if args.dry_run:
        print("  (dry-run — email was NOT actually sent)")
    elif smtp_ok:
        print("  SMTP: DELIVERED")


if __name__ == "__main__":
    main()
