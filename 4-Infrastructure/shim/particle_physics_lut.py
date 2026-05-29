"""Particle Physics LUT — Q16_16 lookup tables from 50 years of PDG data.

The LHC trigger system classifies billions of events/second using hardware LUTs.
The Particle Data Group (PDG) maintains precision measurements of every known
particle property. This module encodes the most useful tables as Q16_16 values
suitable for FPGA BRAM storage.

Key insight: particle physics has been doing "computation via lookup tables"
since the 1970s. The PDG tables ARE a LUT for the Standard Model.

Tables encoded:
1. Particle masses (Q16_16 in MeV)
2. Decay widths (Q16_16 in GeV)
3. Cross-sections (Q16_16 in pb)
4. Trigger thresholds (Q16_16 in GeV)
5. Calorimeter calibration constants (Q16_16)

All values are deterministic Q16_16 integers — no floats in compute paths.
"""

import struct
from pathlib import Path

# ── Q16_16 Constants ──────────────────────────────────────────────────

Q16_SCALE = 65536
Q16_MAX = 2147483647
Q16_MIN = -2147483648


def _q16(value: float) -> int:
    """Convert float to Q16_16 integer with clamping."""
    raw = int(value * Q16_SCALE)
    return max(Q16_MIN, min(Q16_MAX, raw))


def _q16_to_float(q: int) -> float:
    """Convert Q16_16 integer to float."""
    return q / Q16_SCALE


# ── Particle Mass Table (PDG 2024) ───────────────────────────────────
# Values in MeV, encoded as Q16_16 (so 938.272 → 938.272 * 65536)
# Source: Particle Data Group, https://pdg.lbl.gov

PARTICLE_MASSES_MEV = {
    # Leptons
    'electron':       0.51099895,     # ± 0.00000000015
    'muon':           105.6583755,    # ± 0.0000023
    'tau':            1776.86,        # ± 0.12

    # Light quarks (MSbar masses)
    'up':             2.16,           # ± 0.26 (at 2 GeV)
    'down':           4.67,           # ± 0.29 (at 2 GeV)
    'strange':        93.4,           # ± 3.4 (at 2 GeV)

    # Heavy quarks
    'charm':          1270,           # ± 20 (MSbar)
    'bottom':         4180,           # ± 30 (MSbar)
    'top':            172690,         # ± 300 (pole mass)

    # Gauge bosons
    'photon':         0,              # massless
    'W':              80379,          # ± 12
    'Z':              91187.6,        # ± 2.1
    'gluon':          0,              # massless (confined)

    # Higgs
    'higgs':          125250,         # ± 110

    # Light mesons
    'pion_charged':   139.57039,      # ± 0.00018
    'pion_neutral':   134.9768,       # ± 0.0005
    'kaon_charged':   493.677,        # ± 0.016
    'kaon_neutral':   497.611,        # ± 0.013
    'eta':            547.862,        # ± 0.017
    'eta_prime':      957.78,         # ± 0.06

    # Light baryons
    'proton':         938.27208816,   # ± 0.00000029
    'neutron':        939.56542052,   # ± 0.00000054
    'lambda':         1115.683,       # ± 0.006
    'sigma_plus':     1189.37,        # ± 0.07
    'sigma_zero':     1192.642,       # ± 0.024
    'sigma_minus':    1197.449,       # ± 0.030
    'xi_zero':        1314.86,        # ± 0.20
    'xi_minus':       1321.71,        # ± 0.07
    'omega_minus':    1672.45,        # ± 0.29

    # Charmonium
    'J_psi':          3096.900,       # ± 0.006
    'psi_2S':         3686.097,       # ± 0.010

    # Bottomonium
    'upsilon_1S':     9460.30,        # ± 0.26
    'upsilon_2S':     10023.26,       # ± 0.31
    'upsilon_3S':     10355.2,        # ± 0.5
}

# Encode as Q16_16 integers
PARTICLE_MASSES_Q16 = {
    name: _q16(mass) for name, mass in PARTICLE_MASSES_MEV.items()
}

# ── Decay Width Table (PDG 2024) ─────────────────────────────────────
# Values in GeV, encoded as Q16_16

DECAY_WIDTHS_GEV = {
    'W':              2.085,          # ± 0.042
    'Z':              2.4952,         # ± 0.0023
    'higgs':          0.00407,        # ± 0.00010 (SM prediction)
    'top':            1.42,           # ± 0.51 (approximate)
    'J_psi':          0.0000929,      # ± 0.0000017 (keV → GeV: 92.9 keV)
    'upsilon_1S':     0.00005402,     # ± 0.00000125
    'tau':            2.267e-12,      # lifetime → width (very small)
    'muon':           2.996e-19,      # lifetime → width
}

DECAY_WIDTHS_Q16 = {
    name: _q16(width) for name, width in DECAY_WIDTHS_GEV.items()
}

# ── Cross-Section Table (representative, in pb) ──────────────────────
# Q16_16 encoded cross-sections at various energies

CROSS_SECTIONS_PB = {
    # pp collisions at √s = 13 TeV (LHC Run 2)
    'ttbar_13TeV':        830,        # ± 40 (top pair production)
    'W_incl_13TeV':       20500,      # ± 500 (W boson inclusive)
    'Z_incl_13TeV':       1870,       # ± 50 (Z boson inclusive)
    'H_gg_13TeV':         48.6,       # ± 2.0 (Higgs via gluon fusion)
    'H_vbf_13TeV':        3.78,       # ± 0.08 (Higgs via VBF)
    'jets_incl_13TeV':    80000000,   # 80 Mb (inclusive jets, pT > 30 GeV)
    'dijet_13TeV':        10000000,   # 10 Mb (dijet, pT > 50 GeV)

    # ee collisions at √s = 91.2 GeV (LEP Z pole)
    'Z_ee':               2980,       # ± 30 (Z → ee)
    'Z_mumu':             2980,       # ± 30 (Z → μμ)
    'Z_tautau':           2980,       # ± 30 (Z → ττ)
    'Z_had':              1720,       # ± 20 (Z → hadrons)
}

CROSS_SECTIONS_Q16 = {
    name: _q16(xs) for name, xs in CROSS_SECTIONS_PB.items()
}

# ── Trigger Thresholds (LHC, in GeV) ─────────────────────────────────

TRIGGER_THRESHOLDS_GEV = {
    'single_electron':    27,         # HLT_Ele27_WPTight_Gsf
    'single_muon':        24,         # HLT_IsoMu24
    'single_photon':      150,        # HLT_Photon150
    'jet_450':            450,        # HLT_PFJet450
    'met_120':            120,        # PFMET120
    'ht_500':             500,        # HLT_PFHT500
    'dilepton_mll':       12,         # M(ee/μμ) > 12 GeV
    'bjet_csv':           0.8484,     # DeepJet medium WP
}

TRIGGER_THRESHOLDS_Q16 = {
    name: _q16(thresh) for name, thresh in TRIGGER_THRESHOLDS_GEV.items()
}

# ── Calorimeter Calibration Constants ────────────────────────────────
# Energy scale factors for ECAL/HCAL (dimensionless, Q16_16)

CALIBRATION_CONSTANTS = {
    'ecal_eb':            1.000,      # ECAL barrel
    'ecal_ee':            1.005,      # ECAL endcap (slightly higher)
    'hcal_hb':            1.000,      # HCAL barrel
    'hcal_he':            1.010,      # HCAL endcap
    'hcal_hf':            1.050,      # HF (forward, larger corrections)
    'muon_scale':         1.000,      # Muon momentum scale
    'electron_scale':     1.002,      # Electron energy scale
    'photon_scale':       1.003,      # Photon energy scale
}

CALIBRATION_Q16 = {
    name: _q16(cal) for name, cal in CALIBRATION_CONSTANTS.items()
}


# ── BRAM Layout for FPGA ─────────────────────────────────────────────

def generate_bram_layout() -> dict:
    """Generate BRAM layout for particle physics LUTs.

    Returns dict mapping BRAM bank to (name, entries, data).
    Each bank is 256 entries × 32-bit Q16_16.
    """
    banks = {}

    # Bank 0: Particle masses (up to 256 entries)
    mass_entries = list(PARTICLE_MASSES_Q16.items())[:256]
    bank0 = [0] * 256
    for i, (name, q16val) in enumerate(mass_entries):
        bank0[i] = q16val
    banks[0] = ('particle_masses', len(mass_entries), bank0)

    # Bank 1: Decay widths
    width_entries = list(DECAY_WIDTHS_Q16.items())[:256]
    bank1 = [0] * 256
    for i, (name, q16val) in enumerate(width_entries):
        bank1[i] = q16val
    banks[1] = ('decay_widths', len(width_entries), bank1)

    # Bank 2: Cross-sections
    xs_entries = list(CROSS_SECTIONS_Q16.items())[:256]
    bank2 = [0] * 256
    for i, (name, q16val) in enumerate(xs_entries):
        bank2[i] = q16val
    banks[2] = ('cross_sections', len(xs_entries), bank2)

    # Bank 3: Trigger thresholds + calibration
    trigger_entries = list(TRIGGER_THRESHOLDS_Q16.items())
    cal_entries = list(CALIBRATION_Q16.items())
    bank3 = [0] * 256
    for i, (name, q16val) in enumerate(trigger_entries):
        bank3[i] = q16val
    for i, (name, q16val) in enumerate(cal_entries):
        bank3[len(trigger_entries) + i] = q16val
    banks[3] = ('triggers_calibration', len(trigger_entries) + len(cal_entries), bank3)

    return banks


def export_bram_init(bank_data: list[int], path: Path):
    """Export BRAM initialization data as Verilog initial block."""
    with open(path, 'w') as f:
        f.write('// Auto-generated particle physics LUT\n')
        f.write('// Q16_16 fixed-point, 256 entries × 32-bit\n\n')
        f.write('initial begin\n')
        for i, val in enumerate(bank_data):
            # Format as 32-bit hex
            hexval = val & 0xFFFFFFFF
            f.write(f'  memory[8\'h{i:02X}] = 32\'h{hexval:08X};\n')
        f.write('end\n')


def export_all_bram(output_dir: Path):
    """Export all BRAM initialization files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    banks = generate_bram_layout()

    for bank_id, (name, count, data) in banks.items():
        path = output_dir / f'particle_lut_bank{bank_id}_{name}.v'
        export_bram_init(data, path)
        print(f'Bank {bank_id}: {name} ({count} entries) → {path}')


# ── Cross-Section Lookup (energy-dependent) ───────────────────────────

def interpolate_cross_section(energy_tev: float, process: str) -> int:
    """Interpolate cross-section at given energy. Returns Q16_16.

    Uses log-log interpolation between known energy points.
    For energies outside the table, uses power-law extrapolation.
    """
    # Energy points and corresponding cross-sections (approximate)
    energy_points = {
        'ttbar': [(7, 165), (8, 230), (13, 830), (14, 930)],
        'W':     [(7, 12200), (8, 14700), (13, 20500), (14, 22000)],
        'Z':     [(7, 1200), (8, 1400), (13, 1870), (14, 2000)],
        'H_gg':  [(7, 15.1), (8, 19.3), (13, 48.6), (14, 54.7)],
    }

    if process not in energy_points:
        return _q16(0)

    points = energy_points[process]
    if energy_tev <= points[0][0]:
        return _q16(points[0][1])
    if energy_tev >= points[-1][0]:
        return _q16(points[-1][1])

    # Log-log interpolation
    import math
    for i in range(len(points) - 1):
        e0, xs0 = points[i]
        e1, xs1 = points[i + 1]
        if e0 <= energy_tev <= e1:
            t = (math.log(energy_tev) - math.log(e0)) / (math.log(e1) - math.log(e0))
            xs = xs0 * (xs1 / xs0) ** t
            return _q16(xs)

    return _q16(0)


# ── CLI ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('=== Particle Physics LUT (Q16_16) ===\n')

    print('Particle Masses (MeV):')
    for name, mass in PARTICLE_MASSES_MEV.items():
        q16 = PARTICLE_MASSES_Q16[name]
        print(f'  {name:<20} {mass:>12.3f} MeV  →  Q16: {q16:>12d}  ({_q16_to_float(q16):.3f} MeV)')

    print(f'\nDecay Widths (GeV):')
    for name, width in DECAY_WIDTHS_GEV.items():
        q16 = DECAY_WIDTHS_Q16[name]
        print(f'  {name:<20} {width:>12.6f} GeV  →  Q16: {q16:>12d}')

    print(f'\nCross-Sections at 13 TeV (pb):')
    for name, xs in CROSS_SECTIONS_PB.items():
        q16 = CROSS_SECTIONS_Q16[name]
        print(f'  {name:<20} {xs:>12.1f} pb   →  Q16: {q16:>12d}')

    print(f'\nTrigger Thresholds (GeV):')
    for name, thresh in TRIGGER_THRESHOLDS_GEV.items():
        q16 = TRIGGER_THRESHOLDS_Q16[name]
        print(f'  {name:<20} {thresh:>12.1f} GeV  →  Q16: {q16:>12d}')

    print(f'\nBRAM Layout:')
    banks = generate_bram_layout()
    for bank_id, (name, count, data) in banks.items():
        nonzero = sum(1 for v in data if v != 0)
        print(f'  Bank {bank_id}: {name} ({count} entries, {nonzero} non-zero)')

    # Export
    out_dir = Path('/tmp/particle_lut_bram')
    export_all_bram(out_dir)
    print(f'\nExported to {out_dir}/')
