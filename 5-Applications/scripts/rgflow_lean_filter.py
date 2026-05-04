#!/usr/bin/env python3
"""
RGFlow Lean File Filter

Applies the Unified Adaptation Equation with RGFlow to filter Lean files.
Only files that are "lawful" under RGFlow are retained.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from scripts.commoncrawl_waveprobe_ingestion import UnifiedAdaptationEquation, AdaptationState

logging.basicConfig(level=logging.INFO, format='%(levelname)s:RGFlowLeanFilter:%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class LeanCodeAnalysis:
    """Analysis result for a Lean file."""
    filepath: str
    lawful_now: bool
    lawful_under_flow: bool
    reaches_attractor: bool
    flows_to_noise: bool
    flows_to_sabotage: bool
    adaptation_cost: float
    stability_margin: float
    rg_depth: int
    attractor_id: int
    failure_mask: int


class RGFlowLeanFilter:
    """Filter Lean files using RGFlow mechanism."""
    
    def __init__(self, root_path: str = "/home/allaun/Research Stack"):
        self.root_path = Path(root_path)
        self.adaptation_equation = UnifiedAdaptationEquation()
        self.analyses: List[LeanCodeAnalysis] = []
        
        # Adjust constants for Lean files (more permissive than web content)
        self.adaptation_equation.DRAKE_BUDGET_D = 0.1  # Increased from 0.003
        self.adaptation_equation.DRIFT_BARRIER_B = 0.01  # Increased from 0.001
        self.adaptation_equation.LAMBDA = 0.1  # Decreased from 0.5
        
        # Adjust RGFlow parameters for Lean files
        self.adaptation_equation.SCALE_STEPS = 5  # Reduced from 10
        
        # Recompute LUT with new constants
        self.adaptation_equation.adaptation_surface = self.adaptation_equation._precompute_adaptation_surface()
        
        # File extensions to analyze
        self.target_extensions = {'.lean'}
        
        # Directories to exclude
        self.exclude_dirs = {
            '.git', '.lake', 'node_modules', '__pycache__', '.pytest_cache',
            'hutter_venv', 'out', 'shared-data/data/archives', 'shared-data/data/archive', 'shared-data/data/swarm',
            'venv', 'venv_unsloth', '.venv', 'site-packages', 'blackboard'
        }
    
    def extract_lean_features(self, filepath: Path) -> AdaptationState:
        """Extract adaptation equation variables from Lean file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Failed to read {filepath}: {e}")
            return AdaptationState(0, 0, 0.001, 0.001, 0, 0)
        
        # μ_q: Mutation rate (code change frequency)
        mu_q = min(len(content) / 10000.0, 1.0) * 0.01  # Smaller for Lean files
        
        # ρ_q: Refresh rate (how often code is updated)
        rho_q = 0.5  # Default refresh rate
        
        # C_fac: Graph connectance (import/dependency density)
        import_count = len([line for line in content.split('\n') if 'import' in line.lower()])
        C_fac = min(import_count / 20.0, 1.0)
        C_fac = max(0.001, C_fac)
        
        # M_fac: Modularity (definition/theorem organization)
        def_count = len([line for line in content.split('\n') if 'def ' in line])
        theorem_count = len([line for line in content.split('\n') if 'theorem' in line.lower()])
        structure_count = len([line for line in content.split('\n') if 'structure' in line.lower()])
        M_fac = min((def_count + theorem_count + structure_count) / 50.0, 1.0)
        M_fac = max(0.001, M_fac)
        
        # n_e: Observer count (references, citations)
        path_depth = len(filepath.parts)
        n_e = min(path_depth / 10.0, 1.0)
        
        # σ_q: Selection coefficient (fitness/significance)
        # CRITICAL: Must be > 1 for Layer 3 to pass
        entropy = self._calculate_entropy(content)
        text_complexity = self._calculate_text_complexity(content)
        base_fitness = (entropy + text_complexity) / 2.0
        sigma_q = 1.0 + base_fitness  # Scale to [1, 2] range
        
        return AdaptationState(mu_q, rho_q, C_fac, M_fac, n_e, sigma_q)
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text."""
        if not text:
            return 0.0
        
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        total = len(text)
        entropy = 0.0
        for count in char_counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * np.log2(probability)
        
        max_entropy = np.log2(len(char_counts)) if char_counts else 1.0
        return min(entropy / max_entropy, 1.0) if max_entropy > 0 else 0.0
    
    def _calculate_text_complexity(self, text: str) -> float:
        """Calculate text complexity (unique words / total words)."""
        if not text:
            return 0.0
        
        words = text.split()
        if not words:
            return 0.0
        
        unique_words = len(set(word.lower() for word in words))
        total_words = len(words)
        
        return min(unique_words / total_words, 1.0)
    
    def analyze_file(self, filepath: Path) -> LeanCodeAnalysis:
        """Analyze a single file using RGFlow."""
        adaptation_state = self.extract_lean_features(filepath)
        
        (lawful_now, lawful_under_flow, reaches_attractor, flows_to_noise,
         flows_to_sabotage, adaptation_cost, stability_margin, rg_depth,
         attractor_id, failure_mask) = self.adaptation_equation.evaluate_state(adaptation_state)
        
        return LeanCodeAnalysis(
            filepath=str(filepath),
            lawful_now=lawful_now,
            lawful_under_flow=lawful_under_flow,
            reaches_attractor=reaches_attractor,
            flows_to_noise=flows_to_noise,
            flows_to_sabotage=flows_to_sabotage,
            adaptation_cost=adaptation_cost,
            stability_margin=stability_margin,
            rg_depth=rg_depth,
            attractor_id=attractor_id,
            failure_mask=failure_mask
        )
    
    def scan_specific_file(self, filepath: Path) -> None:
        """Analyze a specific Lean file."""
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return
        
        if filepath.suffix not in self.target_extensions:
            logger.warning(f"Not a Lean file: {filepath}")
            return
        
        analysis = self.analyze_file(filepath)
        self.analyses.append(analysis)
        logger.info(f"Analyzed: {filepath}")
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive report of the analysis."""
        if not self.analyses:
            return {}
        
        lawful_files = [a for a in self.analyses if a.lawful_under_flow]
        noise_files = [a for a in self.analyses if a.flows_to_noise]
        sabotage_files = [a for a in self.analyses if a.flows_to_sabotage]
        
        # Statistics
        total = len(self.analyses)
        lawful_count = len(lawful_files)
        noise_count = len(noise_files)
        sabotage_count = len(sabotage_files)
        local_only_lawful = len([a for a in self.analyses if a.lawful_now and not a.lawful_under_flow])
        
        # Attractor distribution
        attractor_counts = {}
        for analysis in lawful_files:
            attractor_id = analysis.attractor_id
            attractor_counts[attractor_id] = attractor_counts.get(attractor_id, 0) + 1
        
        # Average metrics
        avg_cost = np.mean([a.adaptation_cost for a in self.analyses])
        avg_margin = np.mean([a.stability_margin for a in self.analyses])
        avg_rg_depth = np.mean([a.rg_depth for a in self.analyses])
        
        # Failure mask distribution
        failure_mask_counts = {}
        for analysis in self.analyses:
            mask = analysis.failure_mask
            failure_mask_counts[mask] = failure_mask_counts.get(mask, 0) + 1
        
        report = {
            'total_files_analyzed': total,
            'lawful_under_rgflow': lawful_count,
            'flows_to_noise': noise_count,
            'flows_to_sabotage': sabotage_count,
            'local_only_lawful': local_only_lawful,
            'lawfulness_rate': lawful_count / total if total > 0 else 0,
            'attractor_distribution': attractor_counts,
            'failure_mask_distribution': failure_mask_counts,
            'average_adaptation_cost': avg_cost,
            'average_stability_margin': avg_margin,
            'average_rg_depth': avg_rg_depth,
            'lawful_files': [a.filepath for a in lawful_files],
            'noise_files': [a.filepath for a in noise_files],
            'sabotage_files': [a.filepath for a in sabotage_files]
        }
        
        return report
    
    def print_report(self, report: Dict) -> None:
        """Print the analysis report."""
        print("\n" + "="*80)
        print("RGFlow Lean File Filter Report")
        print("="*80)
        print(f"\nTotal Lean files analyzed: {report['total_files_analyzed']}")
        print(f"Lawful under RGFlow: {report['lawful_under_rgflow']} ({report['lawfulness_rate']:.2%})")
        print(f"Flows to noise: {report['flows_to_noise']}")
        print(f"Flows to sabotage: {report['flows_to_sabotage']}")
        print(f"Locally lawful only (fails RGFlow): {report['local_only_lawful']}")
        
        print(f"\nAverage metrics:")
        print(f"  Adaptation cost: {report['average_adaptation_cost']:.4f}")
        print(f"  Stability margin: {report['average_stability_margin']:.4f}")
        print(f"  RGFlow depth: {report['average_rg_depth']:.2f}")
        
        print(f"\nAttractor distribution:")
        for attractor_id, count in report['attractor_distribution'].items():
            print(f"  Attractor {attractor_id}: {count} files")
        
        print(f"\nFailure mask distribution:")
        for mask, count in report['failure_mask_distribution'].items():
            print(f"  Mask {mask:04b}: {count} files")
        
        if report['lawful_files']:
            print(f"\n✓ Lawful Lean files:")
            for filepath in report['lawful_files']:
                print(f"  ✓ {filepath}")
        
        if report['noise_files']:
            print(f"\n⚠  NOISE FILES (POTENTIALLY BUGGY):")
            for filepath in report['noise_files']:
                print(f"  ⚠ {filepath}")
        
        if report['sabotage_files']:
            print(f"\n✗ SABOTAGE FILES (HIGH RISK):")
            for filepath in report['sabotage_files']:
                print(f"  ✗ {filepath}")
        
        print("\n" + "="*80)


def main():
    """Main entry point."""
    # Analyze specific Lean file
    killer_criterion_path = Path("/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/KillerCriterion.lean")
    
    filter = RGFlowLeanFilter()
    filter.scan_specific_file(killer_criterion_path)
    report = filter.generate_report()
    filter.print_report(report)


if __name__ == "__main__":
    main()
