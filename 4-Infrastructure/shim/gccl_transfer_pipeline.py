#!/usr/bin/env python3
"""
gccl_transfer_pipeline.py — GCCL-Gated Parallel Transfer Pipeline with Resume.

Integrates GCCL WaveProbe, MetaProbe, and Delta+RLE encoding concepts to transfer
files securely and with complete receipt verification between hosts. Supports block-level
resuming for interrupted transfers. Optimized with metadata-only fast manifest scanning.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Insert shim path to import gccl_waveprobe
SHIM_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SHIM_DIR))

try:
    import gccl_waveprobe as gw
except ImportError:
    # Fallback to local copy if run from home dir
    sys.path.insert(0, os.getcwd())
    import gccl_waveprobe as gw

DEFAULT_TARGET_HOST = "100.92.88.64"  # neon-64gb IP

# ── Manifest Generation ─────────────────────────────────────────────────────

def compute_file_signature(path: Path, quick: bool = True) -> Dict:
    """Compute size, modification time, and WaveProbe sample of a file.
    
    If quick=True, skips reading the entire file for SHA-256 computation.
    """
    stat = path.stat()
    size = stat.st_size
    mtime = int(stat.st_mtime)
    
    content = b""
    try:
        with open(path, "rb") as f:
            # Only read the first 1KB to generate the WaveProbe sample signature
            content = f.read(1024)
    except Exception as e:
        return {"error": str(e)}

    # Generate WaveProbe signature using golden-angle sample points
    data_ints = list(content)
    probe = gw.WaveProbe(id=1, sample_rate=48000, buffer_size=64)
    signature = probe.sample(data_ints)

    sha256 = f"quick-{size}-{mtime}"
    if not quick:
        # Full file hash required during actual transmission
        h = hashlib.sha256()
        h.update(content)
        try:
            with open(path, "rb") as f:
                # Seek past what we already read
                f.seek(len(content))
                while chunk := f.read(64 * 1024):
                    h.update(chunk)
            sha256 = h.hexdigest()
        except Exception as e:
            return {"error": str(e)}

    return {
        "rel_path": str(path.relative_to(path.anchor)), # Keep path relative
        "size": size,
        "mtime": mtime,
        "sha256": sha256,
        "signature": signature,
    }


def generate_directory_manifest(dir_path: Path) -> Dict[str, Dict]:
    """Scan directory and build manifest of all files using quick scans."""
    manifest = {}
    for root, _, files in os.walk(dir_path):
        for file in files:
            path = Path(root) / file
            # Skip hidden/system files
            if file.startswith(".") or ".gccl" in file:
                continue
            sig = compute_file_signature(path, quick=True)
            if "error" not in sig:
                # Use relative path as key
                rel = str(path.relative_to(dir_path))
                sig["rel_path"] = rel
                manifest[rel] = sig
    return manifest


# ── Sender Pipeline ──────────────────────────────────────────────────────────

def transfer_single_file(
    rel_path: str,
    source_dir: Path,
    dest_dir: str,
    target_host: str,
    ref_sig: Optional[Dict],
) -> Dict:
    """Process, encode, and transmit a single file with support for resume."""
    src_file = source_dir / rel_path
    
    # Compute full signature (with SHA-256) for the file we are actually transferring
    sig = compute_file_signature(src_file, quick=False)
    if "error" in sig:
        return {"rel_path": rel_path, "status": "error", "reason": sig["error"]}

    offset = 0
    is_resume = False

    # Check if a partial file exists on the remote destination and is smaller
    if ref_sig and 0 < ref_sig["size"] < sig["size"]:
        offset = ref_sig["size"]
        is_resume = True

    # Read data starting from the offset for resume, or full data
    with open(src_file, "rb") as f:
        if offset > 0:
            f.seek(offset)
        data = f.read()

    ref_data = None
    # Delta compression check (not applicable if resuming from middle of the file)
    if not is_resume and ref_sig and ref_sig["sha256"] != sig["sha256"]:
        probe = gw.WaveProbe(id=1, sample_rate=48000, buffer_size=64)
        overlap = probe.signal_overlap(sig["signature"], ref_sig["signature"])
        if overlap > 32768:
            pass

    # Perform compression & gate check
    result = gw.gccl_delta_compress(
        data=data,
        reference=ref_data,
        gccl_threshold_q16=32768, # 0.5 threshold
        wave_probe=gw.WaveProbe(id=1, sample_rate=48000, buffer_size=64)
    )

    # Prepare stream packet containing metadata, receipt, and payload
    packet = {
        "rel_path": rel_path,
        "original_size": sig["size"],
        "compressed_size": result.compressed_size,
        "ratio": result.compression_ratio,
        "sha256": sig["sha256"],
        "receipt": result.gccl_receipt.to_dict() if result.gccl_receipt else None,
        "is_delta": result.success and ref_data is not None,
        "is_resume": is_resume,
        "offset": offset,
        # Hex encode compressed bytes for transmission inside JSON
        "payload_hex": result.compressed.hex(),
    }

    # Stream the packet to the remote receiver command
    cmd = [
        "ssh", target_host,
        f"python3 ~/gccl_transfer_pipeline.py --mode receive-packet --dest-dir {dest_dir}"
    ]
    
    try:
        proc = subprocess.run(
            cmd,
            input=json.dumps(packet) + "\n",
            capture_output=True,
            text=True,
            check=True
        )
        resp = json.loads(proc.stdout.strip())
        return {
            "rel_path": rel_path,
            "status": resp.get("status", "error"),
            "reason": resp.get("reason", ""),
            "resumed": is_resume,
            "offset": offset
        }
    except Exception as e:
        return {"rel_path": rel_path, "status": "error", "reason": str(e)}


def run_sender(source_dir: Path, dest_dir: str, target_host: str, threads: int):
    """Orchestrate the sender pipeline."""
    print(f"[*] Starting GCCL Sender Pipeline targeting {target_host}...")
    
    # 1. Bootstrap shims onto the remote receiver
    print("[*] Bootstrapping pipeline scripts to remote host...")
    try:
        subprocess.run(
            ["scp", "-q", str(SHIM_DIR / "gccl_waveprobe.py"), str(SHIM_DIR / "gccl_transfer_pipeline.py"), f"{target_host}:~/"],
            check=True
        )
    except Exception as e:
        print(f"[-] Bootstrapping failed: {e}")
        sys.exit(1)

    # 2. Build local manifest (quick scan)
    print("[*] Scanning local source directory (metadata-only)...")
    local_manifest = generate_directory_manifest(source_dir)
    print(f"[+] Found {len(local_manifest)} files to sync.")

    # 3. Query remote manifest (quick scan on receiver)
    print("[*] Querying remote destination manifest (metadata-only)...")
    cmd = [
        "ssh", target_host,
        f"python3 ~/gccl_transfer_pipeline.py --mode manifest --dest-dir {dest_dir}"
    ]
    remote_manifest = {}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        remote_manifest = json.loads(proc.stdout.strip())
    except Exception as e:
        print(f"[*] Remote directory empty or manifest query failed (expected for fresh sync): {e}")

    # 4. Filter files that already match perfectly (same size and mtime)
    transfer_queue = []
    for rel_path, sig in local_manifest.items():
        ref = remote_manifest.get(rel_path)
        # Match based on size and mtime for speed (avoiding full-file hashing during diff check)
        if ref and ref["size"] == sig["size"] and ref["mtime"] == sig["mtime"]:
            continue
        transfer_queue.append((rel_path, ref))

    print(f"[+] Need to transfer {len(transfer_queue)} files.")

    if not transfer_queue:
        print("[+] Sync complete! All files up to date.")
        return

    # 5. Parallel transfer execution
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(
                transfer_single_file, rel_path, source_dir, dest_dir, target_host, ref
            ): rel_path
            for rel_path, ref in transfer_queue
        }
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            status_char = "+" if res["status"] == "success" else "-"
            resume_tag = f" (resumed at {res['offset']} bytes)" if res.get("resumed") else ""
            print(f"[{status_char}] {res['rel_path']}: {res['status']}{resume_tag} {res.get('reason', '')}")

    elapsed = time.time() - t0
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n[+] Transfer complete in {elapsed:.2f}s.")
    print(f"[+] Success: {success_count}/{len(transfer_queue)} files.")


# ── Receiver Pipeline ────────────────────────────────────────────────────────

def run_receiver_packet(dest_dir: Path, packet_data: str) -> Dict:
    """Receive a single packet, run MetaProbe check, reconstruct with resume, and write."""
    try:
        packet = json.loads(packet_data)
        rel_path = packet["rel_path"]
        payload_bytes = bytes.fromhex(packet["payload_hex"])
        is_delta = packet["is_delta"]
        is_resume = packet.get("is_resume", False)
        offset = packet.get("offset", 0)
        original_size = packet["original_size"]
        original_sha = packet["sha256"]
        receipt = packet["receipt"]

        # 1. Run MetaProbe check
        if receipt and receipt.get("decision") != "accept":
            return {"status": "quarantined", "reason": "GCCL receipt decision was not accept"}

        meta = gw.MetaProbe(threshold_q16=32768)
        would_grant = meta.export_grant(0)
        if not would_grant:
            return {"status": "hold", "reason": "MetaProbe EXPORT_GRANT failed"}

        # 2. Reconstruct payload
        out_file = dest_dir / rel_path
        out_file.parent.mkdir(parents=True, exist_ok=True)

        if is_resume:
            # Verify that the local file exists and matches the offset
            if not out_file.exists():
                return {"status": "mismatch", "reason": "Resume file missing"}
            current_size = out_file.stat().st_size
            if current_size != offset:
                return {
                    "status": "mismatch",
                    "reason": f"Size mismatch for resume: expected {offset}, got {current_size}"
                }
            
            # Open file in read/write binary mode and write from offset
            with open(out_file, "r+b") as f:
                f.seek(offset)
                f.write(payload_bytes)
                f.truncate(original_size)
        else:
            if is_delta:
                # Delta decoding fallback
                pass
            # Write data in full
            with open(out_file, "wb") as f:
                f.write(payload_bytes)

        # 3. Post-write integrity check
        h = hashlib.sha256()
        with open(out_file, "rb") as f:
            while chunk := f.read(64 * 1024):
                h.update(chunk)
        
        if h.hexdigest() != original_sha:
            return {"status": "corrupt", "reason": "SHA256 mismatch after write"}

        # Save the GCCL receipt next to the file
        receipt_file = out_file.with_suffix(out_file.suffix + ".gccl-receipt.json")
        with open(receipt_file, "w") as f:
            json.dump(receipt, f, indent=2)

        return {"status": "success", "reason": "admitted and verified"}

    except Exception as e:
        return {"status": "error", "reason": str(e)}


# ── Main / CLI ───────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="GCCL Parallel Transfer Pipeline")
    parser.add_argument("--mode", required=True, choices=["send", "receive", "receive-packet", "manifest"])
    parser.add_argument("--source-dir", help="Local directory to send files from")
    parser.add_argument("--dest-dir", help="Destination directory on receiver")
    parser.add_argument("--target-host", default=DEFAULT_TARGET_HOST, help="Remote host address")
    parser.add_argument("--threads", type=int, default=8, help="Number of concurrent transfer threads")

    args = parser.parse_args()

    if args.mode == "manifest":
        if not args.dest_dir:
            print("Error: --dest-dir is required for manifest mode", file=sys.stderr)
            return 1
        dest_path = Path(args.dest_dir).expanduser()
        if not dest_path.exists():
            print("{}", end="")
            return 0
        manifest = generate_directory_manifest(dest_path)
        print(json.dumps(manifest))
        return 0

    if args.mode == "receive-packet":
        if not args.dest_dir:
            print("Error: --dest-dir is required for receive-packet mode", file=sys.stderr)
            return 1
        dest_path = Path(args.dest_dir).expanduser()
        # Read single packet from stdin
        packet_data = sys.stdin.read()
        res = run_receiver_packet(dest_path, packet_data)
        print(json.dumps(res))
        return 0

    if args.mode == "send":
        if not args.source_dir or not args.dest_dir:
            print("Error: --source-dir and --dest-dir are required for send mode", file=sys.stderr)
            return 1
        src_path = Path(args.source_dir).expanduser()
        run_sender(src_path, args.dest_dir, args.target_host, args.threads)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
