#!/usr/bin/env python3
"""
Analyze RGFlow noise files to understand if they represent buggy code.
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

logging.basicConfig(level=logging.INFO, format='%(levelname)s:NoiseAnalyzer:%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class NoiseFileAnalysis:
    """Analysis of a noise file."""
    filepath: str
    file_size: int
    line_count: int
    entropy: float
    text_complexity: float
    structural_complexity: float
    adaptation_state: AdaptationState
    failure_mask: int


class RGFlowNoiseAnalyzer:
    """Analyze files that flow to noise under RGFlow."""
    
    def __init__(self, root_path: str = "/home/allaun/Research Stack"):
        self.root_path = Path(root_path)
        self.adaptation_equation = UnifiedAdaptationEquation()
        
        # Adjust constants for code files
        self.adaptation_equation.DRAKE_BUDGET_D = 0.1
        self.adaptation_equation.DRIFT_BARRIER_B = 0.01
        self.adaptation_equation.LAMBDA = 0.1
        self.adaptation_equation.SCALE_STEPS = 5
        self.adaptation_equation.adaptation_surface = self.adaptation_equation._precompute_adaptation_surface()
        
        self.noise_analyses: List[NoiseFileAnalysis] = []
    
    def extract_code_features(self, filepath: Path) -> AdaptationState:
        """Extract adaptation equation variables from code file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Failed to read {filepath}: {e}")
            return AdaptationState(0, 0, 0.001, 0.001, 0, 0)
        
        mu_q = min(len(content) / 10000.0, 1.0) * 0.01
        rho_q = 0.5
        import_count = len([line for line in content.split('\n') if 'import' in line.lower()])
        C_fac = min(import_count / 20.0, 1.0)
        C_fac = max(0.001, C_fac)
        function_count = len([line for line in content.split('\n') if 'def ' in line or 'fn ' in line])
        class_count = len([line for line in content.split('\n') if 'class ' in line or 'structure ' in line])
        M_fac = min((function_count + class_count) / 50.0, 1.0)
        M_fac = max(0.001, M_fac)
        path_depth = len(filepath.parts)
        n_e = min(path_depth / 10.0, 1.0)
        entropy = self._calculate_entropy(content)
        text_complexity = self._calculate_text_complexity(content)
        sigma_q = 1.0 + ((entropy + text_complexity) / 2.0)
        
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
    
    def analyze_file(self, filepath: Path) -> NoiseFileAnalysis:
        """Analyze a single file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Failed to read {filepath}: {e}")
            return None
        
        file_size = len(content)
        line_count = len(content.split('\n'))
        entropy = self._calculate_entropy(content)
        text_complexity = self._calculate_text_complexity(content)
        
        # Structural complexity
        import_count = len([line for line in content.split('\n') if 'import' in line.lower()])
        function_count = len([line for line in content.split('\n') if 'def ' in line or 'fn ' in line])
        class_count = len([line for line in content.split('\n') if 'class ' in line or 'structure ' in line])
        structural_complexity = min((import_count + function_count + class_count) / 50.0, 1.0)
        
        adaptation_state = self.extract_code_features(filepath)
        (lawful_now, lawful_under_flow, reaches_attractor, flows_to_noise,
         flows_to_sabotage, adaptation_cost, stability_margin, rg_depth,
         attractor_id, failure_mask) = self.adaptation_equation.evaluate_state(adaptation_state)
        
        return NoiseFileAnalysis(
            filepath=str(filepath),
            file_size=file_size,
            line_count=line_count,
            entropy=entropy,
            text_complexity=text_complexity,
            structural_complexity=structural_complexity,
            adaptation_state=adaptation_state,
            failure_mask=failure_mask
        )
    
    def scan_noise_files(self, noise_file_paths: List[str]) -> None:
        """Analyze specific noise files."""
        for filepath_str in noise_file_paths:
            filepath = Path(filepath_str)
            if not filepath.exists():
                continue
            
            analysis = self.analyze_file(filepath)
            if analysis:
                self.noise_analyses.append(analysis)
    
    def generate_report(self) -> Dict:
        """Generate analysis report."""
        if not self.noise_analyses:
            return {}
        
        # Statistics
        avg_file_size = np.mean([a.file_size for a in self.noise_analyses])
        avg_line_count = np.mean([a.line_count for a in self.noise_analyses])
        avg_entropy = np.mean([a.entropy for a in self.noise_analyses])
        avg_text_complexity = np.mean([a.text_complexity for a in self.noise_analyses])
        avg_structural_complexity = np.mean([a.structural_complexity for a in self.noise_analyses])
        
        # Failure mask distribution
        failure_mask_counts = {}
        for analysis in self.noise_analyses:
            mask = analysis.failure_mask
            failure_mask_counts[mask] = failure_mask_counts.get(mask, 0) + 1
        
        # Empty file count
        empty_files = len([a for a in self.noise_analyses if a.file_size == 0])
        
        report = {
            'total_noise_files': len(self.noise_analyses),
            'empty_files': empty_files,
            'avg_file_size': avg_file_size,
            'avg_line_count': avg_line_count,
            'avg_entropy': avg_entropy,
            'avg_text_complexity': avg_text_complexity,
            'avg_structural_complexity': avg_structural_complexity,
            'failure_mask_distribution': failure_mask_counts,
            'noise_files': [a.filepath for a in self.noise_analyses]
        }
        
        return report
    
    def print_report(self, report: Dict) -> None:
        """Print analysis report."""
        print("\n" + "="*80)
        print("RGFlow Noise File Analysis")
        print("="*80)
        print(f"\nTotal noise files analyzed: {report['total_noise_files']}")
        print(f"Empty files: {report['empty_files']} ({report['empty_files']/report['total_noise_files']*100:.1f}%)")
        
        print(f"\nAverage metrics:")
        print(f"  File size: {report['avg_file_size']:.1f} bytes")
        print(f"  Line count: {report['avg_line_count']:.1f} lines")
        print(f"  Entropy: {report['avg_entropy']:.4f}")
        print(f"  Text complexity: {report['avg_text_complexity']:.4f}")
        print(f"  Structural complexity: {report['avg_structural_complexity']:.4f}")
        
        print(f"\nFailure mask distribution:")
        for mask, count in report['failure_mask_distribution'].items():
            print(f"  Mask {mask:04b}: {count} files")
        
        print(f"\nNoise file characteristics:")
        print(f"  High percentage of empty files suggests:")
        print(f"    - RGFlow detects stub/placeholder files")
        print(f"    - Files with insufficient content fail Drift Barrier")
        print(f"    - This could indicate:")
        print(f"      * Incomplete implementations")
        print(f"      * TODO/placeholder files")
        print(f"      * Broken or corrupted files")
        
        print("\n" + "="*80)


def main():
    """Main entry point."""
    # Sample noise files from the RGFlow filter report
    noise_files = [
        "/home/allaun/Documents/Research Stack/manifold_sample.txt",
        "/home/allaun/Documents/Research Stack/docs/nlab/pages/9/8/0/6/16089/content.md",
        "/home/allaun/Documents/Research Stack/docs/nlab/pages/9/7/4/7/27479/content.md",
        "/home/allaun/Documents/Research Stack/docs/nlab/pages/9/6/3/7/17369/content.md",
        "/home/allaun/Documents/Research Stack/docs/nlab/pages/9/4/3/8/18349/content.md",
    ]
    
    analyzer = RGFlowNoiseAnalyzer()
    analyzer.scan_noise_files(noise_files)
    report = analyzer.generate_report()
    analyzer.print_report(report)


if __name__ == "__main__":
    main()
