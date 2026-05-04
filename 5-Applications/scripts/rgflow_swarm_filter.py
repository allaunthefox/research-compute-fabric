#!/usr/bin/env python3
"""
RGFlow Swarm Code Filter

Applies the Unified Adaptation Equation with RGFlow to filter swarm code files.
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

from infra.lean_unified_shim import LeanUnifiedShim

logging.basicConfig(level=logging.INFO, format='%(levelname)s:RGFlowSwarmFilter:%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class SwarmCodeAnalysis:
    """Analysis result for a swarm code file."""
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


class RGFlowSwarmFilter:
    """Filter swarm code using RGFlow mechanism."""
    
    def __init__(self, root_path: str = "/home/allaun/Research Stack"):
        self.root_path = Path(root_path)
        self.shim = LeanUnifiedShim()
        self.analyses: List[SwarmCodeAnalysis] = []
        
        # Swarm-specific directories and patterns
        self.swarm_directories = {
            'infra',
            'scripts',
            'tools/waveprobe',
            'tools/manifold'
        }
        
        self.swarm_patterns = {
            'swarm',
            'enhanced_integrated_swarm',
            'swarm_execution_layer',
            'distributed_swarm',
            'swarm_competition',
            'swarm_resource_manager',
            'swarm_topology_optimizer',
            'swarm_transport_layer',
            'swarm_api'
        }
        
        # File extensions to analyze
        self.target_extensions = {'.py', '.lean', '.rs', '.v', '.c', '.h'}
        
        # Directories to exclude
        self.exclude_dirs = {
            '.git', '.lake', 'node_modules', '__pycache__', '.pytest_cache',
            'hutter_venv', 'out', 'shared-data/data/archives', 'shared-data/data/archive', 'shared-data/data/swarm',
            'venv', 'venv_unsloth', '.venv', 'site-packages'
        }
    
    def is_swarm_file(self, filepath: Path) -> bool:
        """Check if a file is related to swarm code."""
        # Check if file is in a swarm directory
        for part in filepath.parts:
            if any(swarm_dir in part.lower() for swarm_dir in self.swarm_directories):
                return True
        
        # Check if filename matches swarm patterns
        filename = filepath.name.lower()
        if any(pattern in filename for pattern in self.swarm_patterns):
            return True
        
        return False
    
    @staticmethod
    def _to_q16_16(value: float) -> int:
        """Convert a float to Q16.16 raw integer."""
        return int(value * 65536)

    def extract_code_features(self, filepath: Path) -> dict:
        """Extract adaptation equation variables from code file.
        Returns a dict of Q16.16 raw integer values for Lean bindserver."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Failed to read {filepath}: {e}")
            return {"mu_q": 0, "rho_q": 0, "c_fac": 66, "m_fac": 66, "n_e": 0, "sigma_q": 65536}
        
        # μ_q: Mutation rate (code change frequency)
        mu_q = min(len(content) / 10000.0, 1.0) * 0.01
        
        # ρ_q: Refresh rate (how often code is updated)
        rho_q = 0.5
        
        # C_fac: Graph connectance (import/dependency density)
        import_count = len([line for line in content.split('\n') if 'import' in line.lower()])
        C_fac = min(import_count / 20.0, 1.0)
        C_fac = max(0.001, C_fac)
        
        # M_fac: Modularity (function/class organization)
        function_count = len([line for line in content.split('\n') if 'def ' in line or 'fn ' in line])
        class_count = len([line for line in content.split('\n') if 'class ' in line or 'structure ' in line])
        M_fac = min((function_count + class_count) / 50.0, 1.0)
        M_fac = max(0.001, M_fac)
        
        # n_e: Observer count (references, citations)
        path_depth = len(filepath.parts)
        n_e = min(path_depth / 10.0, 1.0)
        
        # σ_q: Selection coefficient (fitness/significance)
        entropy = self._calculate_entropy(content)
        text_complexity = self._calculate_text_complexity(content)
        base_fitness = (entropy + text_complexity) / 2.0
        sigma_q = 1.0 + base_fitness
        
        return {
            "mu_q": self._to_q16_16(mu_q),
            "rho_q": self._to_q16_16(rho_q),
            "c_fac": self._to_q16_16(C_fac),
            "m_fac": self._to_q16_16(M_fac),
            "n_e": self._to_q16_16(n_e),
            "sigma_q": self._to_q16_16(sigma_q),
        }
    
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
    
    def analyze_file(self, filepath: Path) -> SwarmCodeAnalysis:
        """Analyze a single file using Lean RGFlow bindserver.
        Python shim: only feature extraction and JSON serialization."""
        state = self.extract_code_features(filepath)
        result = self.shim.swarm_rgflow_evaluate(state, steps=5)
        
        if "error" in result:
            logger.error(f"Lean RGFlow evaluation failed for {filepath}: {result['error']}")
            return SwarmCodeAnalysis(
                filepath=str(filepath),
                lawful_now=False,
                lawful_under_flow=False,
                reaches_attractor=False,
                flows_to_noise=False,
                flows_to_sabotage=False,
                adaptation_cost=0.0,
                stability_margin=0.0,
                rg_depth=0,
                attractor_id=0,
                failure_mask=0
            )
        
        adaptation_cost = result.get("adaptation_cost", 0)
        return SwarmCodeAnalysis(
            filepath=str(filepath),
            lawful_now=result.get("lawful_now", False),
            lawful_under_flow=result.get("lawful_under_flow", False),
            reaches_attractor=result.get("reaches_attractor", False),
            flows_to_noise=result.get("flows_to_noise", False),
            flows_to_sabotage=result.get("flows_to_sabotage", False),
            adaptation_cost=float(adaptation_cost) / 65536.0,
            stability_margin=1.0 - (float(adaptation_cost) / 65536.0),
            rg_depth=result.get("rg_depth", 0),
            attractor_id=result.get("attractor_id", 0),
            failure_mask=result.get("failure_mask", 0)
        )
    
    def scan_swarm_code(self) -> None:
        """Scan the codebase for swarm-related files."""
        logger.info(f"Scanning for swarm code at {self.root_path}")
        
        file_count = 0
        for filepath in self.root_path.rglob('*'):
            # Skip directories
            if not filepath.is_file():
                continue
            
            # Skip excluded directories
            if any(excluded in filepath.parts for excluded in self.exclude_dirs):
                continue
            
            # Skip files without target extensions
            if filepath.suffix not in self.target_extensions:
                continue
            
            # Check if file is swarm-related
            if not self.is_swarm_file(filepath):
                continue
            
            # Analyze file
            analysis = self.analyze_file(filepath)
            self.analyses.append(analysis)
            file_count += 1
            
            if file_count % 10 == 0:
                logger.info(f"Analyzed {file_count} swarm files...")
        
        logger.info(f"Total swarm files analyzed: {len(self.analyses)}")
    
    def filter_lawful_files(self) -> List[SwarmCodeAnalysis]:
        """Filter files that are lawful under RGFlow."""
        lawful_files = [a for a in self.analyses if a.lawful_under_flow]
        logger.info(f"Lawful swarm files under RGFlow: {len(lawful_files)}/{len(self.analyses)}")
        return lawful_files
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive report of the analysis."""
        lawful_files = self.filter_lawful_files()
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
        print("RGFlow Swarm Code Filter Report")
        print("="*80)
        print(f"\nTotal swarm files analyzed: {report['total_files_analyzed']}")
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
            print(f"\nLawful swarm files:")
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
    filter = RGFlowSwarmFilter()
    filter.scan_swarm_code()
    report = filter.generate_report()
    filter.print_report(report)


if __name__ == "__main__":
    main()
