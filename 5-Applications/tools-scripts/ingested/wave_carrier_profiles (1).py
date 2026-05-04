from __future__ import annotations

"""Carrier-profile utilities for synthetic speech and PCM/PipeWire replay.

Provides a deterministic synthetic speech-like waveform generator and three
carrier views over the same signal:
- direct floating-point carrier
- PCM-packed carrier
- PipeWire-profile carrier
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple
import math
import struct

import numpy as np


@dataclass(frozen=True)
class CarrierConfig:
    sample_rate_hz: int = 16000
    chunk_size: int = 1024
    pcm_sample_width_bytes: int = 2
    channels: int = 1
    seed: int = 42


def generate_synthetic_speech(duration_s: float = 2.0, cfg: CarrierConfig = CarrierConfig()) -> np.ndarray:
    """Generate a deterministic speech-like waveform.

    The signal alternates voiced harmonic blocks with shaped envelopes and light
    noise, giving a bounded real-structured carrier without relying on external
    TTS or archival audio.
    """
    rng = np.random.default_rng(cfg.seed)
    t = np.linspace(0.0, duration_s, int(cfg.sample_rate_hz * duration_s), endpoint=False)

    # Slowly varying voiced fundamental.
    f0 = 120.0 + 15.0 * np.sin(2.0 * np.pi * 2.1 * t) + 8.0 * np.sin(2.0 * np.pi * 0.7 * t)

    signal = np.zeros_like(t, dtype=np.float64)
    for k in range(1, 7):
        signal += (1.0 / k) * np.sin(2.0 * np.pi * k * f0 * t)

    # Syllable-like envelope: periodic voiced windows with smoothed on/off.
    gate = (np.sin(2.0 * np.pi * 1.6 * t) > -0.1).astype(np.float64)
    kernel = np.ones(801, dtype=np.float64) / 801.0
    envelope = np.convolve(gate, kernel, mode="same")

    # Fricative-like bursts layered in at deterministic positions.
    burst = np.zeros_like(t, dtype=np.float64)
    burst_mask = (np.sin(2.0 * np.pi * 4.0 * t + 0.4) > 0.92).astype(np.float64)
    burst = 0.08 * burst_mask * rng.standard_normal(t.shape[0])

    # Light background noise to avoid trivial perfect periodicity.
    noise = 0.015 * rng.standard_normal(t.shape[0])

    y = signal * envelope + burst + noise
    peak = float(np.max(np.abs(y))) if y.size else 1.0
    if peak > 1e-12:
        y = 0.95 * y / peak
    return y.astype(np.float32)


def chunk_signal(samples: np.ndarray, chunk_size: int) -> List[np.ndarray]:
    out: List[np.ndarray] = []
    for i in range(0, len(samples), chunk_size):
        chunk = samples[i : i + chunk_size]
        if len(chunk) < chunk_size:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
        out.append(chunk.astype(np.float32, copy=False))
    return out


def pack_pcm16_mono(samples: np.ndarray) -> bytes:
    clipped = np.clip(samples.astype(np.float32, copy=False), -1.0, 1.0)
    ints = np.round(clipped * 32767.0).astype('<i2')
    return ints.tobytes()


def unpack_pcm16_mono(data: bytes) -> np.ndarray:
    if not data:
        return np.zeros(0, dtype=np.float32)
    arr = np.frombuffer(data, dtype='<i2').astype(np.float32)
    return (arr / 32768.0).astype(np.float32, copy=False)


def _safe01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def carrier_metrics_from_samples(samples: np.ndarray, sample_rate_hz: int) -> Dict[str, float]:
    samples = samples.astype(np.float32, copy=False)
    if samples.size == 0:
        return {
            "spectral_centroid": 0.0,
            "spectral_flatness": 0.0,
            "transient_ratio": 0.0,
            "band_low": 0.0,
            "band_mid": 0.0,
            "band_high": 0.0,
            "coherence": 1.0,
            "energy": 0.0,
            "confidence": 1.0,
            "noise": 0.0,
        }

    rms = float(np.sqrt(np.mean(samples * samples)))
    energy = _safe01(rms / 0.5)

    if samples.size >= 2:
        diff = np.diff(samples, prepend=samples[0])
        transient_ratio = float(np.mean(np.abs(diff)) / max(rms, 1e-6))
        transient_ratio = _safe01(transient_ratio / 1.5)
        zero_cross = float(np.mean((samples[:-1] * samples[1:]) < 0.0))
    else:
        transient_ratio = 0.0
        zero_cross = 0.0

    if samples.size < 8 or sample_rate_hz <= 0:
        spectral_centroid = 0.0
        flatness = 0.0
        low = mid = high = 0.0
        dominant_hz = 0.0
    else:
        window = np.hanning(samples.size).astype(np.float32)
        spec = np.fft.rfft(samples * window)
        power = np.abs(spec) ** 2 + 1e-12
        freqs = np.fft.rfftfreq(samples.size, d=1.0 / sample_rate_hz)
        total = float(np.sum(power))
        centroid_hz = float(np.sum(freqs * power) / total)
        spectral_centroid = _safe01(centroid_hz / (sample_rate_hz / 2.0))
        flatness = float(np.exp(np.mean(np.log(power))) / max(np.mean(power), 1e-12))
        flatness = _safe01(flatness)
        low = float(np.sum(power[freqs < 1000.0]) / total)
        mid = float(np.sum(power[(freqs >= 1000.0) & (freqs < 4000.0)]) / total)
        high = float(np.sum(power[freqs >= 4000.0]) / total)
        dom_idx = int(np.argmax(power[1:]) + 1) if power.size > 1 else 0
        dominant_hz = float(freqs[dom_idx]) if dom_idx < freqs.size else 0.0

    # Confidence/coherence are intentionally bounded structural surrogates.
    coherence = _safe01(1.0 - 0.55 * flatness - 0.20 * zero_cross)
    noise = _safe01(0.65 * flatness + 0.35 * zero_cross)
    confidence = _safe01(0.45 * coherence + 0.35 * (1.0 - noise) + 0.20 * energy)

    return {
        "spectral_centroid": spectral_centroid,
        "spectral_flatness": flatness,
        "transient_ratio": transient_ratio,
        "band_low": _safe01(low),
        "band_mid": _safe01(mid),
        "band_high": _safe01(high),
        "coherence": coherence,
        "energy": energy,
        "confidence": confidence,
        "noise": noise,
        "dominant_hz": dominant_hz,
    }


def direct_carriers(samples: np.ndarray, cfg: CarrierConfig = CarrierConfig()) -> List[Dict[str, float]]:
    return [carrier_metrics_from_samples(ch, cfg.sample_rate_hz) for ch in chunk_signal(samples, cfg.chunk_size)]


def pcm_carriers(samples: np.ndarray, cfg: CarrierConfig = CarrierConfig()) -> List[Dict[str, float]]:
    out: List[Dict[str, float]] = []
    for ch in chunk_signal(samples, cfg.chunk_size):
        pcm = pack_pcm16_mono(ch)
        recovered = unpack_pcm16_mono(pcm)
        out.append(carrier_metrics_from_samples(recovered, cfg.sample_rate_hz))
    return out


def pipewire_profile_carriers(samples: np.ndarray, cfg: CarrierConfig = CarrierConfig()) -> List[Dict[str, float]]:
    out: List[Dict[str, float]] = []
    for idx, ch in enumerate(chunk_signal(samples, cfg.chunk_size)):
        pcm = pack_pcm16_mono(ch)
        recovered = unpack_pcm16_mono(pcm)
        metrics = carrier_metrics_from_samples(recovered, cfg.sample_rate_hz)
        # PipeWire-profile view: same carrier realized through a DSP surface with
        # explicit transport metadata and tiny bounded jitter penalty.
        metrics["transport_latency"] = _safe01(0.02 + 0.005 * ((idx % 3)))
        metrics["confidence"] = _safe01(metrics["confidence"] * (1.0 - 0.25 * metrics["transport_latency"]))
        out.append(metrics)
    return out



import wave
from pathlib import Path

def load_wav_mono(path: str | Path, target_sample_rate_hz: int | None = None) -> np.ndarray:
    """
    Load a mono-compatible WAV file into a float32 waveform in [-1, 1].
    If target_sample_rate_hz is provided and differs from the source rate,
    a simple deterministic linear resample is applied.
    """
    path = Path(path)
    with wave.open(str(path), 'rb') as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        frames = wf.readframes(nframes)

    if sampwidth == 1:
        arr = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
        arr = (arr - 128.0) / 128.0
    elif sampwidth == 2:
        arr = np.frombuffer(frames, dtype='<i2').astype(np.float32)
        arr = arr / 32768.0
    elif sampwidth == 4:
        arr = np.frombuffer(frames, dtype='<i4').astype(np.float32)
        arr = arr / 2147483648.0
    else:
        raise ValueError(f'Unsupported WAV sample width: {sampwidth}')

    if channels > 1:
        arr = arr.reshape(-1, channels).mean(axis=1)

    if target_sample_rate_hz and target_sample_rate_hz > 0 and target_sample_rate_hz != framerate:
        if arr.size == 0:
            return arr.astype(np.float32)
        duration = arr.size / framerate
        n_out = max(1, int(round(duration * target_sample_rate_hz)))
        x_old = np.linspace(0.0, 1.0, arr.size, endpoint=False)
        x_new = np.linspace(0.0, 1.0, n_out, endpoint=False)
        arr = np.interp(x_new, x_old, arr).astype(np.float32)

    peak = float(np.max(np.abs(arr))) if arr.size else 0.0
    if peak > 1e-12:
        arr = 0.98 * arr / peak
    return arr.astype(np.float32, copy=False)


def archival_wav_carriers(path: str | Path, cfg: CarrierConfig = CarrierConfig()) -> dict[str, object]:
    """
    Return direct / PCM / PipeWire-profile carriers from a replayed archival WAV.
    """
    samples = load_wav_mono(path, target_sample_rate_hz=cfg.sample_rate_hz)
    return {
        'samples': samples,
        'direct': direct_carriers(samples, cfg),
        'pcm': pcm_carriers(samples, cfg),
        'pipewire': pipewire_profile_carriers(samples, cfg),
    }
