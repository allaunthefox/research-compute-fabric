#!/usr/bin/env python3
"""
flac_dsp_node.py — PipeWire/FLAC DSP compute node registration and workload processor.

Every DSP-active node registers its capabilities in ene.dsp_nodes and processes
FLAC audio chunk workloads dispatched from the VCN router.

Receipt-bearing: every DSP operation emits a receipt to ~/.cache/flac_dsp_receipts.jsonl
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = os.environ.get("ENE_DB", os.path.expanduser("~/.cache/ene_substrate.db"))

RECEIPT_LOG = os.path.expanduser("~/.cache/flac_dsp_receipts.jsonl")


def _ensure_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def _query_pipewire() -> dict:
    result = {
        "pipewire_available": False,
        "pipewire_version": None,
        "virtual_soundcard_supported": False,
        "pw_loopback_available": False,
    }
    try:
        r = subprocess.run(
            ["pw-cli", "info", "0"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            result["pipewire_available"] = True
            for line in r.stdout.splitlines():
                if line.startswith("obj.id"):
                    result["pipewire_version"] = line.split("=")[-1].strip()
                    break
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        r = subprocess.run(
            ["pw-link", "-l"],
            capture_output=True, text=True, timeout=5
        )
        if "loopback" in r.stdout.lower():
            result["pw_loopback_available"] = True
            result["virtual_soundcard_supported"] = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return result


def _query_audio_hardware() -> dict:
    result = {
        "has_physical_audio": False,
        "audio_devices": [],
    }
    for probe in ["/proc/asound/cards", "/dev/snd"]:
        if Path(probe).exists():
            result["has_physical_audio"] = True
            break

    try:
        r = subprocess.run(
            ["cat", "/proc/asound/cards"],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0:
            result["audio_devices"] = [
                l.strip() for l in r.stdout.splitlines() if l.strip()
            ]
    except Exception:
        pass

    return result


def _get_max_sample_rate() -> int:
    rates = [44100, 48000, 88200, 96000, 176400, 192000]
    for rate in reversed(rates):
        try:
            r = subprocess.run(
                ["pw-link", "-o", f"alsa_output.null-@{rate}"],
                capture_output=True, timeout=2
            )
            if r.returncode == 0:
                return rate
        except Exception:
            pass
    return 48000


def _read_snd_hw_params() -> int:
    hw_params = Path("/proc/asound/card0/hw_params")
    if hw_params.exists():
        content = hw_params.read_text()
        for line in content.splitlines():
            if "rate" in line.lower():
                parts = line.split()
                for i, p in enumerate(parts):
                    if p.isdigit() and int(p) >= 44100:
                        return int(p)
    return 48000


def register_node(node_id: str) -> dict:
    _ensure_db()

    pw = _query_pipewire()
    hw = _query_audio_hardware()

    max_rate = _get_max_sample_rate() if pw["pipewire_available"] else 48000

    capabilities = {
        "node_id": node_id,
        "dsp_available": True,
        "pipewire_available": pw["pipewire_available"],
        "virtual_soundcard_supported": pw["virtual_soundcard_supported"],
        "physical_soundcard": hw["has_physical_audio"],
        "max_sample_rate": max_rate,
        "spectral_bands": 2048,
        "latency_target_us": 5120,
        "fft_size": 4096,
        "overlap_factor": 0.5,
        "last_seen_at": datetime.now(timezone.utc).isoformat(),
    }

    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO ene.dsp_nodes
        (node_id, dsp_available, pipewire_available, virtual_soundcard_supported,
         physical_soundcard, max_sample_rate, spectral_bands, latency_target_us,
         fft_size, overlap_factor, last_seen_at)
        VALUES (:node_id, :dsp_available, :pipewire_available,
                :virtual_soundcard_supported, :physical_soundcard, :max_sample_rate,
                :spectral_bands, :latency_target_us, :fft_size, :overlap_factor,
                :last_seen_at)
    """, capabilities)
    conn.commit()
    conn.close()

    receipt = {
        "schema": "flac_dsp_node_registration_v1",
        "version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "node_id": node_id,
        "action": "register",
        "capabilities": {k: v for k, v in capabilities.items() if k != "node_id"},
        "pipewire_probe": pw,
        "hardware_probe": hw,
        "claim_boundary": "node-capability-probe-only",
    }
    _write_receipt(receipt)

    return capabilities


def _write_receipt(receipt: dict) -> None:
    Path(RECEIPT_LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(RECEIPT_LOG, "a") as f:
        f.write(json.dumps(receipt) + "\n")


def process_flac_chunk(chunk_path: str, work_unit_id: str, parent_hash: Optional[str] = None) -> dict:
    import struct

    result = {
        "work_unit_id": work_unit_id,
        "chunk_path": chunk_path,
        "status": "unknown",
        "fft_peaks": [],
        "spectral_centroid_hz": 0.0,
        "rms_level_db": -60.0,
        "processing_node": os.environ.get("HOSTNAME", "unknown"),
    }

    try:
        import numpy as np

        import soundfile as sf
        data, samplerate = sf.read(chunk_path)

        if data.ndim > 1:
            data = data.mean(axis=1)

        n_fft = 4096
        hop = n_fft // 2
        window = np.hanning(n_fft)

        S = []
        for i in range(0, len(data) - n_fft, hop):
            frame = data[i:i + n_fft] * window
            spectrum = np.abs(np.fft.rfft(frame))
            S.append(spectrum)

        S = np.array(S)

        mean_spectrum = S.mean(axis=0)
        freqs = np.fft.rfftfreq(n_fft, 1.0 / samplerate)

        peak_indices = np.argsort(mean_spectrum)[-8:]
        result["fft_peaks"] = [
            {"freq_hz": float(freqs[i]), "magnitude": float(mean_spectrum[i])}
            for i in sorted(peak_indices)
        ]

        spectral_sum = np.sum(mean_spectrum)
        if spectral_sum > 0:
            result["spectral_centroid_hz"] = float(
                np.sum(freqs * mean_spectrum) / spectral_sum
            )

        rms = np.sqrt(np.mean(data ** 2))
        result["rms_level_db"] = float(20 * np.log10(rms + 1e-12))

        result["status"] = "ok"

    except ImportError:
        result["status"] = "missing_libs"
        result["error"] = "numpy or soundfile not available"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    receipt = {
        "schema": "flac_dsp_work_receipt_v1",
        "version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "work_unit_id": work_unit_id,
        "parent_hash": parent_hash,
        "result": {k: v for k, v in result.items() if k not in ("fft_peaks",)},
        "fft_peaks": result["fft_peaks"][:4],
        "processing_node": os.environ.get("HOSTNAME", "unknown"),
        "claim_boundary": "dsp-compute-result",
    }
    _write_receipt(receipt)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="FLAC DSP Node — PipeWire/FLAC compute worker")
    sub = parser.add_subparsers(dest="cmd", required=True)

    reg = sub.add_parser("register", help="Register this node's DSP capabilities")
    reg.add_argument("--node-id", required=True, help="Unique node identifier")

    proc = sub.add_parser("process", help="Process a FLAC chunk workload")
    proc.add_argument("--chunk", required=True, help="Path to FLAC chunk file")
    proc.add_argument("--work-unit-id", required=True, help="Work unit identifier")
    proc.add_argument("--parent-hash", help="Parent receipt hash for chaining")

    args = parser.parse_args()

    if args.cmd == "register":
        caps = register_node(args.node_id)
        print(json.dumps(caps, indent=2))
        return 0

    if args.cmd == "process":
        result = process_flac_chunk(args.chunk, args.work_unit_id, args.parent_hash)
        print(json.dumps(result, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
