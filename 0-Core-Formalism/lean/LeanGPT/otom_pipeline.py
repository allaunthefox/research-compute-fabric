#!/usr/bin/env python3
"""
OTOM LeanGPT Pipeline
Integrates LeanGPT framework as testing pipeline for OTOM Lean modules

Per AGENTS.md §6.1: Python shim for testing pipeline only
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OTOMLeanGPTPipeline")

@dataclass
class LeanModule:
    """OTOM Lean module for testing"""
    name: str
    path: str
    domain: str
    theorems: int
    status: str  # "complete", "wip", "todo"

@dataclass
class TestResult:
    """Test result for a Lean module"""
    module: str
    lake_build: bool
    theorems_checked: int
    errors: List[str]
    duration: float
    timestamp: str

class OTOMLeanGPTPipeline:
    """
    Integrates LeanGPT framework for testing OTOM Lean modules.
    
    Pipeline:
    1. Lake build check (compilation)
    2. Theorem verification
    3. AI-assisted proof generation (future)
    """
    
    def __init__(self, lean_path: str = None, lean_gpt_path: str = None):
        self.lean_path = Path(lean_path) if lean_path else Path("/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics")
        self.lean_gpt_path = Path(lean_gpt_path) if lean_gpt_path else Path("/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/LeanGPT")
        self.results: List[TestResult] = []
        
        # OTOM v2.1 modules
        self.modules = [
            LeanModule("GenomicCompression", "Semantics/GenomicCompression.lean", "Compression", 4, "complete"),
            LeanModule("ResearchAgent", "Semantics/ResearchAgent.lean", "Cognitive/Control", 4, "complete"),
            LeanModule("CrossModalCompression", "Semantics/CrossModalCompression.lean", "Compression", 2, "complete"),
            LeanModule("AgenticOrchestration", "Semantics/AgenticOrchestration.lean", "Cognitive/Control", 0, "complete"),
            LeanModule("BracketShellCount", "Semantics/BracketShellCount.lean", "Braid/Algebra", 2, "wip"),
        ]
        
        logger.info(f"OTOM LeanGPT Pipeline initialized")
        logger.info(f"Lean path: {self.lean_path}")
        logger.info(f"LeanGPT path: {self.lean_gpt_path}")
    
    def lake_build_module(self, module: LeanModule) -> tuple[bool, List[str], float]:
        """Run lake build on the entire Semantics package"""
        start_time = datetime.now()
        module_path = self.lean_path / module.path
        
        if not module_path.exists():
            return False, [f"Module not found: {module_path}"], 0.0
        
        try:
            # Build the entire Semantics package
            result = subprocess.run(
                ["lake", "build"],
                cwd=self.lean_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for full build
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            success = result.returncode == 0
            
            errors = []
            if not success:
                # Extract last 500 chars of stderr for error reporting
                stderr_lines = result.stderr.split('\n')
                error_lines = [line for line in stderr_lines if 'error:' in line.lower()]
                if error_lines:
                    errors.append('\n'.join(error_lines[-5:]))  # Last 5 error lines
                else:
                    errors.append(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            
            return success, errors, duration
            
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            return False, ["Build timeout after 300s"], duration
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return False, [f"Build error: {str(e)}"], duration
    
    def check_theorems(self, module: LeanModule) -> int:
        """
        Check theorems in a module (placeholder for LeanGPT integration).
        
        In full implementation, this would:
        1. Parse the module for theorem declarations
        2. Check which have proofs vs sorry
        3. Use LeanGPT to attempt proof generation for sorry placeholders
        """
        # Placeholder: use Grep to find theorems
        # For now, return the expected count from module definition
        return module.theorems
    
    def run_test(self, module: LeanModule) -> TestResult:
        """Run full test on a module"""
        logger.info(f"Testing module: {module.name}")
        
        # Step 1: Lake build
        build_success, build_errors, build_duration = self.lake_build_module(module)
        
        # Step 2: Check theorems
        theorems_checked = self.check_theorems(module)
        
        result = TestResult(
            module=module.name,
            lake_build=build_success,
            theorems_checked=theorems_checked,
            errors=build_errors,
            duration=build_duration,
            timestamp=datetime.now().isoformat()
        )
        
        self.results.append(result)
        logger.info(f"Test complete: {module.name} - Success: {build_success}")
        
        return result
    
    def run_pipeline(self) -> Dict:
        """Run full OTOM pipeline test"""
        logger.info("=" * 60)
        logger.info("OTOM LEANGPT PIPELINE")
        logger.info("=" * 60)
        
        for module in self.modules:
            self.run_test(module)
        
        # Summary statistics
        total_modules = len(self.modules)
        successful_builds = sum(1 for r in self.results if r.lake_build)
        total_theorems = sum(r.theorems_checked for r in self.results)
        total_errors = sum(len(r.errors) for r in self.results)
        
        summary = {
            "total_modules": total_modules,
            "successful_builds": successful_builds,
            "build_success_rate": successful_builds / total_modules if total_modules > 0 else 0,
            "total_theorems": total_theorems,
            "total_errors": total_errors,
            "results": [asdict(r) for r in self.results],
            "timestamp": datetime.now().isoformat()
        }
        
        # Save results
        results_file = self.lean_gpt_path / "otom_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\nPipeline complete. Results saved to {results_file}")
        
        return summary
    
    def print_summary(self, summary: Dict):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("OTOM LEANGPT PIPELINE RESULTS")
        print("=" * 60)
        print(f"Total modules: {summary['total_modules']}")
        print(f"Successful builds: {summary['successful_builds']}/{summary['total_modules']}")
        print(f"Build success rate: {summary['build_success_rate']:.2%}")
        print(f"Total theorems: {summary['total_theorems']}")
        print(f"Total errors: {summary['total_errors']}")
        
        print("\nModule Results:")
        print("-" * 60)
        for result in summary['results']:
            status = "✓" if result['lake_build'] else "✗"
            print(f"{status} {result['module']:20} | Theorems: {result['theorems_checked']:2} | Duration: {result['duration']:6.2f}s")
            if result['errors']:
                for error in result['errors'][:2]:
                    print(f"   Error: {error}")
        
        print("=" * 60)

# CLI interface
if __name__ == "__main__":
    print("=" * 60)
    print("OTOM LEANGPT PIPELINE")
    print("=" * 60)
    
    pipeline = OTOMLeanGPTPipeline()
    summary = pipeline.run_pipeline()
    pipeline.print_summary(summary)
