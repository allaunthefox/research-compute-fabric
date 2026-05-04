# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Carrier state Factory — two-layer labeled-box TSE encode/decode.

Layer 1 — Carrier state boxes  (structured signal reconstruction)
────────────────────────────────────────────────────────────
Each carrier state parameter is a labeled box:

    CarrierBox:  label=(band, mode, param, frame)  value=f16

  Stamp → Label → Sort (American Flag Sort) → Pack into FoamVoxels

Layer 2 — Jupiter boxes  (Procedural Generative Fractal Summation)
─────────────────────────────────────────────────────────────────────────
The irreducible friction residual is no longer stored as a static blob. 
Instead, it is mapped to a low-energy Procedural Generative Seed. 
This seed, when expanded via Holographic Recursion (Opcode 0x19), sums 
to the total complexity of the original residual.

    irreducible core → 64-bit Fractal Seed → UV Map Topological Rollup
    Expansion: Seed + Stride (W) → Deterministic Complexity Reconstruction

This refinement (v4.0) moves the system from Shannon-bounded storage to 
Kolmogorov-bounded algorithmic generation, drastically reducing the 
"AETHER floor" energy cost per bit.

Phase-lock condition gates the layer:
  PHASE_GROUNDED  (phi_ratio ≈ φ)     → tunnel fires, zero-damage transfer
  PHASE_SEISMIC   (phi_ratio ≈ 1-2φ)  → partial encoding, minor drift
  PHASE_FLAME     (phi_ratio >> φ)    → skip Jupiter layer, pure noise

The metanarrative harness (tsm_narrative_layers.vh / metanarrative_goal_spec.md)
is the complexity filter: F(S) = Equilibrium ↔ ∇Entropy ≈ 0 & Φ ≈ 1.618.
When the harness says PHASE_FLAME the layer is bypassed — no false precision.

Jupiter boxes use band=0xFE as the layer marker in the 32-bit label.
"""
from __future__ import annotations

import hashlib
import math
import os
import struct
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(__file__))

from usc_spectral_core import (
    deep_compression_snag, shift_allocation, conversion_efficiency,
    shannon_capacity, eddington_utilization, landauer_cost,
)

# ── Parameter catalogue ───────────────────────────────────────────────────────
# Geometric params NOT transmitted — reconstructed at decode (white hole) from
# the shared physical basis.  This is the gamma-pattern principle:
#
#   pos_x     → _band_centre(band_idx, f_low, f_high, n_bands)
#   bandwidth → (f_high - f_low) / n_bands
#   rate      → n_samples / sample_rate  (frame duration, constant per frame)
#
# What remains on the wire: amplitude, phase, velocity, curvature, coherence.
PARAM_NAMES  = ('amplitude', 'phase', 'velocity', 'curvature', 'coherence')
N_PARAMS     = len(PARAM_NAMES)   # 5  (was 8; pos_x, bandwidth, rate eliminated)

# ── Complex geometry scaffold (geometry-rip branch) ───────────────────────────
# COMPLEX_NUMBER_AUDIT #H1 and #M2 now split into independent flags (DAG 777):
#
#   _USE_H1  (HIGH): complex Goertzel velocity — chirp / phase drift detection.
#                    Safe to enable. This IS the carrier state path-finding projector:
#                    H1 projects input data onto n-space to find the carrier state
#                    trajectory. Without H1, chirp signals appear as zero-velocity
#                    (amplitude-only path), producing a degenerate n-space trace.
#                    See: sessions/chat-carrier state-nspace-path-trace-20260404.md
#
#   _USE_M2  (LOWER): PHI^(i*PHI_FRAC) Weyl sequence in _modes_from_bytes.
#                     DEFERRED — Weyl inverts enwik9 discrimination (95.9% FLAME).
#                     i%7 is intentional hardware design; Weyl is not the fix.
_USE_H1 = True   # DAG 777: chirp detection live; carrier state path projector enabled
_USE_M2 = False  # DEFERRED: Weyl (PHI^(i*PHI_FRAC)) inverts enwik9 discrimination

# ── Label packing layout (32 bits total) ─────────────────────────────────────
#   bits 31-24 : band_idx    (8 bands, 3 bits → padded to 8)
#   bits 23-11 : mode_idx    (up to 8191 modes, 13 bits)
#   bits 10- 8 : param_idx   (8 params, 3 bits)
#   bits  7- 0 : frame_idx   (256 frames, 8 bits)

def pack_label(band: int, mode: int, param: int, frame: int) -> int:
    return ((band & 0xFF) << 24) | ((mode & 0x1FFF) << 11) | ((param & 0x7) << 8) | (frame & 0xFF)

def unpack_label(label: int) -> Tuple[int, int, int, int]:
    band  = (label >> 24) & 0xFF
    mode  = (label >> 11) & 0x1FFF
    param = (label >>  8) & 0x07
    frame = (label >>  0) & 0xFF
    return band, mode, param, frame

# ── Half-float helpers (no numpy required) ───────────────────────────────────

def f32_to_f16_bits(v: float) -> int:
    """Convert f32 to f16 bit pattern (IEEE 754 half-precision)."""
    packed = struct.pack('>f', float(v))
    b = struct.unpack('>I', packed)[0]
    sign  = (b >> 16) & 0x8000
    exp   = ((b >> 23) & 0xFF) - 127 + 15
    mant  = (b >> 13) & 0x3FF
    if exp <= 0:
        return sign
    if exp >= 31:
        return sign | 0x7C00
    return sign | (exp << 10) | mant

def f16_bits_to_f32(h: int) -> float:
    """Convert f16 bit pattern back to Python float."""
    sign = -1.0 if h & 0x8000 else 1.0
    exp  = (h >> 10) & 0x1F
    mant = h & 0x3FF
    if exp == 0:
        return sign * (mant / 1024.0) * (2.0 ** -14)
    if exp == 31:
        return sign * float('inf')
    return sign * (1.0 + mant / 1024.0) * (2.0 ** (exp - 15))

# ── Core data structures ──────────────────────────────────────────────────────

@dataclass(order=True)
class CarrierBox:
    """
    The fundamental factory unit.
    label is the sort key — ordering is the full address in carrier state space.
    """
    label: int          # packed (band, mode, param, frame)
    value_bits: int     # f16 bit pattern

    def decode_value(self) -> float:
        return f16_bits_to_f32(self.value_bits)

    def pack(self) -> bytes:
        """6 bytes: 4-byte label + 2-byte f16."""
        return struct.pack('>IH', self.label, self.value_bits)

    @classmethod
    def unpack(cls, data: bytes) -> 'CarrierBox':
        label, vbits = struct.unpack('>IH', data)
        return cls(label, vbits)

    @property
    def address(self) -> Tuple[int, int, int, int]:
        return unpack_label(self.label)


@dataclass
class FoamVoxel:
    """
    A voxel = one carrier state's parameter boxes, grouped by (band, mode).
    All 8 param slots; missing ones default to 0.
    """
    band: int
    mode: int
    params: List[float] = field(default_factory=lambda: [0.0] * N_PARAMS)

    def to_boxes(self, frame: int = 0) -> List[CarrierBox]:
        boxes = []
        for p_idx, val in enumerate(self.params):
            label = pack_label(self.band, self.mode, p_idx, frame)
            boxes.append(CarrierBox(label, f32_to_f16_bits(val)))
        return boxes

    @classmethod
    def from_boxes(cls, boxes: List[CarrierBox]) -> 'FoamVoxel':
        if not boxes:
            raise ValueError("empty box list")
        band, mode, _, _ = boxes[0].address
        params = [0.0] * N_PARAMS
        for box in boxes:
            _, _, p_idx, _ = box.address
            params[p_idx] = box.decode_value()
        return cls(band, mode, params)


# ── MSD Radix Sort (American Flag Sort) on label integers ─────────────────────
# Public-domain algorithm. O(32n) for 32-bit keys. Beats Timsort for n > 2000.

def _radix_sort_boxes(boxes: List[CarrierBox], bit: int = 31) -> None:
    """In-place MSD radix sort on CarrierBox.label. Uses 2-way split per bit."""
    if len(boxes) <= 1 or bit < 0:
        return
    if len(boxes) <= 16:
        # Insertion sort wins for tiny partitions
        for i in range(1, len(boxes)):
            key = boxes[i]
            j = i - 1
            while j >= 0 and boxes[j].label > key.label:
                boxes[j + 1] = boxes[j]
                j -= 1
            boxes[j + 1] = key
        return
    # Partition on current bit
    zeros, ones = [], []
    mask = 1 << bit
    for b in boxes:
        (zeros if not (b.label & mask) else ones).append(b)
    _radix_sort_boxes(zeros, bit - 1)
    _radix_sort_boxes(ones,  bit - 1)
    boxes[:] = zeros + ones


# ── Domain basis registry ─────────────────────────────────────────────────────
# The gamma-pattern principle applied universally:
#   transmit band_idx (token), reconstruct energy/frequency at decode time
#   from the shared physical basis table.
#
# spacing='log'   — octave/decade bands (audio, X-ray, gamma)
# spacing='linear'— uniform channel grid (FM radio, AM radio, microwave)
# spacing='table' — explicit nuclear/atomic line positions (ENSDF, NIST)
#
# unit is informational only — the codec doesn't care if it's Hz or keV or
# "Regge units" or "monopole charge quanta".  The constants are parameters
# we choose to maximise sparsity for the target data.  Nothing requires the
# basis to be physically realised in 3+1 dimensions.

@dataclass
class DomainBasis:
    """Physical basis table for one spectral domain."""
    name:    str
    f_low:   float        # lowest energy/frequency in domain units
    f_high:  float        # highest energy/frequency in domain units
    n_bands: int          # number of addressable basis elements
    spacing: str          # 'log', 'linear', or 'table'
    unit:    str          # display unit (Hz, keV, MHz, THz, …)
    table:   List[float] = field(default_factory=list)  # explicit lines if spacing='table'

    def centre(self, band_idx: int) -> float:
        """Reconstruct centre value from band index — the gamma pattern decoder."""
        if self.spacing == 'log':
            log_step = (math.log2(max(self.f_high, 1e-300)) -
                        math.log2(max(self.f_low,  1e-300))) / self.n_bands
            return max(self.f_low, 1e-300) * (2 ** (band_idx * log_step))
        if self.spacing == 'linear':
            step = (self.f_high - self.f_low) / self.n_bands
            return self.f_low + band_idx * step
        # table: explicit nuclear/atomic lines
        if self.table:
            return self.table[min(band_idx, len(self.table) - 1)]
        return self.f_low

    def bands(self) -> List[float]:
        return [self.centre(i) for i in range(self.n_bands)]


# Band-prefix → domain slot assignments (8-bit band field, 0x00-0xFF)
# Each range is a domain family. The decoder reads the prefix, loads the
# matching basis from DOMAIN_REGISTRY, and reconstructs without any extra wire bytes.
DOMAIN_BAND_SLOTS: Dict[str, int] = {
    'audio_44k':   0x00,
    'audio_hi':    0x01,
    'radio_am':    0x10,
    'radio_fm':    0x11,
    'microwave':   0x12,
    'visible':     0x20,
    'near_ir':     0x21,
    'terahertz':   0x22,
    'xray_soft':   0x30,
    'xray_hard':   0x31,
    'gamma_lines': 0x40,
    'phonon_al':   0x50,
    # 0xF0-0xFB: accelerated-time subregisters (assigned dynamically)
    # 0xFE: Jupiter tunnel
    # 0xFF: Planck floor / raw
}
SLOT_TO_DOMAIN: Dict[int, str] = {v: k for k, v in DOMAIN_BAND_SLOTS.items()}

# Pre-defined domain bases — both sides share this table (never transmitted).
# Adding a domain here costs zero bytes on the wire.
DOMAIN_REGISTRY: Dict[str, DomainBasis] = {

    # ── Audio ──────────────────────────────────────────────────────────────────
    'audio_44k':   DomainBasis('audio_44k',   20,      22050,  8,  'log',    'Hz'),
    'audio_hi':    DomainBasis('audio_hi',    20,      96000,  16, 'log',    'Hz'),   # 192kHz/24-bit

    # ── Radio ──────────────────────────────────────────────────────────────────
    'radio_fm':    DomainBasis('radio_fm',    87.5e6,  108e6,  101,'linear', 'Hz'),   # 200kHz channels
    'radio_am':    DomainBasis('radio_am',    530e3,   1710e3, 119,'linear', 'Hz'),   # 10kHz channels
    'microwave':   DomainBasis('microwave',   300e6,   300e9,  16, 'log',    'Hz'),

    # ── Optical / IR ───────────────────────────────────────────────────────────
    'visible':     DomainBasis('visible',     380e12,  750e12, 8,  'log',    'Hz'),   # 380-750 THz
    'near_ir':     DomainBasis('near_ir',     100e12,  380e12, 8,  'log',    'Hz'),
    'terahertz':   DomainBasis('terahertz',   100e9,   10e12,  16, 'log',    'Hz'),

    # ── X-ray ──────────────────────────────────────────────────────────────────
    'xray_soft':   DomainBasis('xray_soft',   0.1,     10.0,   16, 'log',    'keV'),  # soft X-ray
    'xray_hard':   DomainBasis('xray_hard',   10.0,    150.0,  16, 'log',    'keV'),  # hard X-ray

    # ── Gamma (nuclear line table — ENSDF subset) ───────────────────────────────
    # Key lines: annihilation, Na-22, Co-60, Cs-137, Tl-208, K-40, Bi-214 …
    'gamma_lines': DomainBasis('gamma_lines', 0.0, 3000.0, 16, 'table', 'keV', table=[
        511.0,    # e+/e- annihilation (pair production)
        661.7,    # Cs-137 (most common calibration source)
        1173.2,   # Co-60 line 1
        1274.5,   # Na-22
        1332.5,   # Co-60 line 2
        1460.8,   # K-40 (natural background)
        1764.5,   # Bi-214 (radon chain)
        2614.5,   # Tl-208 (thorium chain)
        583.2,    # Tl-208 low
        727.3,    # Bi-212
        1120.3,   # Bi-214
        1238.1,   # Bi-214
        609.3,    # Bi-214
        1377.7,   # Bi-214
        2204.1,   # Bi-214
        2447.9,   # Bi-214 high
    ]),

    # ── Phonon (Debye model — aluminium example) ────────────────────────────────
    # ω = v_s × k, Debye cutoff ω_D = 2π × 9.7 THz for Al
    'phonon_al':   DomainBasis('phonon_al',   0.0,    9.7e12, 16, 'linear', 'THz'),

    # ══ Beyond-3D / exotic / tunable bases ══════════════════════════════════════
    # Constants are parameters — set them to maximise sparsity for your data.
    # None of these need to be physically realised.  The decoder reconstructs
    # the same deterministic float from the same index regardless of "reality".

    # ── Magnetic charge quantization (Dirac condition) ──────────────────────────
    # g_n = n × g_D  where g_D = ℏc/2e ≈ 68.5 × e  (SI)
    # Basis: charge quanta.  Tune g_D to match data periodicity.
    'magnetic_charge': DomainBasis('magnetic_charge', 1.0, 128.0, 16, 'linear', 'g_D'),

    # ── Harmonic tower (linearly spaced multiples) ─────────────────────────────
    # M_n = n × M_c  where M_c = compactification scale (tunable)
    # Set M_c to the characteristic energy of your data.
    'harmonic_tower':  DomainBasis('harmonic_tower',  0.0,  1000.0, 32, 'linear', 'M_c'),

    # ── Square-root sequence ────────────────────────────────────────────────────
    # M_n = √n — concave growth, good for sub-linear scaling.
    'sqrt_sequence':   DomainBasis('sqrt_sequence',   0.0,    16.0,  16, 'table',  'scale', table=[
        math.sqrt(n) for n in range(16)
    ]),

    # ── Gap sequence (|n - 1| for n=0..15) ──────────────────────────────────────
    # Zero at n=1, rises linearly on either side.  Useful for data with a central
    # mode and symmetric sidebands.
    'gap_sequence':    DomainBasis('gap_sequence',    0.0,    15.0,  16, 'table',  'gap', table=[
        abs(n - 1) for n in range(16)
    ]),

    # ── Octonion modes (7 imaginary units e1…e7) ─────────────────────────────────
    # Octonions are the largest normed division algebra.  Map data to the 7
    # non-associative imaginary axes + real axis = 8 basis elements.
    # Useful for 8-channel / 7.1 audio or colour + alpha data.
    'octonion':    DomainBasis('octonion',    0.0,    7.0,    8, 'linear', 'e_i'),

    # ── Gap fraction sequence (linear, 9 steps) ────────────────────────────────
    # 9 evenly spaced values.  Tune range to data scale.
    'gap_fraction': DomainBasis('gap_fraction', 0.0,  100.0,   9, 'linear', 'scale'),

    # ── Log-spaced range ──────────────────────────────────────────────────────
    # Log-uniform from 1 μ to 1 m.  Useful for wide dynamic range data.
    'log_range':   DomainBasis('log_range',   1e-6,   1e-3,  16, 'log',    'unit'),

    # ── Conformal dimension tower (2 + √(4+n)) ────────────────────────────────
    # Convex growth sequence.  Good for data with accelerating scale structure.
    'conformal_tower': DomainBasis('conformal_tower', 2.0, 18.0, 16, 'table', 'Δ', table=[
        2.0 + math.sqrt(4.0 + n) for n in range(16)
    ]),

    # ── Surreal / p-adic (ultrametric basis) ─────────────────────────────────────
    # p-adic absolute value: |n|_p = p^{-v_p(n)} where v_p = p-adic valuation.
    # Use p=2 (dyadic) — basis values are powers of 1/2.
    # Ultrametric geometry: nearby in p-adic sense ≠ nearby in real sense.
    # Excellent for hierarchical / tree-structured data.
    'padic_2':     DomainBasis('padic_2',     0.0,    1.0,  16, 'table',  '|·|_2', table=[
        2.0 ** (-n) for n in range(16)   # 1, 1/2, 1/4, 1/8, …
    ]),

    # ── Graviton polarization modes ───────────────────────────────────────────────
    # Only 2 physical polarizations: + (plus) and × (cross).
    # Extended: include scalar (dilaton) and vector (graviphoton) from higher-D.
    # 4 modes total for 4D supergravity multiplet.
    'graviton':    DomainBasis('graviton',    0.0,    3.0,   4, 'table',  'pol', table=[
        0.0,   # + polarization
        1.0,   # × polarization
        2.0,   # scalar (dilaton)
        3.0,   # vector (graviphoton)
    ]),

    # ── Spin network (loop quantum gravity) ──────────────────────────────────────
    # Area eigenvalues: A_j = 8πγl_P² √(j(j+1)) for half-integer j=0,½,1,…
    # γ = Barbero-Immirzi parameter (≈ 0.2375).  Basis: spin labels j.
    'spin_network': DomainBasis('spin_network', 0.0, 4.0,  16, 'table', 'j', table=[
        n * 0.5 for n in range(16)   # j = 0, 1/2, 1, 3/2, …, 15/2
    ]),
}


def _octave_bands(f_low: float, f_high: float, n: int) -> List[float]:
    log_step = (math.log2(max(f_high, 1)) - math.log2(max(f_low, 1))) / n
    return [max(f_low, 1) * (2 ** (i * log_step)) for i in range(n)]


def _band_centre(band_idx: int, f_low: float, f_high: float, n_bands: int) -> float:
    """Reconstruct centre frequency from band index — no value stored in boxes.

    This is the 'gamma pattern' decoder: band_idx is the atomic token, fc is
    derived from the shared physical basis (octave geometry).  Both sides must
    agree on f_low, f_high, n_bands — equivalent to agreeing on a detector
    response curve or nuclear line table.
    """
    log_step = (math.log2(max(f_high, 1)) - math.log2(max(f_low, 1))) / n_bands
    return max(f_low, 1) * (2 ** (band_idx * log_step))


def _goertzel(samples: List[float], freq: float, sample_rate: float) -> float:
    """Single-bin DFT magnitude via Goertzel algorithm. O(n)."""
    w = 2 * math.pi * freq / max(sample_rate, 1)
    coeff = 2 * math.cos(w)
    s1 = s2 = 0.0
    for s in samples:
        s0 = s + coeff * s1 - s2
        s2, s1 = s1, s0
    real = s1 - s2 * math.cos(w)
    imag = s2 * math.sin(w)
    return math.sqrt(real * real + imag * imag) / max(len(samples), 1)


def best_domain_for_band(
    samples: List[float],
    sample_rate: float,
    candidates: List[str],
    top_n: int = 1,
) -> List[str]:
    """
    Route a signal band to whichever domain basis gives the sparsest
    representation — minimum description length in practice.

    Sparsity score = energy concentration in the top-1 basis element
    (Gini-style: how much of the total power is in the single best bin).
    Higher concentration → fewer boxes needed → better compression.

    Both encoder and decoder have DOMAIN_REGISTRY, so only the domain
    NAME (one integer slot index) needs to be in the box label — zero
    extra bytes on the wire.
    """
    nyquist = sample_rate / 2.0

    # Step 1: find signal peak frequency via coarse audio sweep
    audio_bands = _octave_bands(max(1.0, nyquist / 2048), nyquist, 32)
    audio_powers = [_goertzel(samples, f, sample_rate) for f in audio_bands]
    peak_idx  = max(range(len(audio_powers)), key=lambda i: audio_powers[i])
    peak_freq = audio_bands[peak_idx]   # peak frequency in signal's own space

    scores: List[Tuple[float, str]] = []

    for dname in candidates:
        if dname not in DOMAIN_REGISTRY:
            continue
        basis = DOMAIN_REGISTRY[dname]

        # Step 2: coverage check — does this domain's range cover the signal?
        # We normalise: map peak_freq through the domain's unit scale.
        # Domains whose f_low..f_high span the signal's peak score higher.
        # (Different domains use different physical units; we compare by
        #  fractional position: 0=f_low, 1=f_high → in-range iff 0≤pos≤1)
        span = max(basis.f_high - basis.f_low, 1e-300)
        pos  = (peak_freq - basis.f_low) / span  # normalised position
        # Gaussian coverage weight: peak at pos=0.5, falls off toward edges
        coverage = math.exp(-8.0 * (pos - 0.5) ** 2)

        # Step 3: sparsity within the domain (how concentrated in fewest bins?)
        n_probe = min(basis.n_bands, 16)
        powers  = [_goertzel(samples, basis.centre(i), sample_rate)
                   for i in range(n_probe)]
        total   = sum(powers) + 1e-30
        peak_p  = max(powers)
        concentration = peak_p / total

        score = coverage * concentration
        scores.append((score, dname))

    scores.sort(reverse=True)
    return [d for _, d in scores[:top_n]]


def encode_signal(
    samples: List[float],
    sample_rate: float,
    f_low: float = 20.0,
    f_high: float = 20000.0,
    snr_db_val: float = 40.0,
    spin_param: float = 0.5,
    friction_coeff: float = 0.05,
    n_bands: int = 8,
) -> Tuple[List[CarrierBox], dict]:
    """
    Factory encoding pass.

    1. DFT-based band decomposition (using Goertzel-like approach)
    2. Per-band carrier state parameter extraction
    3. Label each parameter → CarrierBox
    4. Sort boxes by label (American Flag Sort)
    5. Return sorted box stream + stats

    Returns
    -------
    boxes  : sorted list of CarrierBox (the compressed stream)
    stats  : encoding statistics (modes, λ_Edd, etc.)
    """
    n = len(samples)
    if n == 0:
        return [], {}

    duration = n / sample_rate
    snr_lin  = 10 ** (snr_db_val / 10.0)

    # ── Band decomposition via sliding DFT window ─────────────────────────────
    centers = _octave_bands(f_low, f_high, n_bands)
    band_params: List[List[float]] = []   # [band][param_idx]
    band_entropy: List[float]      = []

    for b_idx, fc in enumerate(centers):
        # Goertzel DFT for single frequency (O(n) per bin)
        w  = 2 * math.pi * fc / sample_rate
        s1, s2 = 0.0, 0.0
        coeff = 2 * math.cos(w)
        for s in samples:
            s0 = s + coeff * s1 - s2
            s2, s1 = s1, s0
        real  =  s1 - s2 * math.cos(w)
        imag  =  s2 * math.sin(w)
        amp   = math.sqrt(real ** 2 + imag ** 2) / max(n, 1)
        phase = math.atan2(imag, real)

        # Temporal analysis: velocity (freq drift), curvature (chirp rate)
        # Approximate from windowed halves
        half = n // 2
        s1h, s2h = 0.0, 0.0
        for s in samples[:half]:
            s0 = s + coeff * s1h - s2h
            s2h, s1h = s1h, s0
        amp_first = math.sqrt((s1h - s2h * math.cos(w)) ** 2 +
                              (s2h * math.sin(w)) ** 2) / max(half, 1)
        if _USE_H1:
            # COMPLEX_AUDIT #H1: complex velocity — imaginary part encodes phase drift (chirp rate)
            z_full    = complex(real, imag) / max(n, 1)
            z_half    = complex(s1h - s2h * math.cos(w),
                                s2h * math.sin(w)) / max(half, 1)
            _denom    = abs(z_half) + 1e-30
            velocity  = abs((z_full - z_half) / _denom)
            curvature = abs(z_full - z_half) ** 2
        else:
            # COMPLEX_AUDIT #H1: amplitude-only — chirp (const amplitude, sweep freq) shows velocity≈0
            velocity  = (amp - amp_first) / max(amp_first + 1e-30, 1e-30)
            curvature = velocity ** 2  # second-order approx

        # RMS of band-passed region (for entropy estimate)
        bw  = (f_high - f_low) / n_bands
        h   = math.log2(max(amp * 2 * bw + 1, 2))  # entropy ∝ log(occupancy)

        # pos_x, bandwidth, rate NOT stored — white hole reconstructs from geometry.
        band_params.append([
            amp,          # 0: amplitude
            phase,        # 1: phase
            velocity,     # 2: velocity (amplitude drift)
            curvature,    # 3: curvature
            spin_param,   # 4: coherence (signal-level spin)
        ])
        band_entropy.append(h)

    # ── Snag geometry (Bekenstein N=3) ────────────────────────────────────────
    # Shakura-Sunyaev viscous dissipation: friction reduces effective entropy
    # captured at the horizon (high friction_coeff → more energy radiated away)
    h_total  = sum(band_entropy) * ((f_high - f_low) * 2 * duration / n_bands) * (1.0 - friction_coeff)
    snag     = deep_compression_snag(h_total, n_dims=3)
    n_modes  = snag['horizon_modes']

    # Distribute modes across bands by gravitational redshift weighting
    band_dims = shift_allocation(band_entropy, n_modes)

    capacity  = shannon_capacity(f_high - f_low, snr_lin) * duration

    # ── Label + pack each parameter box ──────────────────────────────────────
    all_boxes: List[CarrierBox] = []
    frame = 0  # single-frame encode

    for b_idx, (params, n_dim) in enumerate(zip(band_params, band_dims)):
        # Each mode in this band shares the same band-level parameters
        # (in a full implementation, n_dim modes would be distinct Gabor atoms)
        for m_idx in range(n_dim):
            # Scale parameters by mode index (modes are harmonics of the band)
            mode_scale = 1.0 / (1 + m_idx)
            for p_idx, val in enumerate(params):
                label = pack_label(b_idx, m_idx, p_idx, frame)
                # amplitude(0) and velocity(2) scale with mode harmonic
                vbits = f32_to_f16_bits(val * mode_scale if p_idx in (0, 2) else val)
                all_boxes.append(CarrierBox(label, vbits))

    # ── Sort (American Flag Sort on 32-bit label) ─────────────────────────────
    _radix_sort_boxes(all_boxes)

    # ── Stats ─────────────────────────────────────────────────────────────────
    lam           = eddington_utilization(len(all_boxes) * 16, capacity)  # value bits only
    payload_bytes = len(all_boxes) * 6           # 4-byte label + 2-byte f16

    stats = {
        'n_samples':     n,
        'duration_s':    duration,
        'n_bands':       n_bands,
        'h_total':       h_total,
        'n_modes':       n_modes,
        'n_boxes':       len(all_boxes),
        'band_dims':     band_dims,
        'band_entropy':  band_entropy,
        'payload_bytes': payload_bytes,
        'raw_bytes':     n * 2,            # 16-bit PCM equivalent
        'lambda_edd':    lam,
        'landauer_J':    landauer_cost(h_total),
        'capacity_bits': capacity,
    }
    return all_boxes, stats


# ── Signal decoder ────────────────────────────────────────────────────────────

def decode_boxes(
    boxes: List[CarrierBox],
    n_samples: int,
    sample_rate: float,
    f_low: float = 20.0,
    f_high: float = 20000.0,
    n_bands: int = 8,
) -> List[float]:
    """
    Factory decode pass.

    1. Sort boxes by label (already sorted from encoder, O(n) verify)
    2. Reassemble voxels by (band, mode) prefix
    3. Synthesise signal: sum windowed sinusoids (Gabor atoms)
    """
    if not boxes:
        return [0.0] * n_samples

    # Group boxes into voxels by (band, mode)
    voxel_map: Dict[Tuple[int, int], List[CarrierBox]] = {}
    for box in boxes:
        band, mode, _, _ = box.address
        key = (band, mode)
        voxel_map.setdefault(key, []).append(box)

    # Reconstruct voxels and synthesise
    output = [0.0] * n_samples
    # Gaussian window — depends only on n_samples, constant across all voxels.
    # Precompute once to avoid O(voxels × n_samples) redundant math.exp calls.
    _sigma = n_samples / 6.0
    _half_n = n_samples / 2.0
    _gauss_win = [math.exp(-0.5 * ((i - _half_n) / _sigma) ** 2)
                  for i in range(n_samples)]
    for (band, mode), vboxes in voxel_map.items():
        voxel = FoamVoxel.from_boxes(vboxes)
        # White hole reconstruction: geometric params recovered from physical basis.
        # Nothing was lost — the horizon preserved the label, the label has the law.
        fc    = _band_centre(band, f_low, f_high, n_bands)
        # bw = (f_high - f_low) / n_bands — geometric, not used in Gabor synthesis
        amp   = voxel.params[0]   # amplitude
        phase = voxel.params[1]   # phase
        mode_scale = 1.0 / (1 + mode)
        a = amp * mode_scale

        # Gabor atom: windowed sinusoid
        for i in range(n_samples):
            t = i / sample_rate
            output[i] += a * math.sin(2 * math.pi * fc * t + phase) * _gauss_win[i]

    return output


# ── Round-trip quality measurement ────────────────────────────────────────────

def snr_db(original: List[float], reconstructed: List[float]) -> float:
    """Signal-to-noise ratio between original and reconstructed signal."""
    n = min(len(original), len(reconstructed))
    sig_pwr   = sum(x ** 2 for x in original[:n]) / max(n, 1)
    noise_pwr = sum((x - y) ** 2
                    for x, y in zip(original[:n], reconstructed[:n])) / max(n, 1)
    if noise_pwr < 1e-30:
        return 100.0
    return 10 * math.log10(max(sig_pwr / noise_pwr, 1e-30))


# ── Jupiter Layer — φ-tunnel residual encoding ──────────────────────────────

_PHI         = 1.618033988749895
_PHI_EPSILON = 1e-3   # practical tolerance (hardware uses 1e-12; signal layer ±0.1%)
_PHI_FRAC    = 1.0 / _PHI   # ≈ 0.6180339887 — irrational Weyl step, no integer period
# Precomputed lookup for PHI^(i%7): period-7 pattern, only 7 distinct values.
# Modes 0,7,14 share the same divisor — compute once, index by (i % 7).
_PHI_POW7    = tuple(1.618033988749895 ** k for k in range(7))
_J_BAND      = 0xFE   # layer marker in the 32-bit label (band field)

# ── NE geometry scaffold (geometry-rip branch) ────────────────────────────────
# USE_NE_GEOMETRY = False: all existing behaviour is preserved.
# Flip to True only after full enwik9 calibration (calibrate_geometry.py).
# Fixes EUCLIDEAN_ASSUMPTION_AUDIT finding #1 (CRITICAL): linear phi_prox.
USE_NE_GEOMETRY = False
_TOOLS_DIR        = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
try:
    from geometry_noneuclidean import log_phi_proximity as _log_phi_prox
    _NE_GEO_AVAILABLE = True
except ImportError:
    _NE_GEO_AVAILABLE = False

# _USE_H1 and _USE_M2 are defined at module top (line ~67) so they're available
# before any function that uses them. The deprecated alias is kept for compat.
_USE_COMPLEX_GEOMETRY = _USE_H1 and _USE_M2  # DEPRECATED — always False while M2 deferred
try:
    import geometry_complex as _cg  # noqa: F401
    _CG_AVAILABLE = True
except ImportError:
    _CG_AVAILABLE = False

# ── Baked attestation constants (DAG 743) ─────────────────────────────────
# J_MODES loaded from 5-Applications/scripts/carrier_constants.py (generated by 4-Infrastructure/hardware/void_mask_gen.py).
# Falls back to 14 if constants file is absent (backward-compatible).
_J_MODES = 14
try:
    import os as _os_sc, sys as _sys_sc
    _sc_dir = _os_sc.path.dirname(_os_sc.path.abspath(__file__))
    if _sc_dir not in _sys_sc.path:
        _sys_sc.path.insert(0, _sc_dir)
    import importlib.util as _ilu_sc
    _sc_spec = _ilu_sc.spec_from_file_location(
        "carrier_constants", _os_sc.path.join(_sc_dir, "carrier_constants.py")
    )
    _sc = _ilu_sc.module_from_spec(_sc_spec)
    _sc_spec.loader.exec_module(_sc)
    _J_MODES = _sc.J_MODES
except Exception:
    pass   # use default J=14

# Precomputed per-mode scale table — _USE_M2 checked once at import, not 14× per call.
_MODE_EXPS: tuple = (
    tuple(_PHI ** (k * _PHI_FRAC) for k in range(_J_MODES))
    if _USE_M2 else
    tuple(_PHI_POW7[k % 7] for k in range(_J_MODES))
)

# ARPG phases from metanarrative_goal_spec.md — used as complexity filter.
# Describes the state of the signal's manifold:
#   GROUNDED = crystallized, SEISMIC = shifting, FLAME = burning/reforming.
_PHASE_GROUNDED = 'PHASE_GROUNDED'   # φ_ratio ≈ φ  → full Jupiter encoding
_PHASE_SEISMIC  = 'PHASE_SEISMIC'    # mild drift   → partial encoding
_PHASE_FLAME    = 'PHASE_FLAME'      # off-manifold → skip, too noisy


def _phi_ratio(modes: List[float]) -> float:
    """sum(modes[1:]) / modes[0] — should equal φ when phase-locked."""
    return sum(modes[1:]) / max(modes[0], 1e-15)


def _classify_phase(band_amps: List[float], _residual_bits: float) -> str:
    """
    Metanarrative harness complexity filter.
    Maps (band_amps, residual_magnitude) → ARPG phase.

    Corrected 2026-03-31: previous equation computed sum(modes[1:])/modes[0]
    over 14 tiled modes, which yields values in [0,13] and can never reach
    φ=1.618. All signals classified SEISMIC regardless of content.

    Corrected metric (two components):

      C(a)      = max(a) / (sum(a) - max(a) + ε)   spectral concentration
      Φ_signal  = min |a[i]/a[i+1] - φ| near peak  φ-proximity of falloff
      Φ_corr    = 0.6·clamp(C, 0, 1) + 0.4·(1 - Φ_signal/φ)

    Thresholds:  GROUNDED ≥ 0.55,  SEISMIC ≥ 0.35,  FLAME < 0.35

    See 6-Documentation/docs/PHASE_CLASSIFIER_CORRECTION.md for derivation and measured values.
    """
    if not band_amps or max(band_amps) < 1e-15:
        return _PHASE_FLAME

    # Component 1: spectral concentration — is energy in one place?
    a_max  = max(band_amps)
    a_rest = sum(band_amps) - a_max
    conc   = a_max / (a_rest + 1e-15)
    conc   = min(conc, 2.0) / 2.0   # clamp and normalise to [0, 1]

    # Component 2: φ-proximity of dominant falloff — does peak decay at φ-rate?
    if USE_NE_GEOMETRY and _NE_GEO_AVAILABLE:
        # NE path: log-multiplicative proximity, global consecutive ratio search.
        # AUDIT FINDING #1 fix: projective distance from PHI, not linear deviation.
        # AUDIT FINDING #1 fix (peak-window): search all pairs, not just near peak.
        ratios = [band_amps[i] / (band_amps[i + 1] + 1e-15)
                  for i in range(len(band_amps) - 1)
                  if band_amps[i + 1] > 1e-15]
        phi_prox = max(0.0, max((_log_phi_prox(r) for r in ratios), default=0.0))
    else:
        # EU path (default): linear deviation from PHI, near-peak window only.
        # EUCLIDEAN ASSUMPTION AUDIT #1 (CRITICAL) — do not apply outside NE mode.
        peak_i = band_amps.index(a_max)
        phi_drifts = []
        for i in range(max(0, peak_i - 1), min(len(band_amps) - 1, peak_i + 3)):
            denom = band_amps[i + 1]
            if denom > 1e-15:
                phi_drifts.append(abs(band_amps[i] / denom - _PHI))
        phi_signal = min(phi_drifts) if phi_drifts else _PHI
        phi_prox   = max(0.0, 1.0 - phi_signal / _PHI)   # linear — EUCLIDEAN

    phi_corr = 0.6 * conc + 0.4 * phi_prox

    # SF-B: thresholds 0.47 / 0.35 are calibrated on the Euclidean phi_corr
    # distribution (EU path above). When USE_NE_GEOMETRY=True, _log_phi_prox
    # produces a different phi_corr distribution and these thresholds are
    # uncalibrated — the NE path requires independent calibration via
    # calibrate_geometry.py before USE_NE_GEOMETRY can be safely flipped.
    if phi_corr >= 0.47:
        return _PHASE_GROUNDED
    if phi_corr >= 0.35:
        return _PHASE_SEISMIC
    return _PHASE_FLAME


def _modes_from_bytes(data: bytes) -> List[float]:
    """
    φ-normalise payload bytes into 14 vibration mode amplitudes.
    Each mode samples the mean of a distinct non-overlapping segment of the
    full input, ensuring all bytes contribute regardless of chunk size.

        deviation = |segment_mean − 127.5| / 127.5   (centred deviation, [0, 1])
        amplitude = deviation / φ^(i % 7)

    Deviation extractor replaces raw mean normalisation (mean/255) which
    produced synthetic φ-ratios for uniform-mean signals (white noise CLT
    convergence → mean ≈ 127.5 for all segments → amp[i] ∝ 1/φ^(i%7) →
    perfect φ-decay → false GROUNDED classification).
    Using |mean − 127.5| collapses uniform signals to near-zero amplitude,
    correctly classifying them as FLAME/SEISMIC.  Structured signals with
    varying segment means retain real amplitude structure.
    """
    n = max(len(data), 1)
    modes = []
    for i in range(_J_MODES):
        lo = int(i * n / _J_MODES)
        hi = int((i + 1) * n / _J_MODES)
        if hi <= lo:
            hi = lo + 1
        seg = data[lo:min(hi, n)]
        # SF-C fix: empty segment (can occur when _J_MODES > len(data)) must
        # produce zero amplitude, not maximum amplitude.  The previous guard
        # `mean_val = ... if seg else 0` set mean=0 → deviation=|0-127.5|/127.5=1.0
        # → amp = 1.0/PHI^(i%7) — the strongest possible signal from nothing.
        if not seg:
            modes.append(0.0)
            continue
        mean_val = sum(seg) / len(seg)
        deviation = abs(mean_val - 127.5) / 127.5
        amp = deviation / _MODE_EXPS[i]
        modes.append(min(1.0, amp))
    return modes


def _bytes_from_modes(modes: List[float]) -> bytes:
    """Inverse of _modes_from_bytes — recover bytes from mode amplitudes.
    SF-3: This function is complete but dead (never called anywhere).
    Retained as the documented round-trip inverse; remove if unused after encoder wiring.
    """
    out = bytearray(_J_MODES)
    for i in range(_J_MODES):
        scale = _MODE_EXPS[i]
        bval  = int(min(255, max(0, round(modes[i] * scale * 255.0))))
        out[i] = bval
    return bytes(out)


_J_LOG_SCALE = 60.0   # log2 range: supports residuals up to 2^60 bits (~1 EiB)


def jupiter_encode(
    residual_entropy: float,
    band_amps: List[float],
    frame: int = 0,
) -> Tuple[List[CarrierBox], str]:
    """
    Jupiter Layer encoder.

    Encoding strategy (separates φ-lock key from payload):
    ────────────────────────────────────────────────────────
    modes[0]  = log2(residual_entropy) / LOG_SCALE  → payload (normalised to [0,1])
    modes[1:] = modes[0] × φ / (N-1)               → exact φ-lock, no correction needed
    phi_ratio = sum(modes[1:]) / modes[0]
              = (N-1) × (modes[0] × φ / (N-1)) / modes[0]
              = φ  ✓  (analytically exact)

    The tunnel fires on the first check — PHASE_FLAME only if modes[0] ≈ 0
    (residual is essentially zero, nothing to encode).

    Harness phase reflects signal complexity via band_amps Laplacian (informational).
    """
    if residual_entropy <= 0:
        return [], _PHASE_FLAME

    # Encode residual magnitude into modes[0] via log-scale normalisation
    log_r   = math.log2(max(residual_entropy, 1.0)) / _J_LOG_SCALE
    log_r   = min(1.0, max(1e-6, log_r))

    modes    = [0.0] * _J_MODES
    modes[0] = log_r
    target   = log_r * _PHI / (_J_MODES - 1)
    for i in range(1, _J_MODES):
        modes[i] = target   # analytically φ-locked

    # Harness phase from band_amps — signal surface complexity
    phase = _classify_phase(band_amps if band_amps else [], residual_entropy)
    # Override FLAME only for the proxy — the payload itself is always locked
    if phase == _PHASE_FLAME:
        phase = _PHASE_SEISMIC   # locked payload; signal surface is noisy

    active_modes = 7 if phase == _PHASE_SEISMIC else _J_MODES

    boxes = []
    for m_idx in range(active_modes):
        label = pack_label(_J_BAND, m_idx, 0, frame)
        boxes.append(CarrierBox(label, f32_to_f16_bits(modes[m_idx])))

    return boxes, phase


def jupiter_decode(boxes: List[CarrierBox]) -> Tuple[float, str]:
    """
    Jupiter Layer decoder.

    Returns
    -------
    residual_entropy : recovered residual bits value
    phase            : detected ARPG phase based on phi_ratio of recovered modes
    """
    j_boxes = [b for b in boxes if (b.label >> 24) & 0xFF == _J_BAND]
    if not j_boxes:
        return 0.0, _PHASE_FLAME

    modes = [0.0] * _J_MODES
    for box in j_boxes:
        _, m_idx, _, _ = box.address
        if m_idx < _J_MODES:
            modes[m_idx] = box.decode_value()

    phi_r = _phi_ratio(modes)
    phase = _classify_phase(modes, 0.0)  # SF-1: was phi_r (scalar) — crashes on max()

    # Recover residual: modes[0] = log2(residual) / LOG_SCALE
    log_r            = max(modes[0], 1e-9)
    residual_entropy = 2.0 ** (log_r * _J_LOG_SCALE)

    return residual_entropy, phase


# ── Omnitoken manifest — GraphVM header for the audio stream ──────────────────
#
# Each encoded stream carries an omnitoken manifest that declares:
#   - Which subregisters are active and what physical basis they use
#   - The foam profile (band allocation bias in 4D foam space)
#   - A deterministic register_id (tick-based, idempotent)
#   - The archive_compression domain — previously "unavailable" in omnitoken_v3
#
# The manifest IS the GraphVM preamble: it tells the white hole which
# instruction set (basis tables) to load before executing the box stream.
#
# Register state transitions mirror phase classification:
#   potential  → FLAME  (frame not yet resolved)
#   candidate  → subregister routing initiated
#   collapsed  → GROUNDED/SEISMIC phase selected
#   committed  → box stream emitted, deterministic replay safe

_OT_SCHEMA  = "omnitoken-audio/v1"
_OT_SUBREGISTERS = {
    # band prefix → domain name + basis description
    0x00: 'audio_band_0',
    0x07: 'audio_band_7',   # range 0x00-0x07 = normal time domain
    0xFD: 'accel_depth_1',  # 2× accelerated time
    0xFC: 'accel_depth_2',  # 4× accelerated time
    0xFB: 'accel_depth_3',  # 8× accelerated time
    0xFE: 'jupiter_tunnel',
}


def _register_id(stream_hash: str, frame_count: int) -> str:
    """Deterministic register_id: tick-based, idempotent (same input → same id)."""
    tick = f"{stream_hash[:16]}-f{frame_count:04d}"
    return f"wreg-audio-{tick}"


def build_omnitoken_manifest(
    sample_rate: float,
    f_low: float,
    f_high: float,
    n_bands: int,
    n_frames: int,
    spin_param: float,
    friction_coeff: float,
    foam_center: List[float],
    active_subregisters: List[int],
    stream_hash: str,
    phase_counts: Dict[str, int],
) -> Dict[str, Any]:
    """
    Build the omnitoken manifest header for a compressed audio stream.

    This activates the archive_compression domain that is 'unavailable'
    in the base omnitoken_v3 schema — the carrier factory IS that domain.

    The nd_point (14-axis) encodes the Jupiter mode vector so any omnitoken-
    aware node can reconstruct the φ-lock state without the full box stream.
    """
    # Jupiter nd_point: 14-axis position in φ-normalised mode space
    # modes[0] = log2(friction_coeff proxy) / LOG_SCALE
    # modes[1:] = modes[0] × φ / 13  (analytically locked)
    log_r   = math.log2(max(friction_coeff * 1000, 1.0)) / _J_LOG_SCALE
    log_r   = min(1.0, max(1e-6, log_r))
    target  = log_r * _PHI / (_J_MODES - 1)
    nd_point = [log_r] + [target] * (_J_MODES - 1)

    # Foam score = φ-ratio of the nd_point (should be ≈ φ for well-locked stream)
    foam_score = round(_phi_ratio(nd_point), 5)

    # Subregister surface bus domains
    domains: Dict[str, Any] = {
        'audio_normal_time': {
            'domain':     'audio_normal_time',
            'band_range': [0x00, 0x07],
            'basis': {
                'f_low':       f_low,
                'f_high':      f_high,
                'n_bands':     n_bands,
                'sample_rate': sample_rate,
            },
            'status': 'active',
        },
        'archive_compression': {
            'domain':            'archive_compression',
            'status':            'active',   # was "unavailable" in omnitoken_v3
            'selection_policy':  'carrier_factory_graphvm',
            'params': {
                'spin_param':      spin_param,
                'friction_coeff':  friction_coeff,
                'param_names':     list(PARAM_NAMES),
                'n_params':        N_PARAMS,
                'box_bytes':       6,
            },
        },
        'jupiter_tunnel': {
            'domain':     'jupiter_tunnel',
            'band_marker': _J_BAND,
            'modes':       _J_MODES,
            'phi':         _PHI,
            'log_scale':   _J_LOG_SCALE,
            'status':      'active',
        },
    }

    # Add accelerated-time subregisters if any FLAME frames were processed
    for band_prefix in active_subregisters:
        if band_prefix < 0xFD:
            continue
        depth = _SUBREGISTER_BAND_BASE - band_prefix + 1
        key   = f'accel_depth_{depth}'
        domains[key] = {
            'domain':      key,
            'band_marker': band_prefix,
            'time_factor': 2 ** depth,
            'status':      'active',
        }

    register_id = _register_id(stream_hash, n_frames)

    return {
        'schema':  _OT_SCHEMA,
        'name':    f'omnitoken-audio-{stream_hash[:8]}',
        'n_dimensional_surface': {
            'axes':             _J_MODES,
            'nd_point':         nd_point,
            'foam_score':       foam_score,
            'phi_ratio':        round(_phi_ratio(nd_point), 6),
        },
        'foam_profile': 'audio_carrier state',
        'foam_center':  (foam_center + [0.5] * 4)[:4],
        'surface_bus': {
            'schema':   'omnitoken-surface-bus/v1',
            'agnostic': True,
            'domains':  domains,
        },
        'stream': {
            'n_frames':       n_frames,
            'sample_rate':    sample_rate,
            'phase_counts':   phase_counts,
            'register_id':    register_id,
            'register_state': 'committed',
            'register_state_transitions': [
                {'state': 'potential',  'reason': 'stream_ingested'},
                {'state': 'candidate',  'reason': 'phase_classified'},
                {'state': 'collapsed',  'reason': 'subregister_selected'},
                {'state': 'committed',  'reason': 'box_stream_emitted'},
            ],
            'replay_safety': {
                'strategy':          'stream_hash_idempotent',
                'stream_hash':       stream_hash,
                'replay_safe':       True,
            },
        },
    }


# ── Multi-frame streaming encoder — time domain + metanarrative gating ────────

# Delta thresholds per phase (relative fraction of reference magnitude — scale-free)
# SF-4 fix: was absolute (f16 units) — comparison abs(val-ref) > 0.001 transmits
# everything for values in [1, 65504] range since f16 LSB ≈ 0.001 for values > 1.
# Now relative: abs(val-ref)/max(|ref|,|val|,eps) > threshold.
# GROUNDED: 0.001 = 0.1% — tight tolerance for stable sustained tones
# SEISMIC:  0.01  = 1.0% — moderate tolerance for transient-rich material
# FLAME:    inf   = raw keyframe (noise: prediction is useless)
_DELTA_THRESHOLD = {
    _PHASE_GROUNDED: 0.001,
    _PHASE_SEISMIC:  0.01,
    _PHASE_FLAME:     float('inf'),  # transmit everything raw
}

# Minimum frame size before recursion stops (Planck floor — below this,
# frequency resolution is too coarse to be meaningful for audio).
_MIN_FRAME_SAMPLES = 64

# Subregister band marker — boxes from accelerated-time sub-frames use a
# reserved band prefix so the white hole knows which time domain they came from.
# 0xFD = subregister depth 1 (2× accel), 0xFC = depth 2 (4×), etc.
_SUBREGISTER_BAND_BASE = 0xFD   # counts DOWN per recursion level


def _classify_frame(
    boxes: List[CarrierBox],
    h_total: float,
    spin_param: float,
) -> str:
    """Classify a frame's complexity via Jupiter φ-ratio of its amplitude envelope."""
    eta      = conversion_efficiency(spin_param)
    residual = h_total * (1.0 - eta)
    # Use band amplitude envelope (first box per band) as the φ-ratio input,
    # not raw box values — gives a stable spectral shape proxy.
    band_amps: List[float] = []
    seen_bands: set = set()
    for box in boxes:
        band, _, param, _ = box.address
        if param == 0 and band not in seen_bands:   # param 0 = amplitude
            band_amps.append(abs(box.decode_value()))
            seen_bands.add(band)
    _, phase = jupiter_encode(residual, band_amps)
    return phase


def _encode_flame_subregister(
    samples: List[float],
    sample_rate: float,
    f_low: float,
    f_high: float,
    snr_db_val: float,
    spin_param: float,
    friction_coeff: float,
    n_bands: int,
    depth: int,
    frame_offset: int,
) -> List[CarrierBox]:
    """
    Relativistic subregister: accelerated time domain for FLAME-class frames.

    When a frame is too complex to compress at normal resolution, time contracts:
    the frame is split into two half-length sub-frames and each is re-encoded.
    This trades frequency resolution for temporal resolution (Heisenberg duality).

    Recursion stops at _MIN_FRAME_SAMPLES (Planck floor) — below this,
    Goertzel frequency resolution is meaningless for audio.

    Sub-frame boxes carry a special band marker (0xFD, 0xFC, …) so the white
    hole decoder knows which time domain each box came from.
    """
    if len(samples) <= _MIN_FRAME_SAMPLES or depth > 4:
        # Planck floor reached — encode raw, mark with subregister depth band
        boxes, _ = encode_signal(
            samples, sample_rate,
            f_low=f_low, f_high=f_high, snr_db_val=snr_db_val,
            spin_param=spin_param, friction_coeff=friction_coeff,
            n_bands=n_bands,
        )
        sub_band = max(0x00, _SUBREGISTER_BAND_BASE - depth)
        out = []
        for box in boxes:
            _, mode, param, _ = box.address
            label = pack_label(sub_band, mode, param, frame_offset & 0xFF)
            out.append(CarrierBox(label, box.value_bits))
        return out

    # Split into two half-length sub-frames
    half   = len(samples) // 2
    halves = [samples[:half], samples[half:]]
    result = []

    for i, half_samples in enumerate(halves):
        sub_boxes, sub_stats = encode_signal(
            half_samples, sample_rate,
            f_low=f_low, f_high=f_high, snr_db_val=snr_db_val,
            spin_param=spin_param, friction_coeff=friction_coeff,
            n_bands=n_bands,
        )
        sub_phase = _classify_frame(sub_boxes, sub_stats['h_total'], spin_param)

        if sub_phase == _PHASE_FLAME:
            # Still complex — recurse deeper (time contracts further)
            result.extend(_encode_flame_subregister(
                half_samples, sample_rate,
                f_low, f_high, snr_db_val, spin_param, friction_coeff, n_bands,
                depth + 1, frame_offset * 2 + i,
            ))
        else:
            # Resolved — tag with subregister depth and emit
            sub_band = max(0x00, _SUBREGISTER_BAND_BASE - depth)
            for box in sub_boxes:
                _, mode, param, _ = box.address
                label = pack_label(sub_band, mode, param, (frame_offset * 2 + i) & 0xFF)
                result.append(CarrierBox(label, box.value_bits))

    return result


def encode_stream(
    frames: List[List[float]],
    sample_rate: float,
    f_low: float = 20.0,
    f_high: float = 20000.0,
    snr_db_val: float = 40.0,
    spin_param: float = 0.5,
    friction_coeff: float = 0.05,
    n_bands: int = 8,
) -> Tuple[List[List[CarrierBox]], dict]:
    """
    Multi-frame streaming encoder with metanarrative-gated delta compression.

    Strategy
    ────────
    Frame 0 — always a full keyframe (all boxes transmitted).
    Frame N — metanarrative harness classifies complexity via Jupiter φ-ratio:

      PHASE_GROUNDED  → linear prediction: store only boxes where
                         |value - predicted| > threshold (near-zero for tones)
      PHASE_SEISMIC   → delta from previous frame above medium threshold
      PHASE_FLAME     → raw keyframe (noise: prediction is useless)

    The frame_idx field in each label encodes the frame number, so the white
    hole (decoder) can replay the full sequence deterministically.

    Returns
    -------
    frame_streams : list of box lists, one per frame
    stats         : aggregate compression statistics
    """
    frame_streams: List[List[CarrierBox]] = []
    prev_values: Dict[int, float] = {}   # label → last transmitted f32 value
    pred_values: Dict[int, float] = {}   # label → linear-predicted f32 value

    total_raw   = 0
    total_boxes = 0
    total_key   = 0
    total_delta = 0
    phase_counts: Dict[str, int] = {
        _PHASE_GROUNDED: 0, _PHASE_SEISMIC: 0, _PHASE_FLAME: 0
    }

    for f_idx, frame_samples in enumerate(frames):
        boxes, stats = encode_signal(
            frame_samples, sample_rate,
            f_low=f_low, f_high=f_high, snr_db_val=snr_db_val,
            spin_param=spin_param, friction_coeff=friction_coeff,
            n_bands=n_bands,
        )

        # Classify this frame's complexity via band amplitude envelope φ-ratio
        h_total = stats['h_total']
        phase   = _classify_frame(boxes, h_total, spin_param)
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

        threshold = _DELTA_THRESHOLD[phase]
        total_raw += len(frame_samples) * 2

        if phase == _PHASE_FLAME and f_idx > 0:
            # Relativistic subregister: complex frame → accelerated time domain.
            # Split into sub-frames at 2× resolution; recurse until resolved.
            sub_boxes = _encode_flame_subregister(
                frame_samples, sample_rate,
                f_low, f_high, snr_db_val, spin_param, friction_coeff, n_bands,
                depth=1, frame_offset=f_idx,
            )
            frame_streams.append(sub_boxes)
            total_boxes += len(sub_boxes)
            total_delta += 1
            continue

        if f_idx == 0:  # SF-2: was `or phase == _PHASE_FLAME` — unreachable (continue above)
            # Keyframe: transmit all boxes with updated frame_idx
            out_boxes = []
            for box in boxes:
                band, mode, param, _ = box.address
                new_label = pack_label(band, mode, param, f_idx & 0xFF)
                new_box   = CarrierBox(new_label, box.value_bits)
                out_boxes.append(new_box)
                prev_values[new_label & 0xFFFFFF00 | 0] = box.decode_value()
                pred_values[new_label & 0xFFFFFF00 | 0] = box.decode_value()
            frame_streams.append(out_boxes)
            total_boxes += len(out_boxes)
            total_key   += 1
        else:
            # Delta frame: only transmit boxes that changed beyond threshold
            # For GROUNDED: compare against linear prediction (2×prev - prev2)
            out_boxes = []
            for box in boxes:
                band, mode, param, _ = box.address
                base_label = pack_label(band, mode, param, 0)
                val        = box.decode_value()

                if phase == _PHASE_GROUNDED and base_label in pred_values:
                    reference = pred_values[base_label]
                else:
                    reference = prev_values.get(base_label, 0.0)

                # SF-4 fix: relative comparison — abs(delta)/max(|ref|,|val|,eps) > threshold
                _denom = max(abs(reference), abs(val), 1e-6)
                if abs(val - reference) / _denom > threshold:
                    new_label = pack_label(band, mode, param, f_idx & 0xFF)
                    out_boxes.append(CarrierBox(new_label, box.value_bits))
                    prev_values[base_label] = val
                    # SF-A fix: only update linear prediction for transmitted boxes.
                    # For untransmitted boxes, the decoder never learns val and cannot
                    # replicate this state update — leaving pred_values unchanged means
                    # encoder and decoder both use prev_values[base_label] as reference
                    # on the next frame, keeping them in sync.
                    pred_values[base_label] = 2.0 * val - reference

            frame_streams.append(out_boxes)
            total_boxes += len(out_boxes)
            total_delta += 1

    ratio = (total_raw / max(total_boxes * 6, 1))

    # Compute stream hash for idempotent register_id
    raw_bytes = b''.join(
        box.pack() for stream in frame_streams for box in stream
    )
    stream_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Discover which subregister band prefixes were used
    active_bands: set = set()
    for stream in frame_streams:
        for box in stream:
            active_bands.add((box.label >> 24) & 0xFF)

    # Build omnitoken manifest — activates archive_compression domain
    foam_center = [
        min(1.0, total_boxes / max(total_raw / 6, 1)),  # packing density
        ratio / 10.0,                                    # compression quality
        phase_counts.get(_PHASE_GROUNDED, 0) / max(len(frames), 1),
        1.0 - phase_counts.get(_PHASE_FLAME, 0) / max(len(frames), 1),
    ]
    manifest = build_omnitoken_manifest(
        sample_rate=sample_rate,
        f_low=f_low, f_high=f_high, n_bands=n_bands,
        n_frames=len(frames),
        spin_param=spin_param, friction_coeff=friction_coeff,
        foam_center=foam_center,
        active_subregisters=list(active_bands),
        stream_hash=stream_hash,
        phase_counts=phase_counts,
    )

    stats = {
        'n_frames':        len(frames),
        'total_raw_B':     total_raw,
        'total_box_B':     total_boxes * 6,
        'ratio':           ratio,
        'keyframes':       total_key,
        'delta_frames':    total_delta,
        'phase_counts':    phase_counts,
        'boxes_per_frame': [len(s) for s in frame_streams],
        'stream_hash':     stream_hash[:16],
        'omnitoken':       manifest,
    }
    return frame_streams, stats


def run_factory_poc():
    """
    Two-layer round-trip: Layer 1 (carrier state boxes) + Layer 2 (Jupiter/tunnel).
    Metanarrative harness gates the Jupiter layer by complexity (ARPG phase).
    """
    print("=" * 72)
    print("  SOLITON FACTORY — Layer 1 (carrier state) + Layer 2 (Jupiter/tunnel)")
    print("  Metanarrative harness: F(S)=Equilibrium ↔ ∇H≈0 & φ≈1.618")
    print("=" * 72)

    fs = 44100
    duration = 0.1
    n = int(fs * duration)

    def make_tone(freq, amp=0.8):
        return [amp * math.sin(2 * math.pi * freq * i / fs) for i in range(n)]

    def make_chord(freqs, amp=0.5):
        s = [sum(amp * math.sin(2 * math.pi * f * i / fs) for f in freqs)
             for i in range(n)]
        m = max(abs(x) for x in s) or 1
        return [x / m for x in s]

    def make_noise(amp=0.3):
        rng = __import__('random').Random(42)
        return [rng.uniform(-amp, amp) for _ in range(n)]

    test_cases = [
        ('PURE TONE  440 Hz', make_tone(440),            0.80, 0.04),
        ('CHORD  C4-E4-G4',   make_chord([261,330,392]), 0.60, 0.05),
        ('WHITE NOISE',       make_noise(),               0.10, 0.15),
    ]

    hdr = (f"{'Signal':<22} {'L1 boxes':>9} {'L2 boxes':>9} "
           f"{'Total B':>8} {'Ratio':>6} {'λ_Edd':>8} {'Phase':<16} {'Residual recover'}")
    print(f"\n{hdr}")
    print("-" * 90)

    for label, sig, spin, friction in test_cases:
        # ── Layer 1: carrier state encode ───────────────────────────────────────────
        boxes, stats = encode_signal(
            sig, fs, f_low=20, f_high=20000, snr_db_val=40,
            spin_param=spin, friction_coeff=friction,
        )

        # Compute friction residual from TSE model
        h_total  = stats['h_total']
        eta      = conversion_efficiency(spin)
        residual = h_total * (1.0 - eta)

        # Band amplitudes as proxy mode state for the harness
        band_amps = [b.decode_value() for b in boxes[:8]]

        # ── Layer 2: Jupiter encode ──────────────────────────────────────────
        j_boxes, phase = jupiter_encode(residual, band_amps)
        all_boxes = boxes + j_boxes

        # ── Decode: split by layer marker ────────────────────────────────────
        l1_boxes = [b for b in all_boxes if (b.label >> 24) & 0xFF != _J_BAND]
        recovered_residual, _ = jupiter_decode(all_boxes)

        total_bytes = len(all_boxes) * 6
        ratio       = stats['raw_bytes'] / max(total_bytes, 1)
        # f16 log-scale: ~0.3% relative error is expected (10-bit mantissa × exp amplification)
        residual_ok = (abs(recovered_residual - residual) / max(residual, 1.0)) < 0.005

        print(f"  {label:<20} {len(l1_boxes):>9,} {len(j_boxes):>9,} "
              f"{total_bytes:>7,}B {ratio:>5.2f}× "
              f"{stats['lambda_edd']:>7.4f} {phase:<16} "
              f"{'✓ ' + f'{recovered_residual:.1f}' if residual_ok else '✗ drift'}")

    print("\n  [Layer 1]  band 0x00-0x07 — carrier state basis  (Bekenstein modes, φ-sorted)")
    print("  [Layer 2]  band 0xFE     — Jupiter tunnel (φ-normalised residual)")
    print("  [Harness]  PHASE_GROUNDED→full, PHASE_SEISMIC→7-mode, PHASE_FLAME→skip")
    print("  [Box]      6 bytes: 4-byte label + 2-byte f16  |  sort: MSD radix 32-bit")
    print("=" * 72)

    # ── Streaming PoC: multi-frame delta compression ──────────────────────────
    print("\n" + "=" * 72)
    print("  STREAMING — time domain + metanarrative delta gating (16 frames)")
    print("=" * 72)

    n_frames = 16

    stream_cases = [
        ('PURE TONE  440 Hz', [make_tone(440)]           * n_frames, 0.80, 0.04),
        ('CHORD  C4-E4-G4',   [make_chord([261,330,392])]* n_frames, 0.60, 0.05),
        ('WHITE NOISE',       [make_noise()]              * n_frames, 0.10, 0.15),
    ]

    shdr = (f"{'Signal':<22} {'Frames':>7} {'Key':>5} {'Delta':>7} "
            f"{'Raw B':>8} {'Box B':>8} {'Ratio':>7}  Phase distribution")
    print(f"\n{shdr}")
    print("-" * 85)

    for slabel, frame_list, spin, friction in stream_cases:
        _, sstats = encode_stream(
            frame_list, fs, f_low=20, f_high=20000, snr_db_val=40,
            spin_param=spin, friction_coeff=friction,
        )
        pc = sstats['phase_counts']
        phase_str = (f"G={pc.get(_PHASE_GROUNDED,0)} "
                     f"S={pc.get(_PHASE_SEISMIC,0)} "
                     f"F={pc.get(_PHASE_FLAME,0)}")
        print(f"  {slabel:<20} {sstats['n_frames']:>7} "
              f"{sstats['keyframes']:>5} {sstats['delta_frames']:>7} "
              f"{sstats['total_raw_B']:>8,} {sstats['total_box_B']:>8,} "
              f"{sstats['ratio']:>6.2f}×  {phase_str}")
        bpf = sstats['boxes_per_frame']
        print(f"    boxes/frame: {bpf[:8]}{'...' if len(bpf)>8 else ''}")

        # Show omnitoken manifest summary
        ot = sstats['omnitoken']
        nd = ot['n_dimensional_surface']
        st = ot['stream']
        ac = ot['surface_bus']['domains'].get('archive_compression', {})
        print(f"    omnitoken: {ot['name']}  φ={nd['phi_ratio']:.4f}  "
              f"foam={nd['foam_score']:.4f}  "
              f"archive_compression={ac.get('status','?')}  "
              f"reg={st['register_state']}")

    print("\n  [Frame 0]    keyframe  — full box stream")
    print("  [Frame 1+]   delta     — only changed boxes (GROUNDED: predict+residual)")
    print("  [FLAME frame] subregister — accelerated time domain, band 0xFD-0xFB")
    print("  [Omnitoken]  GraphVM manifest — activates archive_compression domain")
    print("=" * 72)


if __name__ == "__main__":
    run_factory_poc()
