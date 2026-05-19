#!/usr/bin/env python3
# PTOS: LAYER=STORE / DOMAIN=COMPUTE / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
waveprobe_rgflow_teleport.py — Waveform teleport shim.

Reads a WAV file (or a raw PCM array), calls the Lean WaveformTeleport
module via subprocess, and emits a JSON TeleportReceipt.

Shim boundary (per AGENTS.md §7.1):
  ALLOWED:  WAV parsing, SHA-256 hashing, JSON serialisation, subprocess spawn
  FORBIDDEN: RG decimation logic, beta-residual computation, sigma_q arithmetic
             — all of that lives in WaveformTeleport.lean.

Usage:
    python3 4-Infrastructure/shim/waveprobe_rgflow_teleport.py \
        --wav 2-Search-Space/simulations/matter-frequencies/wav-files/caffeine_fade_96k.wav \
        --out /tmp/caffeine_teleport_receipt.json

    python3 4-Infrastructure/shim/waveprobe_rgflow_teleport.py \
        --wav <path> --max-depth 32 --out <receipt.json>

Environment:
    LEAN_BIN   path to SemanticsCli binary
               default: 0-Core-Formalism/lean/Semantics/.lake/build/bin/SemanticsCli
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── repo root ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]

LEAN_BIN_DEFAULT = (
    REPO_ROOT
    / "0-Core-Formalism/lean/Semantics/.lake/build/bin/SemanticsCli"
)

CLAIM_BOUNDARY = "waveform-teleport-rg-attractor-only"


# ── WAV helpers (shim-only: read bytes, hash bytes) ──────────────────────────

def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_words(data: bytes) -> list[int]:
    """Return the SHA-256 digest as 8 × uint32 words (big-endian)."""
    digest = hashlib.sha256(data).digest()
    return list(struct.unpack(">8I", digest))


def _read_wav(path: Path) -> tuple[list[int], int, int]:
    """
    Read a WAV file and return (samples_q16_16, sample_rate, n_samples).

    Samples are normalised to Q16_16 (UInt32):
      PCM int16  → Q16_16 by sign-extending and shifting left 16 bits
      PCM float  → Q16_16 via f * 65536 (clamped)

    Only the first channel is used; stereo is downmixed to mono.
    """
    with wave.open(str(path), "rb") as wf:
        n_channels   = wf.getnchannels()
        sample_width = wf.getsampwidth()   # bytes per sample
        sample_rate  = wf.getframerate()
        n_frames     = wf.getnframes()
        raw          = wf.readframes(n_frames)

    samples_q: list[int] = []

    if sample_width == 2:  # PCM int16
        fmt = f"<{n_frames * n_channels}h"
        pcm = struct.unpack(fmt, raw)
        for i in range(0, len(pcm), n_channels):
            # int16 → Q16_16: treat as signed, shift to 16.16 space
            # value in [-32768, 32767] → Q16_16 by (v + 32768) * 2 to [0, 131070]
            # Then encode as UInt32: (v << 16) with sign handling
            v = pcm[i]
            # Encode: Q16_16 one = 0x00010000 = 65536
            # map int16 range [-32768..32767] → [0x80000000..0x7FFF0000]
            q = (v * 65536) & 0xFFFFFFFF
            samples_q.append(q)
    elif sample_width == 3:  # PCM int24
        n_total = n_frames * n_channels
        for i in range(0, n_total * 3, n_channels * 3):
            # read 3 bytes as little-endian int24
            b0, b1, b2 = raw[i], raw[i + 1], raw[i + 2]
            v24 = b0 | (b1 << 8) | (b2 << 16)
            if v24 & 0x800000:
                v24 -= 0x1000000  # sign extend
            # scale to int16 range then Q16_16
            v16 = v24 >> 8
            q = (v16 * 65536) & 0xFFFFFFFF
            samples_q.append(q)
    else:
        raise ValueError(
            f"Unsupported sample width {sample_width} bytes in {path.name}. "
            "Only 16-bit and 24-bit PCM WAV are supported."
        )

    return samples_q, sample_rate, len(samples_q)


# ── Lean shim call ────────────────────────────────────────────────────────────

def _call_lean_teleport(
    samples_q: list[int],
    sha256_words: list[int],
    sample_hz_q16: int,
    max_depth: int,
    lean_bin: Path,
) -> dict[str, Any]:
    """
    Marshal the waveform data to JSON, call SemanticsCli with the
    waveform-teleport command, and return the parsed receipt dict.

    If the Lean binary is not present, return a stub receipt with a clear
    software-witness-only marker.
    """
    payload = {
        "command":      "waveform_teleport",
        "samples_q16":  samples_q,
        "sha256_words": sha256_words,
        "sample_hz_q16": sample_hz_q16,
        "max_depth":    max_depth,
    }

    if not lean_bin.exists():
        # Software-witness fallback: no Lean binary available.
        # Return a stub so the shim can still emit a receipt.
        return {
            "lean_witness": False,
            "stub": True,
            "reason": f"Lean binary not found at {lean_bin}",
            "attractor_id":   None,
            "rg_depth":       None,
            "sigma_q":        None,
            "beta_residual":  None,
            "token_lawful":   False,
            "roundtrip_ok":   False,
        }

    import subprocess  # noqa: PLC0415 — only imported when binary is present
    result = subprocess.run(
        [str(lean_bin), "waveform-teleport"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"SemanticsCli waveform-teleport failed:\n{result.stderr}"
        )
    return json.loads(result.stdout)


# ── receipt assembly ──────────────────────────────────────────────────────────

def build_receipt(
    wav_path: Path,
    max_depth: int = 32,
    lean_bin: Path = LEAN_BIN_DEFAULT,
) -> dict[str, Any]:
    """
    Main shim entry point.

    1. Read WAV → Q16_16 samples + SHA-256
    2. Call Lean teleport logic
    3. Assemble and return TeleportReceipt JSON
    """
    raw_bytes = wav_path.read_bytes()
    sha256_hex  = _sha256_hex(raw_bytes)
    sha256_words = _sha256_words(raw_bytes)

    samples_q, sample_rate, n_samples = _read_wav(wav_path)

    # sample_rate in Q16_16: Hz * 65536  (fits in UInt32 for rates ≤ 32767 Hz)
    sample_hz_q16 = (sample_rate * 65536) & 0xFFFFFFFF

    lean_result = _call_lean_teleport(
        samples_q    = samples_q,
        sha256_words = sha256_words,
        sample_hz_q16 = sample_hz_q16,
        max_depth    = max_depth,
        lean_bin     = lean_bin,
    )

    receipt: dict[str, Any] = {
        "schema":          "waveprobe_rgflow_teleport_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_path":     str(wav_path),
        "source_sha256":   sha256_hex,
        "n_samples":       n_samples,
        "sample_rate_hz":  sample_rate,
        "max_depth":       max_depth,
        "lean_witness":    lean_result.get("lean_witness", False),
        "attractor_id":    lean_result.get("attractor_id"),
        "rg_depth":        lean_result.get("rg_depth"),
        "sigma_q":         lean_result.get("sigma_q"),
        "beta_residual":   lean_result.get("beta_residual"),
        "token_lawful":    lean_result.get("token_lawful", False),
        "roundtrip_ok":    lean_result.get("roundtrip_ok", False),
        "claim_boundary":  CLAIM_BOUNDARY,
    }

    # receipt_hash: SHA-256 of the stable preimage (excludes generated_at_utc)
    preimage = {k: v for k, v in receipt.items() if k != "generated_at_utc"}
    receipt["receipt_hash"] = _sha256_hex(
        json.dumps(preimage, sort_keys=True).encode()
    )

    return receipt


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Waveform teleport shim — extract RG attractor, emit receipt."
    )
    parser.add_argument("--wav",       required=True, type=Path,
                        help="Input WAV file")
    parser.add_argument("--out",       required=False, type=Path, default=None,
                        help="Output receipt JSON path (default: stdout)")
    parser.add_argument("--max-depth", type=int, default=32,
                        help="Max RG decimation depth (default: 32)")
    parser.add_argument("--lean-bin",  type=Path, default=LEAN_BIN_DEFAULT,
                        help="Path to SemanticsCli binary")
    args = parser.parse_args()

    if not args.wav.exists():
        print(f"[ERROR] WAV not found: {args.wav}", file=sys.stderr)
        sys.exit(1)

    receipt = build_receipt(
        wav_path  = args.wav,
        max_depth = args.max_depth,
        lean_bin  = args.lean_bin,
    )

    out_json = json.dumps(receipt, indent=2)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out_json)
        print(f"[OK] Receipt written to {args.out}")
    else:
        print(out_json)


if __name__ == "__main__":
    main()
