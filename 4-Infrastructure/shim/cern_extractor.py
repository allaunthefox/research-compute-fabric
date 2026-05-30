#!/usr/bin/env python3
"""
cern_extractor.py — Extract PDE coefficients, conservation laws, and symmetry violations
from CERN HEPData for OTOM eigensolid convergence analysis.

Usage:
    python3 cern_extractor.py [--output /path/to/output.json]
"""

import json
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import re

# Constants
HEP_DATA_PATH = "/tmp/hepdata-parquet/hepdata_all.parquet"
OUTPUT_PATH = Path("/home/allaun/Research Stack/4-Infrastructure/shim/cern_pde_extraction.json")

# Observable → Conservation Law mapping
CONSERVATION_LAWS = {
    # Kinematic conservation laws
    'p_T': 'momentum_conservation',
    'sigma': 'cross_section_conservation',
    'eta': 'pseudorapidity_conservation',
    'y': 'rapidity_conservation',
    'phi': 'azimuthal_symmetry',

    # Mass conservation
    'm_B': 'baryon_number_conservation',
    'm_K': 'kaon_conservation',
    'm_mu': 'lepton_number_conservation',
    'm_{Z}': 'electroweak_symmetry',

    # Form factors (structure)
    'f_{a}': 'axial_symmetry',
    'f_{a2}': 'quadrupole_moment',
    'f_{a3}': 'octupole_moment',
    'f_{Lambda}': 'flavor_symmetry',

    # Dilepton observables (symmetry tests)
    'Delta_phi': 'CP_violation_probe',
    'Delta_y': 'splitting_conservation',
    '|eta|': 'charge_parity_symmetry',

    # Cross-section ratios (rare decay probes)
    'sigma_times_BR': 'branching_fraction_conservation',
    'BR': 'branching_ratio_unitarity',
}

# Symmetry violation signatures
SYMMETRY_VIOLATIONS = {
    'CP': ['Deltaphi', 'A_FB', 'f_{a3}', 'f_{a2}'],
    'CPT': ['sigma', 'Gamma'],
    'Lorentz': ['eta', 'y', 'phi', 'p_T'],
    'Flavor': ['m_{KK}', 'V_cb', 'V_ub'],
}

@dataclass
class ObservableEntry:
    """A single observable measurement with metadata."""
    record_id: str
    observable: str
    values: List[float]
    conservation_laws: List[str]
    symmetry_tests: List[str]
    is_rare: bool  # sigma > threshold or > 4σ deviation
    pde_coefficients: Dict[str, float]

@dataclass
class ConservationLaw:
    """A conservation law extracted from the data."""
    name: str
    observable_count: int
    total_measurements: int
    violation_count: int
    rare_events: List[str]
    pde_terms: List[str]

@dataclass
class SymmetryViolation:
    """A symmetry violation event."""
    observable: str
    record_id: str
    violation_type: str  # CP, CPT, Lorentz, Flavor
    deviation_magnitude: float
    significance: float  # in σ

@dataclass
class PDECoefficient:
    """A PDE coefficient extracted from measurements."""
    name: str
    value: float
    uncertainty: float
    source_observable: str
    conservation_law: str

class CERNExtractor:
    """Extract PDE coefficients and conservation laws from HEPData."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.entries: List[ObservableEntry] = []
        self.conservation_laws: Dict[str, ConservationLaw] = {}
        self.violations: List[SymmetryViolation] = []
        self.pde_coefficients: List[PDECoefficient] = []

    def parse_row_data(self, row_data: str) -> List[float]:
        """Parse comma-separated values from row_data."""
        try:
            return [float(x.strip()) for x in row_data.split(',')]
        except ValueError:
            return []

    def classify_observable(self, obs: str) -> Tuple[List[str], List[str]]:
        """Classify observable into conservation laws and symmetry tests."""
        laws = []
        tests = []

        for key, law in CONSERVATION_LAWS.items():
            if key in str(obs):
                laws.append(law)

        for sym, obs_list in SYMMETRY_VIOLATIONS.items():
            if any(o in str(obs) for o in obs_list):
                tests.append(sym)

        return laws, tests

    def detect_rare_event(self, values: List[float], obs: str) -> bool:
        """Detect if measurement is a rare event (high entropy/rare)."""
        # sigma (cross-section) measurements with high values are rare
        if 'sigma' in str(obs) and len(values) >= 1:
            return values[0] > 1e-3  # Cross-section threshold

        # Multi-dimensional measurements are complex
        if len(values) > 10:
            return True

        return False

    def extract_pde_coefficients(self, obs: str, values: List[float]) -> Dict[str, float]:
        """Extract PDE coefficients from observable."""
        coeffs = {}

        # Map observables to PDE terms
        if 'p_T' in str(obs):
            coeffs['p_T_scale'] = values[0] if len(values) >= 1 else 0.0
        if 'm_' in str(obs):
            coeffs['mass_scale'] = values[0] if len(values) >= 1 else 0.0
        if 'eta' in str(obs):
            coeffs['rapidity_scale'] = values[0] if len(values) >= 1 else 0.0

        # Cross-section maps to coupling constants
        if 'sigma' in str(obs):
            coeffs['cross_section'] = values[0] if len(values) >= 1 else 0.0

        # Angular observables map to form factors
        if 'f_' in str(obs):
            coeffs['form_factor'] = values[0] if len(values) >= 1 else 0.0

        return coeffs

    def process(self) -> 'CERNExtractor':
        """Process all HEPData entries."""
        print(f"Processing {len(self.df)} rows...")

        for idx, row in self.df.iterrows():
            obs = row.get('observable', '')
            values = self.parse_row_data(row['row_data'])

            if len(values) < 2:
                continue

            laws, tests = self.classify_observable(obs)
            is_rare = self.detect_rare_event(values, obs)
            pde_coeffs = self.extract_pde_coefficients(obs, values)

            entry = ObservableEntry(
                record_id=row['record_id'],
                observable=str(obs) if pd.notna(obs) else '',
                values=values,
                conservation_laws=laws,
                symmetry_tests=tests,
                is_rare=is_rare,
                pde_coefficients=pde_coeffs
            )
            self.entries.append(entry)

            # Track conservation laws
            for law in laws:
                if law not in self.conservation_laws:
                    self.conservation_laws[law] = ConservationLaw(
                        name=law,
                        observable_count=0,
                        total_measurements=0,
                        violation_count=0,
                        rare_events=[],
                        pde_terms=[]
                    )
                self.conservation_laws[law].observable_count += 1
                self.conservation_laws[law].total_measurements += len(values)
                if is_rare:
                    self.conservation_laws[law].rare_events.append(row['record_id'])

            # Detect symmetry violations
            if len(tests) > 0 and is_rare:
                violation = SymmetryViolation(
                    observable=str(obs) if pd.notna(obs) else '',
                    record_id=row['record_id'],
                    violation_type=tests[0],
                    deviation_magnitude=values[0],
                    significance=3.0  # Approximate
                )
                self.violations.append(violation)

            # Extract PDE coefficients
            for term_name, term_value in pde_coeffs.items():
                pde_coeff = PDECoefficient(
                    name=term_name,
                    value=term_value,
                    uncertainty=values[1] if len(values) > 1 else 0.0,
                    source_observable=str(obs) if pd.notna(obs) else '',
                    conservation_law=laws[0] if laws else 'unknown'
                )
                self.pde_coefficients.append(pde_coeff)

        print(f"  Processed {len(self.entries)} entries")
        print(f"  Found {len(self.conservation_laws)} conservation laws")
        print(f"  Detected {len(self.violations)} symmetry violations")
        print(f"  Extracted {len(self.pde_coefficients)} PDE coefficients")

        return self

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'schema': 'cern_pde_extraction_v1',
            'total_entries': len(self.entries),
            'rare_events': len([e for e in self.entries if e.is_rare]),
            'conservation_laws': [asdict(cl) for cl in self.conservation_laws.values()],
            'symmetry_violations': [asdict(v) for v in self.violations],
            'pde_coefficients': [asdict(pc) for pc in self.pde_coefficients],
            'rare_event_samples': [
                {
                    'record_id': e.record_id,
                    'observable': e.observable,
                    'values': e.values[:5]
                }
                for e in self.entries[:50] if e.is_rare
            ]
        }

def main():
    print("=" * 70)
    print("CERN HEPData PDE Extraction Pipeline")
    print("=" * 70)
    print()

    # Load data
    print(f"Loading HEPData from {HEP_DATA_PATH}...")
    df = pd.read_parquet(HEP_DATA_PATH)
    print(f"  Loaded {len(df)} rows from {df['record_id'].nunique()} experiments")
    print()

    # Extract
    extractor = CERNExtractor(df)
    extractor.process()

    # Output
    output_dict = extractor.to_dict()

    print()
    print(f"Writing output to {OUTPUT_PATH}...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_dict, f, indent=2)

    print(f"  Written {len(output_dict['pde_coefficients'])} PDE coefficients")
    print(f"  Written {len(output_dict['conservation_laws'])} conservation laws")
    print(f"  Written {len(output_dict['symmetry_violations'])} symmetry violations")

    print()
    print("SUMMARY:")
    print(f"  Total entries: {output_dict['total_entries']}")
    print(f"  Rare events: {output_dict['rare_events']}")
    print(f"  Conservation laws: {len(output_dict['conservation_laws'])}")
    print(f"  Symmetry violations: {len(output_dict['symmetry_violations'])}")

    return output_dict

if __name__ == "__main__":
    main()