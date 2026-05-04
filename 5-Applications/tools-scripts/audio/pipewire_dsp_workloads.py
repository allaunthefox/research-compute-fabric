#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
DSP-like front-end workloads for PipeWire waveprobe experiments.

These are bounded host-side transforms intended to approximate the shape of a
front-end DSP lane without claiming to replace a later PipeWire filter node,
custom DSP block, or HDL path.
"""

from __future__ import annotations

from typing import Dict, Tuple

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray


WORKLOAD_RAW = "raw"
WORKLOAD_SPECTRAL_FOCUS = "spectral_focus"
WORKLOAD_TRANSIENT_EDGE = "transient_edge"
WORKLOAD_HYBRID = "hybrid"

AVAILABLE_WORKLOADS = (
    WORKLOAD_RAW,
    WORKLOAD_SPECTRAL_FOCUS,
    WORKLOAD_TRANSIENT_EDGE,
    WORKLOAD_HYBRID,
)


def available_workloads() -> Tuple[str, ...]:
    return AVAILABLE_WORKLOADS


def _decode_pcm_mono(
    chunk_bytes: bytes,
    sample_width_bytes: int,
    channels: int,
) -> Tuple[AnyArray, int]:
    frame_width = max(1, sample_width_bytes * max(1, channels))
    usable = len(chunk_bytes) - (len(chunk_bytes) % frame_width)
    if usable <= 0:
        return xp.zeros(0, dtype=xp.float32), 0
    trimmed = chunk_bytes[:usable]

    if sample_width_bytes == 1:
        arr = xp.frombuffer(trimmed, dtype=xp.uint8).astype(xp.float32)
        arr = (arr - 128.0) / 128.0
    elif sample_width_bytes == 2:
        arr = xp.frombuffer(trimmed, dtype="<i2").astype(xp.float32)
        arr = arr / 32768.0
    elif sample_width_bytes == 4:
        arr = xp.frombuffer(trimmed, dtype="<i4").astype(xp.float32)
        arr = arr / 2147483648.0
    else:
        raise ValueError(f"Unsupported sample width: {sample_width_bytes}")

    arr = arr.reshape(-1, max(1, channels))
    mono = arr.mean(axis=1).astype(xp.float32, copy=False)
    return mono, usable


def _encode_pcm_mono(
    samples: AnyArray,
    sample_width_bytes: int,
    channels: int,
) -> bytes:
    if samples.size == 0:
        return b""
    clipped = xp.clip(samples.astype(xp.float32, copy=False), -1.0, 1.0)
    if channels > 1:
        clipped = xp.repeat(clipped[:, None], channels, axis=1).reshape(-1)

    if sample_width_bytes == 1:
        out = xp.clip(xp.round(clipped * 127.0 + 128.0), 0, 255).astype(xp.uint8)
    elif sample_width_bytes == 2:
        out = xp.clip(xp.round(clipped * 32767.0), -32768, 32767).astype("<i2")
    elif sample_width_bytes == 4:
        out = xp.clip(
            xp.round(clipped * 2147483647.0),
            -2147483648,
            2147483647,
        ).astype("<i4")
    else:
        raise ValueError(f"Unsupported sample width: {sample_width_bytes}")
    return out.tobytes()


def _match_rms(processed: AnyArray, reference: AnyArray) -> AnyArray:
    if processed.size == 0:
        return processed.astype(xp.float32, copy=False)
    ref_rms = float(xp.sqrt(xp.mean(reference * reference))) if reference.size else 0.0
    proc_rms = float(xp.sqrt(xp.mean(processed * processed)))
    out = processed.astype(xp.float32, copy=True)
    if ref_rms > 1e-9 and proc_rms > 1e-9:
        out *= ref_rms / proc_rms
    peak = float(xp.max(xp.abs(out))) if out.size else 0.0
    if peak > 0.999:
        out *= 0.999 / peak
    return out


def _spectral_focus(samples: AnyArray) -> AnyArray:
    if samples.size < 8:
        return samples.astype(xp.float32, copy=True)
    window = xp.hanning(samples.size).astype(xp.float32)
    spec = xp.fft.rfft(samples * window)
    mag = xp.abs(spec)
    if mag.size <= 1:
        return samples.astype(xp.float32, copy=True)
    max_mag = float(xp.max(mag[1:])) if mag.size > 1 else float(xp.max(mag))
    if max_mag <= 1e-12:
        return xp.zeros_like(samples, dtype=xp.float32)
    weights = 0.15 + 0.85 * xp.sqrt(mag / max_mag)
    weights[0] *= 0.35
    focused = xp.fft.irfft(spec * weights, n=samples.size).real.astype(xp.float32)
    blended = (0.65 * samples + 0.35 * focused).astype(xp.float32, copy=False)
    return _match_rms(blended, samples)


def _transient_edge(samples: AnyArray) -> AnyArray:
    if samples.size < 4:
        return samples.astype(xp.float32, copy=True)
    diff = xp.diff(samples, prepend=samples[0]).astype(xp.float32, copy=False)
    kernel = xp.array([0.25, 0.5, 0.25], dtype=xp.float32)
    smoothed = xp.convolve(diff, kernel, mode="same")
    edged = xp.tanh(2.5 * smoothed).astype(xp.float32, copy=False)
    blended = (0.55 * samples + 0.45 * edged).astype(xp.float32, copy=False)
    return _match_rms(blended, samples)


def _hybrid(samples: AnyArray) -> AnyArray:
    focused = _spectral_focus(samples)
    edged = _transient_edge(samples)
    mixed = (0.5 * samples + 0.3 * focused + 0.2 * edged).astype(xp.float32, copy=False)
    return _match_rms(mixed, samples)


def _compute_metrics(samples: AnyArray, sample_rate_hz: int) -> Dict[str, float]:
    if samples.size == 0:
        return {
            "rms": 0.0,
            "zero_crossing_rate": 0.0,
            "spectral_centroid_hz": 0.0,
            "spectral_flatness": 0.0,
            "dominant_freq_hz": 0.0,
            "transient_ratio": 0.0,
            "band_energy_low": 0.0,
            "band_energy_mid": 0.0,
            "band_energy_high": 0.0,
        }

    rms = float(xp.sqrt(xp.mean(samples * samples)))
    if samples.size >= 2:
        zc = float(xp.mean((samples[:-1] * samples[1:]) < 0.0))
        diff = xp.diff(samples, prepend=samples[0])
        transient_ratio = float(xp.mean(xp.abs(diff)) / max(rms, 1e-9))
    else:
        zc = 0.0
        transient_ratio = 0.0

    if samples.size < 8 or sample_rate_hz <= 0:
        return {
            "rms": rms,
            "zero_crossing_rate": zc,
            "spectral_centroid_hz": 0.0,
            "spectral_flatness": 0.0,
            "dominant_freq_hz": 0.0,
            "transient_ratio": transient_ratio,
            "band_energy_low": 0.0,
            "band_energy_mid": 0.0,
            "band_energy_high": 0.0,
        }

    window = xp.hanning(samples.size).astype(xp.float32)
    spec = xp.fft.rfft(samples * window)
    power = xp.abs(spec) ** 2 + 1e-12
    freqs = xp.fft.rfftfreq(samples.size, d=1.0 / sample_rate_hz)
    total_power = float(xp.sum(power))

    centroid = float(xp.sum(freqs * power) / total_power)
    dom_idx = int(xp.argmax(power[1:]) + 1) if power.size > 1 else 0
    dominant = float(freqs[dom_idx]) if freqs.size > dom_idx else 0.0
    flatness = float(xp.exp(xp.mean(xp.log(power))) / max(xp.mean(power), 1e-12))

    low_mask = freqs < 1000.0
    mid_mask = (freqs >= 1000.0) & (freqs < 4000.0)
    high_mask = freqs >= 4000.0
    low = float(xp.sum(power[low_mask]) / total_power)
    mid = float(xp.sum(power[mid_mask]) / total_power)
    high = float(xp.sum(power[high_mask]) / total_power)

    return {
        "rms": rms,
        "zero_crossing_rate": zc,
        "spectral_centroid_hz": centroid,
        "spectral_flatness": flatness,
        "dominant_freq_hz": dominant,
        "transient_ratio": transient_ratio,
        "band_energy_low": low,
        "band_energy_mid": mid,
        "band_energy_high": high,
    }


def apply_dsp_workload(
    chunk_bytes: bytes,
    sample_width_bytes: int,
    channels: int,
    sample_rate_hz: int,
    workload: str = WORKLOAD_RAW,
) -> Tuple[bytes, Dict[str, float]]:
    if workload not in AVAILABLE_WORKLOADS:
        raise ValueError(
            f"Unknown DSP workload {workload!r}; expected one of {AVAILABLE_WORKLOADS}"
        )

    try:
        samples, usable = _decode_pcm_mono(
            chunk_bytes,
            sample_width_bytes=sample_width_bytes,
            channels=channels,
        )
    except ValueError:
        return chunk_bytes, {"workload": workload, "fallback_raw": 1.0}

    if usable <= 0:
        return b"", {"workload": workload, "fallback_raw": 1.0}

    if workload == WORKLOAD_RAW:
        processed = samples
    elif workload == WORKLOAD_SPECTRAL_FOCUS:
        processed = _spectral_focus(samples)
    elif workload == WORKLOAD_TRANSIENT_EDGE:
        processed = _transient_edge(samples)
    else:
        processed = _hybrid(samples)

    metrics_in = _compute_metrics(samples, sample_rate_hz=sample_rate_hz)
    metrics_out = _compute_metrics(processed, sample_rate_hz=sample_rate_hz)
    processed_bytes = _encode_pcm_mono(
        processed,
        sample_width_bytes=sample_width_bytes,
        channels=channels,
    )

    metrics = {
        "workload": workload,
        "input_rms": metrics_in["rms"],
        "output_rms": metrics_out["rms"],
        "rms_ratio": metrics_out["rms"] / max(metrics_in["rms"], 1e-9),
        "zero_crossing_rate": metrics_out["zero_crossing_rate"],
        "spectral_centroid_hz": metrics_out["spectral_centroid_hz"],
        "spectral_flatness": metrics_out["spectral_flatness"],
        "dominant_freq_hz": metrics_out["dominant_freq_hz"],
        "transient_ratio": metrics_out["transient_ratio"],
        "band_energy_low": metrics_out["band_energy_low"],
        "band_energy_mid": metrics_out["band_energy_mid"],
        "band_energy_high": metrics_out["band_energy_high"],
        "centroid_shift_hz": metrics_out["spectral_centroid_hz"]
        - metrics_in["spectral_centroid_hz"],
        "transient_shift": metrics_out["transient_ratio"]
        - metrics_in["transient_ratio"],
    }
    return processed_bytes, metrics
