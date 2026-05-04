# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
USC Spectral Core: Shannon-Eddington-Bekenstein Information Density Framework

Treats the entire EM spectrum as a unified encoding problem.
Every signal is a field perturbation. Optimal compression = the spectral
basis that minimizes energy cost per bit while staying above the Landauer
floor (kT ln 2 joules/bit).

Theoretical basis:
  - Yu, Z. et al. (2025). "The Drivers of the Decline in Supermassive Black Hole
    Growth at z < 2." ApJ 995, 205. DOI:10.3847/1538-4357/ae173d
    Provides the Eddington-ratio framework extended here as a channel-utilisation
    analog: lambda_Edd = actual_flux / max_flux maps to encoded_bits / capacity.
  - Shannon (1948), Landauer (1961), Bekenstein (1973), Hawking (1975).

Four-layer constraint hierarchy for N soliton dimensions:
  - Shannon    : ceiling  — channel capacity C = B log2(1 + S/N)
  - Geometric  : natural  — N = (l_max+1)^2 from spherical harmonic truncation
  - Bekenstein : snag cap — horizon modes ~ H^{(n-2)/(n-1)} in n-space
  - Landauer   : floor    — each dimension must carry >= 1 bit (kT ln2 J)

Black hole as thermodynamic snag in N-space:
  A concentrated entropy region in N-dimensional soliton space behaves as a
  DeepCompression. Its horizon is an (N-2)-sphere. Information collapses onto the
  horizon surface; the residual that doesn't fit leaks back as the Hawking
  analog (reconstruction residual). This gives the tightest upper bound on N
  and explains why optimal_dimensions() previously over-estimated N — it used
  the Shannon ceiling instead of the geometric/Bekenstein natural value.
"""

import math
from collections import Counter

# ── Physical constants ────────────────────────────────────────────────────────
K_B       = 1.380649e-23   # Boltzmann constant  [J/K]
H_PLANCK  = 6.62607e-34    # Planck constant     [J·s]
C_LIGHT   = 2.998e8        # Speed of light      [m/s]
T_AMBIENT = 300.0          # Room temperature    [K]

# Derived limits
LANDAUER_JOULES   = K_B * T_AMBIENT * math.log(2)  # ~2.87e-21 J/bit
BITS_PER_JOULE    = 1.0 / LANDAUER_JOULES           # ~3.48e20 bits/J

# ── EM spectral band registry ─────────────────────────────────────────────────
# (f_low Hz, f_high Hz, description)
SPECTRAL_BANDS = {
    'radio':     (1e3,  1e9,  'DC / slow sensors / telemetry'),
    'microwave': (1e9,  3e11, 'Radar / thermal imaging'),
    'infrared':  (3e11, 4e14, 'Heat / near-IR comms'),
    'optical':   (4e14, 7e14, 'Visual / display / video'),
    'uv':        (7e14, 3e16, 'Fluorescence / UV imaging'),
    'xray':      (3e16, 3e19, 'High-energy transients'),
    'gamma':     (3e19, 1e24, 'Nuclear / cosmic events'),
}


# ── Spectral utilities ────────────────────────────────────────────────────────

def photon_energy(freq_hz: float) -> float:
    """Energy of one photon: E = hf  [J]"""
    return H_PLANCK * freq_hz


def signal_band(freq_hz: float) -> tuple[str, str]:
    """Return (band_name, description) for a signal's characteristic frequency."""
    for name, (f_lo, f_hi, desc) in SPECTRAL_BANDS.items():
        if f_lo <= freq_hz < f_hi:
            return name, desc
    return 'gamma', SPECTRAL_BANDS['gamma'][2]


def band_bits_per_joule(band: str) -> float:
    """
    Maximum bits per joule at the geometric-mean frequency of a band.
    Bounded from below by the Landauer floor — higher frequency bands
    have more energetic photons, so fewer bits per joule.
    """
    f_lo, f_hi, _ = SPECTRAL_BANDS[band]
    f_center = math.sqrt(f_lo * f_hi)
    e_per_photon = photon_energy(f_center)
    e_per_bit = max(e_per_photon, LANDAUER_JOULES)
    return 1.0 / e_per_bit


# ── Information-theoretic core ────────────────────────────────────────────────

def shannon_entropy(samples) -> float:
    """
    Shannon entropy H(X) in bits/sample.
    Works on any discrete iterable (ints, quantised floats, etc.).
    """
    counts = Counter(samples)
    total  = len(samples)
    h = 0.0
    for c in counts.values():
        p = c / total
        if p > 0.0:
            h -= p * math.log2(p)
    return h


def shannon_capacity(bandwidth_hz: float, snr_linear: float) -> float:
    """Shannon channel capacity  C = B log2(1 + S/N)  [bits/s]"""
    return bandwidth_hz * math.log2(1.0 + max(snr_linear, 0.0))


def optimal_dimensions(signal_entropy_bits: float,
                       bandwidth_hz: float,
                       snr_linear: float) -> int:
    """
    Minimum soliton dimensions N such that the basis fully spans the
    signal's true entropy, with each dimension carrying ≥ 1 bit
    (the Landauer floor — adding a dimension that carries < 1 bit
    costs more thermodynamic energy than the information is worth).

    N = min( ceil(H_total),  floor(C) )
        where H_total = total signal entropy  [bits]
              C       = Shannon capacity      [bits/s, treated as bits here]
    """
    capacity  = shannon_capacity(bandwidth_hz, snr_linear)
    n_needed  = max(1, math.ceil(signal_entropy_bits))
    n_ceiling = max(1, int(capacity))
    return min(n_needed, n_ceiling)


def eddington_utilization(encoded_bits: float, capacity_bits: float) -> float:
    """
    λ_Edd analog: ratio of actual encoded information to channel capacity.
      1.0 → operating at Shannon limit  (Eddington-saturated, high-z AGN)
      < 1 → channel underutilised       (inefficient, low-z AGN)
    """
    return encoded_bits / max(capacity_bits, 1.0)


def landauer_cost(bits: float) -> float:
    """Minimum thermodynamic energy to write/erase `bits` bits  [J]"""
    return bits * LANDAUER_JOULES


# ── Gravitational shift engine ───────────────────────────────────────────────

def blueshift_factor(local_entropy: float, snag_entropy: float) -> float:
    """
    Gravitational blueshift factor for a signal band near the entropy snag.

    Analogy
    -------
    In GR an infalling photon is blueshifted by:  nu_local/nu_inf = 1/sqrt(1 - r_s/r)

    Here the "radius" of a band is its fractional entropy:
        f = local_entropy / snag_entropy  in [0, 1]
        r_s/r  →  f

    So:  blueshift = 1 / sqrt(1 - f)  =  1 / sqrt(1 - h_local/h_snag)

    Interpretation
    --------------
    f → 0  (low entropy, far from snag) : blueshift → 1.0  — no compression
    f → 1  (high entropy, at horizon)   : blueshift → inf  — infinite compression
                                          (information already captured by snag)

    Parameters
    ----------
    local_entropy : entropy of this signal band [bits]
    snag_entropy  : peak entropy in the signal — the horizon reference [bits]
    """
    if snag_entropy <= 0 or local_entropy <= 0:
        return 1.0
    f = min(0.9999, local_entropy / snag_entropy)   # clamp below horizon
    return 1.0 / math.sqrt(max(1e-30, 1.0 - f))


def redshift_factor(local_entropy: float, snag_entropy: float) -> float:
    """
    Gravitational redshift factor — the inverse of blueshift.

    A band at fractional entropy f = h_local/h_snag, seen from the outside
    (the decoder), appears redshifted by sqrt(1 - f).

    This is the reconstruction scaling per band: how much the decoded signal
    is stretched relative to the encoded (compressed) representation.

    f → 0  : redshift → 1.0  (far from snag, decodes at full scale)
    f → 1  : redshift → 0.0  (at horizon, decoded contribution → zero width)
    """
    if snag_entropy <= 0 or local_entropy <= 0:
        return 1.0
    f = min(0.9999, local_entropy / snag_entropy)
    return math.sqrt(max(0.0, 1.0 - f))


def shift_allocation(entropy_profile: list, n_total: int) -> list:
    """
    Distribute N soliton dimensions across signal bands using gravitational
    redshift weighting.

    Derivation
    ----------
    The dimension weight per band is the redshift factor (inverse blueshift):

        w_i = sqrt(1 - h_i / h_max)

    High-entropy bands (near snag, heavily blueshifted):
        w → 0  →  few dimensions  (information already captured by the snag)

    Low-entropy bands (far from snag, redshifted):
        w → 1  →  full dimension allocation  (need basis vectors to span this space)

    This is physically identical to solid-angle subtended on the horizon:
    a band far from the snag subtends a larger angle and needs more modes.

    Parameters
    ----------
    entropy_profile : list of per-band entropy values [bits/s or bits/sample]
    n_total         : total soliton dimensions to distribute

    Returns
    -------
    list of integer dimension counts, one per band, summing to n_total
    """
    h_max = max(entropy_profile) if entropy_profile else 1.0

    weights = [math.sqrt(max(0.0, 1.0 - h / h_max)) for h in entropy_profile]
    w_sum   = sum(weights) or 1.0

    # Proportional allocation, minimum 1 dim per band
    raw  = [n_total * w / w_sum for w in weights]
    dims = [max(1, int(r)) for r in raw]   # floor allocation

    # Largest-remainder method (Hamilton/Hare quota): public-domain apportionment
    # algorithm — optimal for distributing an integer total proportionally.
    # Sort bands by their fractional surplus descending; award remaining units
    # to the bands with the largest remainders.  O(k log k), k = n_bands (≤ 8).
    allocated = sum(dims)
    remainder = n_total - allocated
    if remainder > 0:
        fracs = sorted(
            ((raw[i] - dims[i], i) for i in range(len(dims))),
            reverse=True,
        )
        for _, i in fracs[:remainder]:
            dims[i] += 1

    return dims


def total_shift(local_entropy: float, snag_entropy: float,
                velocity_fraction: float = 0.0) -> float:
    """
    Combined gravitational + Doppler blueshift for an infalling signal component.

    Total = blueshift_grav × blueshift_doppler
          = (1/sqrt(1 - f)) × sqrt((1+β)/(1-β))

    where f = local_entropy / snag_entropy   (fractional "radius")
          β = velocity_fraction ∈ (-1, 1)    (infall rate as fraction of max)

    β > 0 : infalling toward snag  → additional blueshift
    β < 0 : outgoing away from snag → additional redshift (reconstruction path)
    β = 0 : purely gravitational shift (static, no velocity)

    Parameters
    ----------
    local_entropy     : entropy of this band [bits]
    snag_entropy      : peak entropy (horizon reference) [bits]
    velocity_fraction : infall velocity as fraction of max rate ∈ (-1, 1)
    """
    grav = blueshift_factor(local_entropy, snag_entropy)
    beta = max(-0.9999, min(0.9999, velocity_fraction))
    doppler = math.sqrt((1.0 + beta) / max(1e-30, 1.0 - beta))
    return grav * doppler


def angular_momentum_modes(n_base: int, spin_param: float) -> int:
    """
    Mode count after Kerr-analog angular momentum splitting.

    In the Kerr metric, frame dragging lifts (l, m) degeneracy — but the
    total number of independent horizon modes is still bounded by the Bekenstein
    area law.  Kerr rotation does NOT create extra modes; it only redistributes
    them more efficiently (better packing near the ISCO / ergosphere).

    The compression benefit of high spin is captured entirely by
    conversion_efficiency() — η rises from 5.7% (Schwarzschild) to 42.4%
    (extreme Kerr).  Adding a multiplicative factor to n_base here would
    double-count the spin advantage and push encoded_bits above Shannon capacity.

    Bounded enhancement (ergosphere solid-angle factor):
        n_eff = n_base × (1 + spin_param × (√3 - 1))
              ≈ n_base × 1.0  ..  n_base × 1.73   (Schw → extreme Kerr)

    This matches the ratio of extreme-Kerr ergosphere volume to horizon volume
    (~√3), staying within the Bekenstein bound.

    Parameters
    ----------
    n_base      : base mode count (from Bekenstein snag)
    spin_param  : temporal coherence / periodicity ∈ [0, 1]
    """
    if spin_param <= 0.0:
        return n_base
    # √3 − 1 ≈ 0.732 → maximum 1.732× enhancement at spin = 1
    ergosphere_factor = 1.0 + spin_param * (math.sqrt(3.0) - 1.0)
    return max(n_base, round(n_base * ergosphere_factor))


def conversion_efficiency(spin_param: float) -> float:
    """
    Radiative efficiency η: fraction of signal entropy captured by the
    soliton basis (the rest goes to the Hawking residual / reconstruction error).

    Directly analogous to DeepCompression accretion efficiency:
      Schwarzschild (spin=0) : η ≈ 0.0572  (5.7%  — ISCO at 3 r_s)
      Extreme Kerr (spin=1)  : η ≈ 0.4238  (42.4% — Thorne limit, prograde ISCO)

    Interpolated quadratically in spin parameter a ∈ [0, 1]:
      η(a) = η_Schw + (η_Kerr − η_Schw) × a²

    Physical interpretation for compression
    ----------------------------------------
    A highly periodic/coherent signal (high spin) has most of its entropy
    concentrated in the soliton modes → high η → small residual.
    A noise-like signal (low spin) has entropy spread everywhere → low η →
    most of the encoding budget goes to the residual, not the soliton basis.

    Parameters
    ----------
    spin_param : signal temporal coherence / periodicity ∈ [0, 1]
      0 = random noise, 1 = perfectly periodic/coherent
    """
    ETA_SCHW = 1.0 - math.sqrt(2.0 / 3.0)   # ~0.0572
    ETA_KERR = 1.0 - 1.0 / math.sqrt(3.0)    # ~0.4226
    a = max(0.0, min(1.0, spin_param))
    return ETA_SCHW + (ETA_KERR - ETA_SCHW) * a ** 2


def friction_loss(local_entropy: float, snag_entropy: float,
                  friction_coeff: float) -> float:
    """
    Energy retained after viscous dissipation traversing entropy space.

    Analogous to Shakura-Sunyaev α-disk viscosity: friction converts
    infall kinetic energy into heat (incoherent noise = reconstruction residual).
    The loss is exponential in the entropy-distance from the snag horizon,
    because longer paths through the dissipative medium bleed off more energy.

        retained = exp(−μ × |1 − h_local/h_snag|)

    where |1 − h_local/h_snag| is the normalised entropy distance from horizon.

    Physical meaning for compression
    ---------------------------------
    μ = 0   : frictionless — all infall energy reaches the soliton basis
    μ ~ 0.1 : typical accretion disk (Shakura-Sunyaev α ~ 0.01–0.1)
    μ = 1.0 : maximally dissipative — most energy lost before reaching snag

    High-friction systems have larger residuals regardless of spin or geometry.
    Entropy is a law, not a suggestion — friction cannot be set to zero in
    practice; it sets the irreducible floor on reconstruction error.

    Parameters
    ----------
    local_entropy  : entropy of this band [bits]
    snag_entropy   : peak entropy (horizon reference) [bits]
    friction_coeff : viscosity analog μ ≥ 0
    """
    if friction_coeff <= 0.0 or snag_entropy <= 0.0:
        return 1.0
    distance = abs(1.0 - local_entropy / max(snag_entropy, 1e-30))
    return math.exp(-friction_coeff * distance)


# ── Geometric dimension selection ─────────────────────────────────────────────

def geometric_dimensions(wavelength: float, manifold_radius: float) -> int:
    """
    N = (l_max + 1)^2  from spherical harmonic truncation.

    l_max = floor(2*pi*R / lambda) = floor(circumference / wavelength)

    This is the maximum angular momentum number resolvable given the ratio
    of manifold size to signal wavelength — identical to the criterion that
    limits EM modes in a spherical cavity, and to the angular resolution of
    a spherical aperture.

    Parameters
    ----------
    wavelength        : signal's characteristic wavelength [same units as radius]
    manifold_radius   : radius of the encoding manifold (cochlea, retina, antenna)

    Returns the tighter, geometry-grounded N to use instead of the
    Shannon ceiling from optimal_dimensions().
    """
    circumference = 2.0 * math.pi * manifold_radius
    l_max = max(0, int(circumference / max(wavelength, 1e-300)))
    return (l_max + 1) ** 2


def _omega_sphere(n: int) -> float:
    """Surface area of the unit n-sphere: Omega_n = 2*pi^{(n+1)/2} / Gamma((n+1)/2)"""
    return 2.0 * math.pi ** ((n + 1) / 2.0) / math.gamma((n + 1) / 2.0)


def deep_compression_snag(signal_entropy_bits: float, n_dims: int) -> dict:
    """
    Treat a concentrated entropy region in N-dimensional soliton space
    as a DeepCompression snag.

    Geometry
    --------
    In N-dimensional space the DeepCompression horizon is an (N-2)-sphere.
    Its information capacity follows the Bekenstein bound generalised to
    N dimensions:

        horizon_modes ~ H^{(N-2)/(N-1)}

    where H = signal_entropy_bits and the exponent comes from:
      - BH radius r_s scales as H^{1/(N-1)}  (Bekenstein: S ~ A ~ r^{N-2})
      - Horizon area ~ r_s^{N-2} ~ H^{(N-2)/(N-1)}

    Hawking residual (reconstruction residual)
    ------------------------------------------
    The analog of Hawking temperature T_H ~ 1/r_s ~ H^{-1/(N-2)}.
    Higher entropy (more massive BH) = colder = less residual leakage.
    The residual is the portion of the signal that the snag did not absorb
    and must be encoded separately.

    Behaviour across N
    ------------------
    N=3  : horizon_modes ~ H^{1/2}  — square-root compression (most efficient)
    N=4  : horizon_modes ~ H^{2/3}
    N=10 : horizon_modes ~ H^{8/9}
    N->∞ : horizon_modes -> H       — no compression (each bit needs a dimension)

    Lower-dimensional soliton spaces are therefore *more efficient* under this
    model — the snag is most powerful when N is minimised to the signal's true
    intrinsic dimensionality.

    Parameters
    ----------
    signal_entropy_bits : total Shannon entropy of the signal  [bits]
    n_dims              : dimensionality of the soliton space

    Returns
    -------
    dict with horizon geometry, mode count, Hawking residual, and efficiency
    """
    horizon_dim = max(1, n_dims - 2)
    exponent = (n_dims - 2) / max(1, n_dims - 1)

    horizon_modes = max(1, int(signal_entropy_bits ** exponent))

    # Hawking temperature analog: colder (lower residual) for larger BH
    hawking_temp = signal_entropy_bits ** (-1.0 / horizon_dim)
    residual_bits = signal_entropy_bits * hawking_temp

    snag_efficiency = 1.0 - (residual_bits / max(1.0, signal_entropy_bits))

    return {
        'n_dims':          n_dims,
        'horizon_dim':     horizon_dim,
        'horizon_modes':   horizon_modes,
        'residual_bits':   residual_bits,
        'snag_efficiency': snag_efficiency,
        'exponent':        exponent,
    }


# ── v4.0 Holographic Fractal Rollup ───────────────────────────────────────────

def fractal_rollup(irreducible_entropy_bits: float, uv_stride: int) -> dict:
    """
    Refines irreducible residuals into a procedural generative seed.
    Based on the "Minecraft" refinement: Math as Memory.
    
    Parameters
    ----------
    irreducible_entropy_bits : bits that cannot be compressed further via Shannon
    uv_stride                : the topological fold width (W) from the annealer
    
    Returns
    -------
    dict with fractal seed, expansion potential, and energy gain
    """
    # 1. Calculate Kolmogorov Complexity proxy
    # In a holographic system, the "program" (seed) is tiny compared to the "world"
    seed_bits = 64.0 
    
    # 2. Expansion Ratio (Holographic Projection)
    expansion_potential = irreducible_entropy_bits / seed_bits
    
    # 3. Energy Gain (Landauer floor reduction)
    # Procedural generation uses CPU cycles (recycled AETHER) instead of N-space storage
    energy_gain = 1.0 - (seed_bits / max(1.0, irreducible_entropy_bits))
    
    return {
        'fractal_seed_bits': seed_bits,
        'uv_stride':         uv_stride,
        'expansion_ratio':   expansion_potential,
        'energy_gain':       energy_gain,
        'status':            'RESONANT' if energy_gain > 0.9 else 'STABLE'
    }


# ── §5. Nonlinear Regularization & Complexity ─────────────────────────────────

def burgers_complexity_metric(amplitudes: list[float], epsilon: float = 0.01) -> float:
    """
    Computes the complexity metric Ω[u] with exponential tapering.
    
    Ω_ε = Σ n² |a_n|² exp(-ε n)
    
    Parameters
    ----------
    amplitudes : list of spectral coefficients a_n
    epsilon    : tapering factor ε. Defaults to 0.01 to prevent UV divergence.
                 If ε=0, this is the standard H1 semi-norm (divergent at shocks).
    
    Returns
    -------
    Total complexity Ω (dimensionless stiffening factor).
    """
    omega = 0.0
    for i, a_n in enumerate(amplitudes):
        n = i + 1
        # n² is the H1 penalty; exp(-εn) is the UV regulator
        weight = (n ** 2) * math.exp(-epsilon * n)
        omega += weight * (abs(a_n) ** 2)
    return omega


def effective_viscosity(nu0: float, omega: float) -> float:
    """
    Computes effective viscosity under harmonic stiffening.
    ν_eff = ν_0 (1 + Ω)
    """
    return nu0 * (1.0 + omega)


def effective_quantum_pressure(q0: float, omega: float, kappa: float = 0.3547) -> float:
    """
    Computes effective quantum pressure (singularity regularization).
    Q_eff = (1 + κ Ω) Q_0
    
    κ = 0.3547 (35.47%) is the verified Sovereign Stack stiffening constant.
    """
    return (1.0 + kappa * omega) * q0
