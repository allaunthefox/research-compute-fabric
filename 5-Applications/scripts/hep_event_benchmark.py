#!/usr/bin/env python3
"""
hep_event_benchmark.py — High-Energy Physics event genomes on the RGFlow manifold.

Treats particle-collision events as genomes sampled from a physical lawfulness
manifold. Generates three populations:
  A: Standard Model background
  B: SM background + planted resonance (pp → X → μ⁺μ⁻ at 750 GeV)
  C: Detector noise / corrupted reconstruction

Each event is encoded into the 18-bit unified genome, evaluated against the
precomputed RGFlow adaptation surface, and scored with the physics fitness:

  F(g) = w₁·L_phys(g) + w₂·M_RG(g) + w₃·A(g) − w₄·R_SM(g) − w₅·N_det(g)

Output: JSON report + classification statistics demonstrating basin separation.
"""

import json
import struct
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

SEED = 42
np.random.seed(SEED)

# Population sizes
N_SM = 10_000
N_RESONANCE = 1_000
N_NOISE = 2_000

# Planted resonance parameters
RESONANCE_MASS = 750.0  # GeV
RESONANCE_WIDTH = 5.0   # GeV
SIGNAL_FRACTION = 0.10  # 10% of resonance population has the signal

# Fitness weights
W_PHYS = 0.35   # L_phys — conservation-law lawfulness
W_RG = 0.20     # M_RG — RGFlow stability margin
W_ATTRACTOR = 0.20  # A — attractor specificity
W_SM = 0.10     # R_SM — SM background residual penalty
W_NOISE = 0.35  # N_det — detector-noise likelihood (heavy penalty)

# Genome encoding constants
ADDR_SPACE = 262_144
ENTRY_BYTES = 6 * 4

# RGFlow LUT path
RGFLOW_BIN = Path("5-Applications/out/rgflow_adaptation_surface.bin")


# ═══════════════════════════════════════════════════════════════════════════
# Event structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Particle:
    pdg: int        # PDG code proxy
    px: float
    py: float
    pz: float
    E: float
    charge: int

@dataclass
class EventGenome:
    particles: List[Particle]
    missing_et_x: float
    missing_et_y: float
    population: str  # 'SM', 'resonance', 'noise'
    has_signal: bool = False


# ═══════════════════════════════════════════════════════════════════════════
# Synthetic event generators
# ═══════════════════════════════════════════════════════════════════════════

def generate_sm_background(n_events: int) -> List[EventGenome]:
    """Generate Standard Model-like background events.
    Soft spectrum, exponential pT falloff, broad mass distribution."""
    events = []
    for _ in range(n_events):
        n_particles = np.random.poisson(12) + 2
        particles = []
        total_charge = 0
        for _ in range(n_particles):
            pt = np.random.exponential(30.0)
            eta = np.random.uniform(-2.5, 2.5)
            phi = np.random.uniform(0, 2 * np.pi)
            mass = np.random.exponential(0.5)
            charge = np.random.choice([-1, 0, 1])
            # Enforce approximate charge conservation
            if total_charge + charge > 2:
                charge = -1
            elif total_charge + charge < -2:
                charge = 1
            total_charge += charge
            px = pt * np.cos(phi)
            py = pt * np.sin(phi)
            pz = pt * np.sinh(eta)
            E = np.sqrt(px**2 + py**2 + pz**2 + mass**2)
            particles.append(Particle(
                pdg=np.random.choice([11, 13, 22, 211, 130, 2212]),
                px=px, py=py, pz=pz, E=E, charge=charge
            ))
        # Small missing ET from neutrino proxy
        missing_et_x = np.random.normal(0, 5)
        missing_et_y = np.random.normal(0, 5)
        events.append(EventGenome(
            particles=particles,
            missing_et_x=missing_et_x,
            missing_et_y=missing_et_y,
            population='SM',
            has_signal=False
        ))
    return events


def generate_planted_resonance(n_events: int) -> List[EventGenome]:
    """Generate SM background with a planted dimuon resonance at 750 GeV."""
    events = []
    bg_events = generate_sm_background(n_events)
    for ev in bg_events:
        ev.population = 'resonance'
        if np.random.random() < SIGNAL_FRACTION:
            ev.has_signal = True
            # Inject back-to-back dimuon pair with resonant mass
            mass = np.random.normal(RESONANCE_MASS, RESONANCE_WIDTH)
            pt = np.random.exponential(50.0) + 20.0
            phi = np.random.uniform(0, 2 * np.pi)
            eta = np.random.normal(0, 0.5)
            px = pt * np.cos(phi)
            py = pt * np.sin(phi)
            pz = pt * np.sinh(eta)
            E = np.sqrt(px**2 + py**2 + pz**2 + mass**2)
            E_mu = E / 2.0
            # Muon 1
            ev.particles.append(Particle(pdg=13, px=px/2, py=py/2, pz=pz/2, E=E_mu, charge=+1))
            # Muon 2 (back-to-back in transverse plane)
            ev.particles.append(Particle(pdg=13, px=-px/2, py=-py/2, pz=-pz/2, E=E_mu, charge=-1))
        events.append(ev)
    return events


def generate_detector_noise(n_events: int) -> List[EventGenome]:
    """Generate corrupted detector noise with violated conservation laws."""
    events = []
    for _ in range(n_events):
        n_particles = np.random.poisson(8) + 2
        particles = []
        # Deliberately violate charge conservation (total charge ±5 or worse)
        target_charge = np.random.choice([-5, -4, 4, 5])
        current_charge = 0
        for i in range(n_particles):
            # Non-physical momenta: no energy-momentum relation
            px = np.random.normal(0, 150)
            py = np.random.normal(0, 150)
            pz = np.random.normal(0, 150)
            # Energy completely uncorrelated with momentum (violates E²=p²+m²)
            E = np.random.exponential(20.0)
            if E < 0:
                E = -E  # negative energy for extra corruption
            # Force charge toward target
            if current_charge < target_charge and i < n_particles - 1:
                charge = np.random.choice([1, 2])
            elif current_charge > target_charge and i < n_particles - 1:
                charge = np.random.choice([-1, -2])
            else:
                charge = target_charge - current_charge
            current_charge += charge
            particles.append(Particle(
                pdg=np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
                px=px, py=py, pz=pz, E=E, charge=charge
            ))
        # Extreme missing energy inconsistent with momentum sum
        total_px = sum(p.px for p in particles)
        total_py = sum(p.py for p in particles)
        missing_et_x = -total_px + np.random.normal(0, 300)
        missing_et_y = -total_py + np.random.normal(0, 300)
        events.append(EventGenome(
            particles=particles,
            missing_et_x=missing_et_x,
            missing_et_y=missing_et_y,
            population='noise',
            has_signal=False
        ))
    return events


# ═══════════════════════════════════════════════════════════════════════════
# Conservation-law checks (L_phys)
# ═══════════════════════════════════════════════════════════════════════════

def check_conservation(event: EventGenome) -> Dict[str, float]:
    """Check physical conservation laws. Returns scores in [0, 1]."""
    parts = event.particles

    # Energy-momentum conservation residual
    total_px = sum(p.px for p in parts)
    total_py = sum(p.py for p in parts)
    total_pz = sum(p.pz for p in parts)
    total_E = sum(p.E for p in parts)
    total_charge = sum(p.charge for p in parts)

    # Missing ET magnitude
    met = np.sqrt(event.missing_et_x**2 + event.missing_et_y**2)
    scalar_sum_pt = sum(np.sqrt(p.px**2 + p.py**2) for p in parts)

    # Momentum conservation score: 1.0 if balanced, 0.0 if huge imbalance
    p_residual = np.sqrt(total_px**2 + total_py**2 + total_pz**2)
    p_score = max(0.0, 1.0 - p_residual / max(1.0, scalar_sum_pt * 0.05))

    # Charge conservation score: strict penalty for any non-zero total charge
    charge_score = max(0.0, 1.0 - abs(total_charge) / 2.0)

    # Energy-momentum consistency: E² ≈ p² + m² for each particle
    em_scores = []
    for p in parts:
        p2 = p.px**2 + p.py**2 + p.pz**2
        if p.E > 0:
            # Expected E for massless particle
            expected_E = np.sqrt(p2)
            ratio = abs(p.E - expected_E) / max(expected_E, 1.0)
            em_scores.append(max(0.0, 1.0 - ratio))
        else:
            em_scores.append(0.0)
    em_score = np.mean(em_scores) if em_scores else 0.0

    # Missing ET plausibility
    met_score = max(0.0, 1.0 - met / max(1.0, scalar_sum_pt * 0.2))

    # Overall: geometric mean for stricter combined score
    overall = (p_score * charge_score * em_score * met_score) ** 0.25

    return {
        'momentum': p_score,
        'charge': charge_score,
        'energy_momentum': em_score,
        'missing_et': met_score,
        'overall': overall,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Event → 18-bit genome encoding
# ═══════════════════════════════════════════════════════════════════════════

def encode_18bit(mu: int, rho: int, c: int, m: int, ne: int, sigma: int) -> int:
    """Pack 6 dimensions × 3 bits into 18-bit address."""
    return (
        (mu & 7) * 32768 +
        (rho & 7) * 4096 +
        (c & 7) * 512 +
        (m & 7) * 64 +
        (ne & 7) * 8 +
        (sigma & 7)
    )


def event_to_genome(event: EventGenome) -> int:
    """Map HEP event features into 18-bit genome address.

    Dimensions (matching RGFlow shader):
      mu    = conservation-law violation rate (inverse of L_phys)
      rho   = reconstruction quality / verification pressure
      c     = particle multiplicity (connectance proxy)
      m     = event topology modularity
      ne    = effective statistics / luminosity proxy
      sigma = signal significance / selection advantage
    """
    parts = event.particles
    n = len(parts)

    # Conservation law check
    conservation = check_conservation(event)
    l_phys = conservation['overall']

    # mu: violation rate = 1 - L_phys, quantized to 0..7
    mu_bin = min(7, int((1.0 - l_phys) * 8.0))

    # rho: reconstruction quality. High-quality events have tight kinematics.
    pt_spread = np.std([np.sqrt(p.px**2 + p.py**2) for p in parts]) if n > 1 else 0
    rho_bin = min(7, int(max(0, 1.0 - pt_spread / 100.0) * 8.0))

    # c: connectance = particle multiplicity density
    c_bin = min(7, n // 2)

    # m: modularity = how clustered are particles in phi space
    if n >= 2:
        phis = np.arctan2([p.py for p in parts], [p.px for p in parts])
        # Simple clustering: count particle pairs within π/4
        pairs_close = 0
        for i in range(n):
            for j in range(i + 1, n):
                dphi = abs(phis[i] - phis[j])
                dphi = min(dphi, 2 * np.pi - dphi)
                if dphi < np.pi / 4:
                    pairs_close += 1
        max_pairs = n * (n - 1) // 2
        modularity = pairs_close / max_pairs if max_pairs > 0 else 0.0
    else:
        modularity = 0.0
    m_bin = min(7, int(modularity * 8.0))

    # ne: effective observer mass (statistics proxy)
    ne_bin = min(7, int(np.log1p(n * 10) / np.log1p(120) * 8.0))

    # sigma: signal significance proxy
    # For resonance events, compute dimuon invariant mass significance
    sigma_bin = 0
    if event.population == 'resonance' and event.has_signal:
        # Find dimuon pair
        muons = [p for p in parts if p.pdg == 13]
        if len(muons) >= 2:
            m1, m2 = muons[-2], muons[-1]
            m_inv = np.sqrt(
                (m1.E + m2.E)**2 -
                (m1.px + m2.px)**2 -
                (m1.py + m2.py)**2 -
                (m1.pz + m2.pz)**2
            )
            # Significance = how close to resonance peak, scaled
            significance = max(0, 5.0 - abs(m_inv - RESONANCE_MASS) / RESONANCE_WIDTH)
            sigma_bin = min(7, int(significance))
    else:
        # Background: low significance
        sigma_bin = min(7, int(np.random.exponential(1.0)))

    return encode_18bit(mu_bin, rho_bin, c_bin, m_bin, ne_bin, sigma_bin)


# ═══════════════════════════════════════════════════════════════════════════
# RGFlow LUT interface
# ═══════════════════════════════════════════════════════════════════════════

def load_rgflow_lut(path: Path) -> np.ndarray:
    """Load precomputed RGFlow adaptation surface as N×6 uint32 array."""
    raw = np.fromfile(path, dtype=np.uint32)
    return raw.reshape(-1, 6)


def lookup_entry(lut: np.ndarray, addr: int) -> Dict:
    """Unpack a single LUT entry."""
    row = lut[addr]
    flags = int(row[0])
    return {
        'lawful_now': bool(flags & 1),
        'lawful_flow': bool(flags & 2),
        'lawful_attractor': bool(flags & 4),
        'noise_flow': bool(flags & 8),
        'sabotage_flow': bool(flags & 16),
        'cost': int(row[1]),
        'margin': int(row[2]),
        'rg_depth': int(row[3]),
        'attractor_id': int(row[4]),
        'failure_mask': f"0x{int(row[5]):04X}",
    }


# ═══════════════════════════════════════════════════════════════════════════
# Physics fitness
# ═══════════════════════════════════════════════════════════════════════════

def compute_fitness(event: EventGenome, lut_entry: Dict) -> float:
    """Compute the HEP physics fitness:

      F(g) = w₁·L_phys(g) + w₂·M_RG(g) + w₃·A(g) − w₄·R_SM(g) − w₅·N_det(g)
    """
    conservation = check_conservation(event)
    l_phys = conservation['overall']

    # RGFlow stability margin, normalized 0-1
    m_rg = min(1.0, lut_entry['margin'] / 65536.0)

    # Attractor specificity
    a = 1.0 if lut_entry['lawful_attractor'] else 0.0

    # SM residual: background-like events get penalized
    # Resonance with signal gets lower penalty
    if event.population == 'SM':
        r_sm = 0.5
    elif event.population == 'resonance' and event.has_signal:
        r_sm = 0.05
    elif event.population == 'resonance':
        r_sm = 0.4
    else:
        r_sm = 0.0

    # Noise likelihood
    if event.population == 'noise':
        n_det = 1.0
    elif lut_entry['sabotage_flow']:
        n_det = 0.7
    elif not lut_entry['lawful_now'] and lut_entry['lawful_flow']:
        # Healed by RGFlow but locally suspicious
        n_det = 0.2
    else:
        n_det = 0.0

    fitness = (
        W_PHYS * l_phys +
        W_RG * m_rg +
        W_ATTRACTOR * a -
        W_SM * r_sm -
        W_NOISE * n_det
    )
    return fitness


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark runner
# ═══════════════════════════════════════════════════════════════════════════

def run_benchmark():
    print("=" * 60)
    print("High-Energy Physics Event Genome Benchmark")
    print("=" * 60)

    if not RGFLOW_BIN.exists():
        print(f"[ERROR] RGFlow LUT not found at {RGFLOW_BIN}", file=sys.stderr)
        print("Run: python3 5-Applications/scripts/rgflow_gpu_pipeline.py", file=sys.stderr)
        sys.exit(1)

    print("[INFO] Loading RGFlow adaptation surface...")
    lut = load_rgflow_lut(RGFLOW_BIN)
    print(f"[INFO] LUT loaded: {lut.shape[0]} entries")

    print(f"\n[INFO] Generating {N_SM} SM background events...")
    sm_events = generate_sm_background(N_SM)

    print(f"[INFO] Generating {N_RESONANCE} planted-resonance events...")
    resonance_events = generate_planted_resonance(N_RESONANCE)

    print(f"[INFO] Generating {N_NOISE} detector-noise events...")
    noise_events = generate_detector_noise(N_NOISE)

    all_events = sm_events + resonance_events + noise_events
    print(f"[INFO] Total events: {len(all_events)}")

    # Evaluate each event
    print("\n[INFO] Encoding events and evaluating against RGFlow surface...")
    results = []
    for i, ev in enumerate(all_events):
        addr = event_to_genome(ev)
        entry = lookup_entry(lut, addr)
        fitness = compute_fitness(ev, entry)
        results.append({
            'index': i,
            'population': ev.population,
            'has_signal': ev.has_signal,
            'address': addr,
            'fitness': round(fitness, 4),
            **entry,
            'conservation_score': round(check_conservation(ev)['overall'], 4),
        })

    # Classification statistics
    stats = {}
    for pop in ['SM', 'resonance', 'noise']:
        subset = [r for r in results if r['population'] == pop]
        stats[pop] = {
            'count': len(subset),
            'lawful_now_fraction': sum(1 for r in subset if r['lawful_now']) / len(subset),
            'lawful_flow_fraction': sum(1 for r in subset if r['lawful_flow']) / len(subset),
            'lawful_attractor_fraction': sum(1 for r in subset if r['lawful_attractor']) / len(subset),
            'sabotage_fraction': sum(1 for r in subset if r['sabotage_flow']) / len(subset),
            'mean_fitness': np.mean([r['fitness'] for r in subset]),
            'mean_margin': np.mean([r['margin'] for r in subset]),
            'mean_cost': np.mean([r['cost'] for r in subset]),
        }
        # Signal-specific stats for resonance
        if pop == 'resonance':
            signal = [r for r in subset if r['has_signal']]
            bg = [r for r in subset if not r['has_signal']]
            stats[pop]['signal_count'] = len(signal)
            stats[pop]['signal_mean_fitness'] = np.mean([r['fitness'] for r in signal]) if signal else 0
            stats[pop]['bg_mean_fitness'] = np.mean([r['fitness'] for r in bg]) if bg else 0
            stats[pop]['signal_lawful_attractor'] = sum(1 for r in signal if r['lawful_attractor']) / len(signal) if signal else 0
            stats[pop]['bg_lawful_attractor'] = sum(1 for r in bg if r['lawful_attractor']) / len(bg) if bg else 0

    # Print report
    print("\n" + "=" * 60)
    print("Benchmark Results")
    print("=" * 60)
    for pop, s in stats.items():
        print(f"\n--- {pop.upper()} ---")
        for k, v in s.items():
            if isinstance(v, float):
                print(f"  {k:30s}: {v:.4f}")
            else:
                print(f"  {k:30s}: {v}")

    # Save JSON
    out_dir = Path("5-Applications/out/hep_benchmark")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    with open(out_path, "w") as f:
        json.dump({
            'meta': {
                'n_sm': N_SM,
                'n_resonance': N_RESONANCE,
                'n_noise': N_NOISE,
                'resonance_mass': RESONANCE_MASS,
                'resonance_width': RESONANCE_WIDTH,
                'signal_fraction': SIGNAL_FRACTION,
                'weights': {
                    'phys': W_PHYS,
                    'rg': W_RG,
                    'attractor': W_ATTRACTOR,
                    'sm': W_SM,
                    'noise': W_NOISE,
                },
            },
            'population_statistics': stats,
            'sample_events': results[:5] + [r for r in results if r['population'] == 'resonance' and r['has_signal']][:5],
        }, f, indent=2)
    print(f"\n[OK] Results saved to {out_path}")

    # Invariant mass spectrum for resonance events (dimuon pairs)
    print("\n[INFO] Computing dimuon invariant-mass spectrum...")
    masses = {'SM': [], 'resonance_signal': [], 'resonance_bg': [], 'noise': []}
    for ev, res in zip(all_events, results):
        muons = [p for p in ev.particles if p.pdg == 13]
        if len(muons) >= 2:
            m1, m2 = muons[-2], muons[-1]
            m_inv = np.sqrt(
                max(0.0, (m1.E + m2.E)**2 -
                (m1.px + m2.px)**2 -
                (m1.py + m2.py)**2 -
                (m1.pz + m2.pz)**2)
            )
        else:
            m_inv = 0.0

        if ev.population == 'SM':
            masses['SM'].append(m_inv)
        elif ev.population == 'resonance':
            if ev.has_signal:
                masses['resonance_signal'].append(m_inv)
            else:
                masses['resonance_bg'].append(m_inv)
        else:
            masses['noise'].append(m_inv)

    # Save mass spectrum
    mass_path = out_dir / "mass_spectrum.json"
    with open(mass_path, "w") as f:
        json.dump({
            'SM': [round(m, 2) for m in masses['SM'][:200]],
            'resonance_signal': [round(m, 2) for m in masses['resonance_signal']],
            'resonance_bg': [round(m, 2) for m in masses['resonance_bg'][:200]],
            'noise': [round(m, 2) for m in masses['noise'][:200]],
        }, f, indent=2)
    print(f"[OK] Mass spectrum saved to {mass_path}")

    # Signal separation summary
    if masses['resonance_signal']:
        sig_masses = np.array(masses['resonance_signal'])
        in_peak = np.sum((sig_masses > RESONANCE_MASS - 3 * RESONANCE_WIDTH) &
                         (sig_masses < RESONANCE_MASS + 3 * RESONANCE_WIDTH))
        print(f"\n  Signal events in 750±15 GeV peak: {in_peak} / {len(sig_masses)} ({100*in_peak/len(sig_masses):.1f}%)")

    print("\n[OK] HEP benchmark complete.")


if __name__ == "__main__":
    run_benchmark()
