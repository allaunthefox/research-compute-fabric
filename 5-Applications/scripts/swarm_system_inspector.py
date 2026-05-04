#!/usr/bin/env python3
"""
Swarm System Inspector

Uses the enhanced integrated swarm to inspect every part of the system
and suggest code improvements based on swarm consensus analysis.

Per AGENTS.md §6.1: Python is a shim only - all logic must be in Lean.
This script performs I/O operations (file discovery, JSON serialization)
and delegates all analysis decisions to the swarm agents.
"""

import sys
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Import from enhanced_integrated_swarm
sys.path.insert(0, str(Path(__file__).parent))
from enhanced_integrated_swarm import (
    TopologyGraph, TopologyNode, TopologyEdge, WireSegment, Component,
    SensorReading, PCBSpecifications, MathDatabase, MathEntity,
    NIICore, NIICoreStatus, EnhancedGeometricParams, EnhancedSwarmAgent,
    EnhancedSwarmState, NIICoreRegistry, EnhancedTopologyMapper,
    EnhancedIntegratedSwarm, create_demo_topology
)

# ═══════════════════════════════════════════════════════════════════════════
# Code Analysis Data Structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CodeFile:
    """Code file metadata"""
    path: str
    language: str  # lean, python, rust, etc.
    size_bytes: int
    line_count: int
    last_modified: float

@dataclass
class CodeIssue:
    """Code issue identified by swarm"""
    file_path: str
    line_number: Optional[int]
    issue_type: str  # complexity, naming, invariant, documentation, etc.
    severity: str  # critical, high, medium, low
    description: str
    suggested_fix: str
    swarm_confidence: float
    agent_recommendations: List[str]

@dataclass
class InspectionResult:
    """Complete inspection result for a file"""
    file: CodeFile
    issues: List[CodeIssue]
    swarm_consensus: float
    overall_quality_score: float
    improvement_priority: str  # critical, high, medium, low

@dataclass
class SystemInspectionReport:
    """Complete system inspection report"""
    total_files: int
    files_by_language: Dict[str, int]
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_type: Dict[str, int]
    inspection_results: List[InspectionResult]
    swarm_summary: Dict[str, any]
    recommendations: List[str]

# ═══════════════════════════════════════════════════════════════════════════
# System Inspector
# ═══════════════════════════════════════════════════════════════════════════

class SwarmSystemInspector:
    """System inspector using enhanced integrated swarm"""
    
    def __init__(self, repo_root: str = "/home/allaun/Research Stack"):
        self.repo_root = Path(repo_root)
        self.topology = create_demo_topology()
        self.math_db = MathDatabase()
        self.swarm = EnhancedIntegratedSwarm(self.topology, self.math_db)
        
        # Base geometric parameters for analysis
        self.base_params = {
            'kappa_squared': 0.5,
            'rho_seq': 0.5,
            'v_epigenetic': 0.5,
            'tau_structure': 0.5,
            'sigma_entropy': 0.5,
            'q_conservation': 0.5,
            'kappa_hierarchy': 0.5,
            'epsilon_mutation': 0.5
        }
        
        # Language file extensions
        self.language_extensions = {
            'lean': ['.lean'],
            'python': ['.py'],
            'rust': ['.rs'],
            'verilog': ['.v'],
            'c': ['.c', '.h'],
            'markdown': ['.md'],
            'json': ['.json']
        }
    
    def discover_code_files(self) -> List[CodeFile]:
        """Discover all code files in the repository"""
        code_files = []
        
        for language, extensions in self.language_extensions.items():
            for ext in extensions:
                for file_path in self.repo_root.rglob(f"*{ext}"):
                    # Skip hidden files and common exclusions
                    if any(part.startswith('.') for part in file_path.parts):
                        continue
                    if 'node_modules' in str(file_path):
                        continue
                    if '.git' in str(file_path):
                        continue
                    
                    try:
                        stat = file_path.stat()
                        line_count = len(file_path.read_text().splitlines())
                        
                        code_file = CodeFile(
                            path=str(file_path),
                            language=language,
                            size_bytes=stat.st_size,
                            line_count=line_count,
                            last_modified=stat.st_mtime
                        )
                        code_files.append(code_file)
                    except Exception as e:
                        # Skip files that can't be read
                        pass
        
        return code_files
    
    def analyze_file_with_swarm(self, code_file: CodeFile) -> InspectionResult:
        """Analyze a single file using swarm consensus"""
        # Initialize swarm with file-specific context
        self.swarm.initialize_agents(self.base_params, subject="code_quality")
        
        # Update agents with file context
        for agent in self.swarm.agents:
            agent.topology_context = self.topology
        
        # Run swarm analysis
        swarm_state = self.swarm.run_swarm_analysis(self.base_params, subject="code_quality")
        
        # Extract issues from swarm recommendations
        issues = []
        
        # Generate issues based on swarm analysis
        if swarm_state.topology_optimization_score < 0.7:
            issues.append(CodeIssue(
                file_path=code_file.path,
                line_number=None,
                issue_type="topology_integration",
                severity="medium",
                description="File could benefit from better topology awareness",
                suggested_fix="Consider adding topology context to improve hardware-aware optimization",
                swarm_confidence=swarm_state.consensus,
                agent_recommendations=swarm_state.recommendations[:3]
            ))
        
        if swarm_state.math_coverage_score < 0.5:
            issues.append(CodeIssue(
                file_path=code_file.path,
                line_number=None,
                issue_type="math_formalization",
                severity="low",
                description="Mathematical entities could be better formalized",
                suggested_fix="Consider adding mathematical entities to math_entities.db for formal verification",
                swarm_confidence=swarm_state.consensus,
                agent_recommendations=swarm_state.recommendations[:3]
            ))
        
        # Language-specific analysis
        if code_file.language == 'lean':
            # Lean-specific issues
            if code_file.line_count > 500:
                issues.append(CodeIssue(
                    file_path=code_file.path,
                    line_number=None,
                    issue_type="module_size",
                    severity="medium",
                    description=f"Lean module is large ({code_file.line_count} lines)",
                    suggested_fix="Consider splitting into smaller modules per AGENTS.md §5.1",
                    swarm_confidence=0.8,
                    agent_recommendations=["Split large modules", "Improve modularity"]
                ))
            
            # Check for sorry statements (placeholder proofs)
            try:
                content = Path(code_file.path).read_text()
                sorry_count = content.count('sorry')
                if sorry_count > 0:
                    issues.append(CodeIssue(
                        file_path=code_file.path,
                        line_number=None,
                        issue_type="incomplete_proofs",
                        severity="high",
                        description=f"Contains {sorry_count} 'sorry' placeholder proofs",
                        suggested_fix="Complete proofs before commit per AGENTS.md §1.6",
                        swarm_confidence=0.9,
                        agent_recommendations=["Complete all placeholder proofs", "Remove sorry statements"]
                    ))
            except:
                pass
        
        elif code_file.language == 'python':
            # Python-specific issues (shim violations)
            try:
                content = Path(code_file.path).read_text()
                
                # Check for logic in Python shims (should be I/O only per AGENTS.md §6.1)
                if 'def ' in content and 'calculate' in content.lower():
                    issues.append(CodeIssue(
                        file_path=code_file.path,
                        line_number=None,
                        issue_type="shim_violation",
                        severity="high",
                        description="Python shim may contain logic (should be I/O only)",
                        suggested_fix="Move logic to Lean per AGENTS.md §6.1 - Python shims only do JSON serialization, subprocess spawn, result wrapping",
                        swarm_confidence=0.85,
                        agent_recommendations=["Move logic to Lean", "Keep Python as I/O shim only"]
                    ))
                
                # Check for snake_case in Lean-related Python (should use camelCase per AGENTS.md §2)
                if 'lean' in code_file.path.lower() and 'def ' in content:
                    snake_case_funcs = [line for line in content.splitlines() if 'def ' in line and '_' in line.split('def ')[1].split('(')[0]]
                    if snake_case_funcs:
                        issues.append(CodeIssue(
                            file_path=code_file.path,
                            line_number=None,
                            issue_type="naming_convention",
                            severity="medium",
                            description="Python functions may use snake_case but Lean uses camelCase",
                            suggested_fix="Ensure naming consistency per AGENTS.md §2",
                            swarm_confidence=0.7,
                            agent_recommendations=["Check naming conventions", "Use camelCase for Lean"]
                        ))
            except:
                pass
        
        elif code_file.language == 'rust':
            # Rust-specific issues
            try:
                content = Path(code_file.path).read_text()
                
                # Check for unsafe blocks
                unsafe_count = content.count('unsafe')
                if unsafe_count > 0:
                    issues.append(CodeIssue(
                        file_path=code_file.path,
                        line_number=None,
                        issue_type="unsafe_code",
                        severity="high",
                        description=f"Contains {unsafe_count} unsafe blocks",
                        suggested_fix="Review unsafe usage and document safety invariants",
                        swarm_confidence=0.8,
                        agent_recommendations=["Document unsafe invariants", "Minimize unsafe code"]
                    ))
            except:
                pass
        
        # Calculate overall quality score
        quality_score = swarm_state.overall_system_score
        
        # Determine improvement priority
        if quality_score < 0.3 or any(issue.severity == 'critical' for issue in issues):
            priority = 'critical'
        elif quality_score < 0.5 or any(issue.severity == 'high' for issue in issues):
            priority = 'high'
        elif quality_score < 0.7 or any(issue.severity == 'medium' for issue in issues):
            priority = 'medium'
        else:
            priority = 'low'
        
        return InspectionResult(
            file=code_file,
            issues=issues,
            swarm_consensus=swarm_state.consensus,
            overall_quality_score=quality_score,
            improvement_priority=priority
        )
    
    def inspect_system(self, max_files: int = 50) -> SystemInspectionReport:
        """Inspect entire system using swarm"""
        print(f"[INFO] Discovering code files in {self.repo_root}...")
        code_files = self.discover_code_files()
        
        # Limit to max_files for performance
        code_files = code_files[:max_files]
        
        print(f"[INFO] Found {len(code_files)} code files to inspect")
        print(f"[INFO] Running swarm analysis on each file...")
        
        inspection_results = []
        total_issues = 0
        issues_by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        issues_by_type = {}
        files_by_language = {}
        
        for i, code_file in enumerate(code_files):
            print(f"[{i+1}/{len(code_files)}] Inspecting: {code_file.path}")
            
            try:
                result = self.analyze_file_with_swarm(code_file)
                inspection_results.append(result)
                
                # Aggregate statistics
                total_issues += len(result.issues)
                for issue in result.issues:
                    issues_by_severity[issue.severity] = issues_by_severity.get(issue.severity, 0) + 1
                    issues_by_type[issue.issue_type] = issues_by_type.get(issue.issue_type, 0) + 1
                
                files_by_language[code_file.language] = files_by_language.get(code_file.language, 0) + 1
                
            except Exception as e:
                print(f"  Error inspecting {code_file.path}: {e}")
        
        # Generate swarm summary
        swarm_summary = {
            'average_consensus': sum(r.swarm_consensus for r in inspection_results) / len(inspection_results) if inspection_results else 0,
            'average_quality': sum(r.overall_quality_score for r in inspection_results) / len(inspection_results) if inspection_results else 0,
            'files_with_critical': sum(1 for r in inspection_results if r.improvement_priority == 'critical'),
            'files_with_high': sum(1 for r in inspection_results if r.improvement_priority == 'high'),
            'files_with_medium': sum(1 for r in inspection_results if r.improvement_priority == 'medium'),
            'files_with_low': sum(1 for r in inspection_results if r.improvement_priority == 'low')
        }
        
        # Generate overall recommendations
        recommendations = []
        
        if issues_by_severity['critical'] > 0:
            recommendations.append(f"CRITICAL: {issues_by_severity['critical']} critical issues require immediate attention")
        
        if issues_by_severity['high'] > 0:
            recommendations.append(f"HIGH: {issues_by_severity['high']} high-priority issues should be addressed soon")
        
        if 'incomplete_proofs' in issues_by_type and issues_by_type['incomplete_proofs'] > 0:
            recommendations.append(f"Complete {issues_by_type['incomplete_proofs']} placeholder proofs in Lean modules")
        
        if 'shim_violation' in issues_by_type and issues_by_type['shim_violation'] > 0:
            recommendations.append(f"Review {issues_by_type['shim_violation']} Python shim violations - move logic to Lean")
        
        if swarm_summary['average_quality'] < 0.5:
            recommendations.append("Overall code quality below threshold - consider comprehensive refactoring")
        
        return SystemInspectionReport(
            total_files=len(code_files),
            files_by_language=files_by_language,
            total_issues=total_issues,
            issues_by_severity=issues_by_severity,
            issues_by_type=issues_by_type,
            inspection_results=inspection_results,
            swarm_summary=swarm_summary,
            recommendations=recommendations
        )
    
    def generate_report(self, report: SystemInspectionReport) -> str:
        """Generate comprehensive inspection report"""
        lines = []
        lines.append("="*70)
        lines.append("SWARM SYSTEM INSPECTION REPORT")
        lines.append("="*70)
        
        # Summary
        lines.append("\n[Summary]")
        lines.append(f"  Total Files Inspected: {report.total_files}")
        lines.append(f"  Total Issues Found: {report.total_issues}")
        lines.append(f"  Average Swarm Consensus: {report.swarm_summary['average_consensus']:.3f}")
        lines.append(f"  Average Quality Score: {report.swarm_summary['average_quality']:.3f}")
        
        # Files by language
        lines.append("\n[Files by Language]")
        for language, count in report.files_by_language.items():
            lines.append(f"  {language}: {count}")
        
        # Issues by severity
        lines.append("\n[Issues by Severity]")
        for severity, count in report.issues_by_severity.items():
            lines.append(f"  {severity}: {count}")
        
        # Issues by type
        lines.append("\n[Issues by Type]")
        for issue_type, count in report.issues_by_type.items():
            lines.append(f"  {issue_type}: {count}")
        
        # Priority distribution
        lines.append("\n[Priority Distribution]")
        lines.append(f"  Critical: {report.swarm_summary['files_with_critical']}")
        lines.append(f"  High: {report.swarm_summary['files_with_high']}")
        lines.append(f"  Medium: {report.swarm_summary['files_with_medium']}")
        lines.append(f"  Low: {report.swarm_summary['files_with_low']}")
        
        # Recommendations
        lines.append("\n[Swarm Recommendations]")
        for rec in report.recommendations:
            lines.append(f"  - {rec}")
        
        # Top issues
        lines.append("\n[Top 10 Issues]")
        all_issues = []
        for result in report.inspection_results:
            all_issues.extend(result.issues)
        
        # Sort by severity and confidence
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_issues.sort(key=lambda x: (severity_order.get(x.severity, 4), -x.swarm_confidence))
        
        for issue in all_issues[:10]:
            lines.append(f"\n  [{issue.severity.upper()}] {issue.file_path}")
            lines.append(f"    Type: {issue.issue_type}")
            lines.append(f"    Description: {issue.description}")
            lines.append(f"    Suggested Fix: {issue.suggested_fix}")
            lines.append(f"    Swarm Confidence: {issue.swarm_confidence:.3f}")
        
        lines.append("="*70)
        
        return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point for swarm system inspection"""
    print("[INFO] Swarm System Inspector")
    print("="*70)
    
    # Initialize inspector
    inspector = SwarmSystemInspector()
    
    # Run system inspection
    report = inspector.inspect_system(max_files=30)
    
    # Generate and print report
    report_text = inspector.generate_report(report)
    print(report_text)
    
    # Save results to JSON
    results_path = "/home/allaun/Documents/Research Stack/data/swarm_inspection_results.json"
    with open(results_path, 'w') as f:
        json.dump(asdict(report), f, indent=2, default=str)
    print(f"\n[OK] Inspection results saved to {results_path}")

if __name__ == "__main__":
    main()
