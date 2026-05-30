#!/usr/bin/env python3
"""
eigensolid_pipeline.py — CERN HEPData → OTOM eigensolid artifacts

1) Extract spectral profiles from measurement rows
2) Generate 8×8 adjacency matrices (PIST format)
3) Emit Lean-compatible stubs (theorems + constants) for proof workflows

Example:
  python3 eigensolid_pipeline.py \
    --input /path/to/cern_pde_extraction.json \
    --hepdata /tmp/hepdata-parquet/hepdata_all.parquet \
    --output-dir ./eigensolid_analysis \
    --lean-output ./CERNEigensolidData.lean
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd


# -----------------------------------------------------------------------------
# Data model
# -----------------------------------------------------------------------------

@dataclass
class SpectralProfile:
    """8-dimensional spectral profile for eigensolid analysis."""
    record_id: Union[str, int]
    observable: str
    eigenvalues: List[float]       # length 8, normalized
    entropy: float
    entropy_convergence: float      # 0..1 derived from entropy
    golden_convergence: float       # 0..1 closeness to golden "targets"
    convergence_level: float        # 0..1 combined metric


@dataclass
class RunSummary:
    schema: str
    hepdata_path: str
    extraction_path: str
    total_records_processed: int
    total_matrices: int
    total_spectral_profiles: int
    avg_convergence: float
    pist_matrices_sample: List[List[List[float]]]
    spectral_profiles_sample: List[Dict[str, Any]]


# -----------------------------------------------------------------------------
# Core pipeline
# -----------------------------------------------------------------------------

class EigensolidPipeline:
    """
    Generate eigensolid analysis from CERN HEPData parquet + an extraction JSON.
    Expected HEPData columns (configurable only by editing code right now):
      record_id
      observable
      row_data
    """

    def __init__(self, df: pd.DataFrame, extraction_data: dict):
        self.df = df
        self.extraction = extraction_data
        self.spectral_profiles: List[SpectralProfile] = []
        self.matrices: List[List[List[float]]] = []
        self.records_processed: int = 0

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _to_float_list(x: Any) -> List[float]:
        """
        Accepts:
          - list/tuple of numbers
          - JSON string like "[1,2,3]"
          - comma-separated string like "1,2,3"
        Returns list[float]. Non-parsable values return [].
        """
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return []

        # Already a list/tuple/np array
        if isinstance(x, (list, tuple, np.ndarray)):
            out = []
            for v in x:
                try:
                    out.append(float(v))
                except Exception:
                    pass
            return out

        # Bytes → decode
        if isinstance(x, (bytes, bytearray)):
            try:
                x = x.decode("utf-8")
            except Exception:
                return []

        # Strings: try JSON first, then CSV-ish
        if isinstance(x, str):
            s = x.strip()
            if not s:
                return []

            # JSON array?
            if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
                try:
                    arr = json.loads(s.replace("(", "[").replace(")", "]"))
                    return EigensolidPipeline._to_float_list(arr)
                except Exception:
                    pass

            # CSV fallback
            parts = [p.strip() for p in s.split(",")]
            out = []
            for p in parts:
                if not p:
                    continue
                try:
                    out.append(float(p))
                except Exception:
                    # ignore bad token
                    pass
            return out

        # Unknown type
        return []

    @staticmethod
    def _normalize_8(values: Sequence[float]) -> List[float]:
        eigens = [0.0] * 8
        for i, v in enumerate(values[:8]):
            eigens[i] = abs(float(v))  # force nonnegative
        norm = float(np.linalg.norm(np.array(eigens, dtype=float)))
        if norm > 0:
            eigens = [e / norm for e in eigens]
        return eigens

    @staticmethod
    def _entropy_from_unit_vector(eigens: Sequence[float]) -> float:
        # probabilities ~ squared components
        probs = [float(e) ** 2 for e in eigens]
        Z = sum(probs)
        if Z <= 0:
            return 0.0
        probs = [p / Z for p in probs]
        # add epsilon for numerical safety
        eps = 1e-12
        return -sum(p * math.log(p + eps) for p in probs)

    @staticmethod
    def _entropy_convergence(entropy: float, entropy_max: float = 2.0) -> float:
        # Scale entropy into 0..1. Clamp.
        if entropy_max <= 0:
            return 0.0
        return max(0.0, min(1.0, entropy / entropy_max))

    @staticmethod
    def _golden_convergence(eigens: Sequence[float]) -> float:
        """
        Compare against normalized golden target vector.
        """
        golden_positions = [0.0, 0.618, 1.0, 1.618, 2.0, 2.618, 3.0, 3.618]
        target = np.array(golden_positions, dtype=float)
        # normalize target to unit vector to match eigens normalization
        tnorm = float(np.linalg.norm(target))
        if tnorm > 0:
            target = target / tnorm

        e = np.array(list(eigens), dtype=float)
        if len(e) != 8:
            return 0.0

        avg_dist = float(np.mean(np.abs(e - target)))
        return max(0.0, min(1.0, 1.0 - avg_dist))

    # -------------------------------------------------------------------------
    # Main transforms
    # -------------------------------------------------------------------------

    def compute_spectral_profile(
        self,
        *,
        record_id: Union[str, int],
        observable: str,
        values: Sequence[float],
        alpha: float = 0.5,
    ) -> SpectralProfile:
        """
        alpha blends entropy vs golden convergence:
          convergence_level = alpha*entropy_convergence + (1-alpha)*golden_convergence
        """
        eigens = self._normalize_8(values)
        entropy = self._entropy_from_unit_vector(eigens)
        ent_conv = self._entropy_convergence(entropy, entropy_max=2.0)
        gold_conv = self._golden_convergence(eigens)
        conv = alpha * ent_conv + (1.0 - alpha) * gold_conv

        return SpectralProfile(
            record_id=record_id,
            observable=observable or "unknown",
            eigenvalues=eigens,
            entropy=entropy,
            entropy_convergence=ent_conv,
            golden_convergence=gold_conv,
            convergence_level=conv,
        )

    @staticmethod
    def build_pist_matrix(observables: Sequence[str]) -> List[List[float]]:
        """
        Deterministic 8×8 adjacency matrix.
        vocab sorted for stability
        strand(token) = vocab_index % 8
        M[strand(t_i)][strand(t_{i+1})] += 1
        """
        obs_clean = [o for o in observables if isinstance(o, str) and o.strip()]
        if not obs_clean:
            return [[0.0] * 8 for _ in range(8)]

        vocab = sorted(set(obs_clean))[:256]
        vocab_to_strand = {v: (i % 8) for i, v in enumerate(vocab)}

        M = [[0.0] * 8 for _ in range(8)]
        for i, tok in enumerate(obs_clean[:-1]):
            row = vocab_to_strand.get(tok, 0)
            col = vocab_to_strand.get(obs_clean[i + 1], 0)
            M[row][col] += 1.0

        return M

    def process(
        self,
        *,
        record_limit: int = 20,
        row_limit_per_record: Optional[int] = None,
        spectral_min_len: int = 4,
        alpha: float = 0.5,
        verbose: bool = True,
    ) -> "EigensolidPipeline":
        if verbose:
            print("Processing CERN data for eigensolid analysis...")

        if "record_id" not in self.df.columns:
            raise ValueError("HEPData dataframe missing required column: record_id")
        if "observable" not in self.df.columns:
            raise ValueError("HEPData dataframe missing required column: observable")
        if "row_data" not in self.df.columns:
            raise ValueError("HEPData dataframe missing required column: row_data")

        record_ids = list(pd.unique(self.df["record_id"]))[:record_limit]

        for rid in record_ids:
            subset = self.df[self.df["record_id"] == rid]
            if row_limit_per_record is not None:
                subset = subset.head(row_limit_per_record)

            observables = subset["observable"].dropna().astype(str).tolist()
            self.matrices.append(self.build_pist_matrix(observables))

            for _, row in subset.iterrows():
                vals = self._to_float_list(row.get("row_data"))
                if len(vals) >= spectral_min_len:
                    prof = self.compute_spectral_profile(
                        record_id=rid,
                        observable=str(row.get("observable") or "unknown"),
                        values=vals,
                        alpha=alpha,
                    )
                    self.spectral_profiles.append(prof)

        self.records_processed = len(record_ids)

        if verbose:
            print(f"  Records processed: {self.records_processed}")
            print(f"  Generated {len(self.matrices)} PIST matrices")
            print(f"  Generated {len(self.spectral_profiles)} spectral profiles")

        return self

    # -------------------------------------------------------------------------
    # Outputs
    # -------------------------------------------------------------------------

    def avg_convergence(self) -> float:
        if not self.spectral_profiles:
            return 0.0
        return float(np.mean([p.convergence_level for p in self.spectral_profiles]))

    def to_summary(self, hepdata_path: str, extraction_path: str) -> RunSummary:
        return RunSummary(
            schema="eigensolid_analysis_v2",
            hepdata_path=hepdata_path,
            extraction_path=extraction_path,
            total_records_processed=self.records_processed,
            total_matrices=len(self.matrices),
            total_spectral_profiles=len(self.spectral_profiles),
            avg_convergence=self.avg_convergence(),
            pist_matrices_sample=self.matrices[:5],
            spectral_profiles_sample=[
                {
                    "record_id": p.record_id,
                    "observable": p.observable,
                    "eigenvalues": p.eigenvalues,
                    "entropy": p.entropy,
                    "entropy_convergence": p.entropy_convergence,
                    "golden_convergence": p.golden_convergence,
                    "convergence_level": p.convergence_level,
                }
                for p in self.spectral_profiles[:10]
            ],
        )

    def generate_lean(self) -> str:
        """
        Emit Lean code (stubs) based on extraction JSON + run summary.
        """
        def lean_ident(s: str) -> str:
            # Conservative identifier sanitization
            out = []
            for ch in s:
                if ch.isalnum() or ch == "_":
                    out.append(ch)
                else:
                    out.append("_")
            ident = "".join(out)
            if not ident or ident[0].isdigit():
                ident = f"c_{ident}"
            return ident

        lines: List[str] = []

        lines.append("-- ========================================================================")
        lines.append("-- CERNEigensolidData.lean — Eigensolid lemmas from CERN particle physics")
        lines.append("-- Generated from HEPData (CERN Open Data)")
        lines.append("-- ========================================================================")
        lines.append("")
        lines.append("import Semantics.Q16_16Numerics")
        lines.append("import Semantics.PIST.Spectral")
        lines.append("")
        lines.append("namespace Semantics.CERNEigensolidData")
        lines.append("")

        # §1 Conservation laws
        lines.append("-- ========================================================================")
        lines.append("-- §1 CONSERVATION LAWS (from CERN HEPData)")
        lines.append("-- ========================================================================")
        lines.append("")

        conservation_laws = self.extraction.get("conservation_laws", []) or []
        for cl in conservation_laws[:5]:
            raw_name = str(cl.get("name", "conservation_law"))
            name = lean_ident(raw_name)
            pretty = raw_name.replace("*", " ")
            obs_ct = cl.get("observable_count", "?")
            meas_ct = cl.get("total_measurements", "?")
            lines.append(f"/-- {pretty} from particle physics experiments.")
            lines.append(f"    Source: {obs_ct} observables, {meas_ct} measurements. -/")
            lines.append(f"theorem {name}_from_cern : Prop := by")
            lines.append("  sorry")
            lines.append("")

        # §2 Symmetry violations
        lines.append("-- ========================================================================")
        lines.append("-- §2 SYMMETRY VIOLATIONS (CP, CPT, Lorentz, Flavor)")
        lines.append("-- ========================================================================")
        lines.append("")

        violations = self.extraction.get("symmetry_violations", []) or []
        for i, v in enumerate(violations[:10]):
            vtype = str(v.get("violation_type", "violation"))
            obs = str(v.get("observable", "observable"))
            dev = v.get("deviation_magnitude", None)
            sig = v.get("significance", None)
            dev_s = f"{dev:.4e}" if isinstance(dev, (int, float)) else "?"
            sig_s = f"{sig:.1f}" if isinstance(sig, (int, float)) else "?"
            lines.append(f"/-- {vtype} violation in {obs}")
            lines.append(f"    Deviation: {dev_s}, Significance: {sig_s}σ -/")
            lines.append(f"theorem symmetry_violation_{i} : Prop := by")
            lines.append("  sorry")
            lines.append("")

        # §3 PDE coefficients
        lines.append("-- ========================================================================")
        lines.append("-- §3 PDE COEFFICIENTS (from experimental data)")
        lines.append("-- ========================================================================")
        lines.append("")

        pde_coeffs = self.extraction.get("pde_coefficients", []) or []
        uniq: Dict[str, dict] = {}
        for pc in pde_coeffs:
            nm = str(pc.get("name", "coeff"))
            if nm not in uniq:
                uniq[nm] = pc

        for i, (nm, pc) in enumerate(list(uniq.items())[:10]):
            src = str(pc.get("source_observable", "source"))
            val = pc.get("value", 0.0)
            unc = pc.get("uncertainty", 0.0)
            try:
                val_f = float(val)
            except Exception:
                val_f = 0.0
            try:
                unc_f = float(unc)
            except Exception:
                unc_f = 0.0
            lines.append(f"/-- PDE coefficient: {src}")
            lines.append(f"    Value: {val_f:.6e} ± {unc_f:.6e} -/")
            lines.append(f"def pde_coefficient_{i} : Q16_16 := Q16_16.ofFloat {val_f}")
            lines.append("")

        # §4 Eigensolid convergence
        lines.append("-- ========================================================================")
        lines.append("-- §4 EIGENSOLID CONVERGENCE (from spectral profiles)")
        lines.append("-- ========================================================================")
        lines.append("")

        if self.spectral_profiles:
            avg = self.avg_convergence()
            lines.append(f"/-- Average eigensolid convergence from CERN data: {avg:.4f}")
            lines.append(f"    Based on {len(self.spectral_profiles)} spectral profiles -/")
            lines.append("theorem eigensolid_convergence_cern : ∀ (s : State8),")
            lines.append("  crossStep (crossStep s) = crossStep s →")
            lines.append("  ∃ (receipt : Receipt), decode receipt = s := by")
            lines.append("  sorry")
            lines.append("")
        else:
            lines.append("-- No spectral profiles were generated in this run.")
            lines.append("")

        lines.append("end Semantics.CERNEigensolidData")

        return "\n".join(lines)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to cern_pde_extraction.json")
    p.add_argument("--hepdata", required=True, help="Path to hepdata_all.parquet")
    p.add_argument("--output-dir", required=True, help="Directory to write analysis JSON")
    p.add_argument("--lean-output", required=True, help="Path to write CERNEigensolidData.lean")
    p.add_argument("--record-limit", type=int, default=20)
    p.add_argument("--row-limit-per-record", type=int, default=0, help="0 means no limit")
    p.add_argument("--spectral-min-len", type=int, default=4)
    p.add_argument("--alpha", type=float, default=0.5, help="Blend entropy vs golden convergence")
    p.add_argument("--quiet", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    extraction_path = Path(args.input).expanduser()
    hepdata_path = Path(args.hepdata).expanduser()
    output_dir = Path(args.output_dir).expanduser()
    lean_output = Path(args.lean_output).expanduser()

    verbose = not args.quiet

    if verbose:
        print("=" * 70)
        print("Eigensolid Pipeline — CERN → OTOM")
        print("=" * 70)

    if not extraction_path.exists():
        raise FileNotFoundError(f"Extraction JSON not found: {extraction_path}")
    if not hepdata_path.exists():
        raise FileNotFoundError(f"HEPData parquet not found: {hepdata_path}")

    if verbose:
        print(f"Loading extraction from {extraction_path}...")

    extraction = json.loads(extraction_path.read_text())

    if verbose:
        print(f"Loading HEPData from {hepdata_path}...")

    df = pd.read_parquet(hepdata_path)

    row_limit = args.row_limit_per_record if args.row_limit_per_record and args.row_limit_per_record > 0 else None

    pipeline = EigensolidPipeline(df, extraction).process(
        record_limit=args.record_limit,
        row_limit_per_record=row_limit,
        spectral_min_len=args.spectral_min_len,
        alpha=args.alpha,
        verbose=verbose,
    )

    # Write analysis JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = pipeline.to_summary(str(hepdata_path), str(extraction_path))
    analysis_path = output_dir / "eigensolid_analysis.json"
    analysis_path.write_text(json.dumps(asdict(summary), indent=2))

    # Write Lean
    lean_output.parent.mkdir(parents=True, exist_ok=True)
    lean_output.write_text(pipeline.generate_lean())

    if verbose:
        print("")
        print("SUMMARY:")
        print(f"  Records processed: {summary.total_records_processed}")
        print(f"  PIST matrices:     {summary.total_matrices}")
        print(f"  Spectral profiles: {summary.total_spectral_profiles}")
        print(f"  Avg convergence:   {summary.avg_convergence:.4f}")
        print("")
        print(f"Wrote analysis JSON: {analysis_path}")
        print(f"Wrote Lean file:     {lean_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())