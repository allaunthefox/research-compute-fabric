#!/usr/bin/env python3
"""
unified_hep_extractor.py — Combine HepData + INSPIRE into unified OTOM format

This creates a comprehensive corpus that combines:
- HepData: particle physics measurements (observables, values, errors)
- INSPIRE: theoretical context (papers, citations, experimental references)

Usage:
    python3 unified_hep_extractor.py --input-dir /tmp/hep_combined --output unified_corpus.json
"""

import argparse
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

import pandas as pd


@dataclass
class UnifiedEntry:
    """A unified HEP entry combining measurement + literature context."""
    source: str  # 'hepdata' or 'inspire'
    record_id: str
    observable: Optional[str]
    values: List[float]
    description: Optional[str]
    authors: List[str]
    experiments: List[str]
    citations: List[str]
    conservation_laws: List[str]
    symmetry_violations: List[str]
    pde_coefficients: Dict[str, float]


CONSERVATION_LAWS = {
    'p_T': 'momentum_conservation',
    'sigma': 'cross_section_conservation',
    'eta': 'pseudorapidity_conservation',
    'y': 'rapidity_conservation',
    'phi': 'azimuthal_symmetry',
    'm_B': 'baryon_number_conservation',
    'm_K': 'kaon_conservation',
    'f_{a}': 'axial_symmetry',
    'Delta': 'symmetry_violation_probe',
}

SYMMETRY_VIOLATIONS = {
    'CP': ['Deltaphi', 'A_FB', 'f_{a3}', 'f_{a2}'],
    'CPT': ['sigma', 'Gamma'],
    'Lorentz': ['eta', 'y', 'phi', 'p_T'],
}


class UnifiedExtractor:
    """Extract unified corpus from multiple HEP providers."""

    def __init__(self, input_dir: Path):
        self.input_dir = input_dir
        self.entries: List[UnifiedEntry] = []
        self.stats = {
            'hepdata_records': 0,
            'inspire_records': 0,
            'conservation_laws_found': set(),
            'symmetry_violations_found': set(),
            'pde_coefficients': {}
        }

    def parse_row_data(self, row_data: str) -> List[float]:
        """Parse comma-separated values."""
        try:
            return [float(x.strip()) for x in str(row_data).split(',')]
        except:
            return []

    def extract_hepdata(self) -> int:
        """Extract from HepData parquet files."""
        hepdata_dir = self.input_dir / "hepdata"
        if not hepdata_dir.exists():
            print(f"  Warning: {hepdata_dir} not found")
            return 0

        parquet_files = list(hepdata_dir.glob("*.parquet"))
        if not parquet_files:
            # Try parent (already in existing location)
            parquet_files = [Path("/tmp/hepdata-parquet/hepdata_all.parquet")]

        count = 0
        for pf in parquet_files:
            if not pf.exists():
                continue
            df = pd.read_parquet(pf)
            for _, row in df.iterrows():
                values = self.parse_row_data(row.get('row_data', ''))
                if len(values) < 2:
                    continue

                obs = str(row.get('observable', ''))
                conservation = []
                violations = []
                pde_coeffs = {}

                for key, law in CONSERVATION_LAWS.items():
                    if key in obs:
                        conservation.append(law)
                        self.stats['conservation_laws_found'].add(law)

                for sym, obs_list in SYMMETRY_VIOLATIONS.items():
                    if any(o in obs for o in obs_list):
                        violations.append(sym)
                        self.stats['symmetry_violations_found'].add(sym)

                if values:
                    pde_coeffs['value'] = values[0]
                    if len(values) > 1:
                        pde_coeffs['uncertainty'] = values[1]
                    self.stats['pde_coefficients'][obs] = pde_coeffs

                entry = UnifiedEntry(
                    source='hepdata',
                    record_id=str(row.get('record_id', '')),
                    observable=obs if obs != 'nan' else None,
                    values=values,
                    description=row.get('description', None),
                    authors=[],
                    experiments=[row.get('record_id', '').split('-')[0]],
                    citations=[],
                    conservation_laws=conservation,
                    symmetry_violations=violations,
                    pde_coefficients=pde_coeffs
                )
                self.entries.append(entry)
                count += 1

        print(f"  Extracted {count} HepData entries")
        self.stats['hepdata_records'] = count
        return count

    def extract_inspire(self) -> int:
        """Extract from INSPIRE literature records."""
        inspire_dir = self.input_dir / "inspire"
        if not inspire_dir.exists():
            print(f"  Warning: {inspire_dir} not found")
            return 0

        parquet_files = list(inspire_dir.glob("*.parquet"))
        count = 0

        for pf in parquet_files:
            df = pd.read_parquet(pf)
            for _, row in df.iterrows():
                metadata = row.get('metadata', {})
                if isinstance(metadata, dict):
                    titles = metadata.get('titles', [])
                    title = ''
                    if len(titles) > 0:
                        t = titles[0]
                        if isinstance(t, dict):
                            title = t.get('title', '')
                        elif isinstance(t, str):
                            title = t

                    authors_data = metadata.get('authors', [])
                    authors = []
                    for a in authors_data[:5]:
                        if isinstance(a, dict):
                            authors.append(a.get('full_name', ''))
                        elif isinstance(a, str):
                            authors.append(a)

                    collaborations = metadata.get('collaborations', [])
                    experiments = []
                    for c in collaborations:
                        if isinstance(c, dict):
                            experiments.append(c.get('value', ''))
                        elif isinstance(c, str):
                            experiments.append(c)

                    abstracts = metadata.get('abstracts', [])
                    abstract = ''
                    if len(abstracts) > 0:
                        a = abstracts[0]
                        if isinstance(a, dict):
                            abstract = a.get('value', '')
                        elif isinstance(a, str):
                            abstract = a

                    arxiv_id = metadata.get('arxiv_id', '')

                    entry = UnifiedEntry(
                        source='inspire',
                        record_id=str(row.get('id', arxiv_id)),
                        observable=None,
                        values=[],
                        description=abstract[:500] if abstract else None,
                        authors=authors,
                        experiments=experiments,
                        citations=[],
                        conservation_laws=[],
                        symmetry_violations=[],
                        pde_coefficients={}
                    )
                    self.entries.append(entry)
                    count += 1

        print(f"  Extracted {count} INSPIRE entries")
        self.stats['inspire_records'] = count
        return count

    def process(self) -> 'UnifiedExtractor':
        """Process all sources."""
        print("Processing HEP data sources...")
        self.extract_hepdata()
        self.extract_inspire()
        return self

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            'schema': 'unified_hep_corpus_v1',
            'total_entries': len(self.entries),
            'hepdata_records': self.stats['hepdata_records'],
            'inspire_records': self.stats['inspire_records'],
            'conservation_laws': list(self.stats['conservation_laws_found']),
            'symmetry_violations': list(self.stats['symmetry_violations_found']),
            'unique_pde_coefficients': len(self.stats['pde_coefficients']),
            'entries': [asdict(e) for e in self.entries[:1000]]  # Cap at 1000 for JSON
        }


def main():
    parser = argparse.ArgumentParser(description="Unified HEP data extractor")
    parser.add_argument("--input-dir", default="/tmp/hep_combined", help="Input directory")
    parser.add_argument("--output", default="/tmp/unified_hep_corpus.json", help="Output JSON")

    args = parser.parse_args()

    print("=" * 70)
    print("UNIFIED HEP DATA EXTRACTOR")
    print("=" * 70)
    print()

    extractor = UnifiedExtractor(Path(args.input_dir))
    extractor.process()

    output_dict = extractor.to_dict()

    with open(args.output, 'w') as f:
        json.dump(output_dict, f, indent=2)

    print()
    print("SUMMARY:")
    print(f"  Total entries: {output_dict['total_entries']}")
    print(f"  HepData records: {output_dict['hepdata_records']}")
    print(f"  INSPIRE records: {output_dict['inspire_records']}")
    print(f"  Conservation laws: {len(output_dict['conservation_laws'])}")
    print(f"  Symmetry violations: {len(output_dict['symmetry_violations'])}")
    print(f"  Unique PDE coefficients: {output_dict['unique_pde_coefficients']}")
    print()
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()