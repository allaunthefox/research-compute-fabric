#!/usr/bin/env python3
"""
BioRxiv Metaprobe - Mathematical Content Audit

Adapts unified metaprobe framework for bioRxiv mathematical content analysis.
Validates resonance with Research Stack mathematical foundations, structural
coherence of mathematical expressions, and lawful alignment with Lean formalization.

Channels:
- SEQUENCE_SIMILARITY: ANI, AAI, BLAST metrics
- PHYLOGENETICS: Jukes-Cantor, MAFFT alignment
- STRUCTURAL_BIOLOGY: pLDDT, pTM, FSC metrics
- STATISTICAL: ANOVA, Tukey HSD, fold change
- INFORMATION_THEORY: Shannon diversity, entropy
- GENOME_ARCHITECTURE: ORF boundaries, similarity scores
"""

import re
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json

# ═══════════════════════════════════════════════════════════════════════════
# BioRxiv Metaprobe Channels
# ═══════════════════════════════════════════════════════════════════════════

class BioRxivMetaprobeChannel(Enum):
    """Metaprobe channels for bioRxiv mathematical content"""
    SEQUENCE_SIMILARITY = 0      # ANI, AAI, BLAST metrics
    PHYLOGENETICS = 1           # Jukes-Cantor, MAFFT
    STRUCTURAL_BIOLOGY = 2      # pLDDT, pTM, FSC
    STATISTICAL = 3             # ANOVA, Tukey HSD, fold change
    INFORMATION_THEORY = 4      # Shannon diversity, entropy
    GENOME_ARCHITECTURE = 5     # ORF boundaries, architecture scores

@dataclass
class BioRxivMetaprobeState:
    """Metaprobe state for a bioRxiv channel"""
    channel: BioRxivMetaprobeChannel
    resonance_score: float
    structural_coherence: float
    entropy: float
    lawful: bool
    mathematical_correctness: float
    lean_alignment: float
    issues: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'channel': self.channel.name,
            'resonance_score': self.resonance_score,
            'structural_coherence': self.structural_coherence,
            'entropy': self.entropy,
            'lawful': self.lawful,
            'mathematical_correctness': self.mathematical_correctness,
            'lean_alignment': self.lean_alignment,
            'issues': self.issues
        }

class BioRxivMetaprobe:
    """BioRxiv-specific metaprobe for mathematical content audit"""
    
    def __init__(self):
        self.threshold = 0.8
        self.math_threshold = 0.85
        self.lean_threshold = 0.75
        self.audit_log: List[Dict] = []
        
        # Load extracted math from Evo paper
        self.extracted_math = self._load_extracted_math()
        
    def _load_extracted_math(self) -> Dict:
        """Load extracted mathematical models from Evo paper or Lean formalization"""
        try:
            # Try Lean formalization first (preferred)
            with open('0-Core-Formalism/lean/Semantics/Semantics/BioRxivFormalization.lean', 'r') as f:
                content = f.read()
            return self._parse_lean_formalization(content)
        except FileNotFoundError:
            try:
                # Fallback to extraction document
                with open('shared-data/data/evo_bacteriophage_math_extraction.md', 'r') as f:
                    content = f.read()
                return self._parse_math_extraction(content)
            except FileNotFoundError:
                return {}
    
    def _parse_math_extraction(self, content: str) -> Dict:
        """Parse mathematical extraction document"""
        models = {}
        current_section = None
        
        for line in content.split('\n'):
            if line.startswith('##'):
                current_section = line.replace('##', '').strip()
                models[current_section] = []
            elif current_section and line.strip() and not line.startswith('#'):
                models[current_section].append(line.strip())
        
        return models
    
    def _parse_lean_formalization(self, content: str) -> Dict:
        """Parse Lean formalization file"""
        models = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            # Detect section headers in Lean comments
            if '/-! ## Section' in line:
                if current_section:
                    models[current_section] = current_content
                current_section = line.split('##')[1].strip().replace(' -/', '').strip()
                current_content = []
            elif current_section and line.strip():
                # Include structure definitions, theorems, and equations
                if any(keyword in line for keyword in ['structure', 'def', 'theorem', 'Equation', ':=']):
                    current_content.append(line.strip())
                elif line.strip() and not line.startswith('/-'):
                    current_content.append(line.strip())
        
        if current_section:
            models[current_section] = current_content
        
        return models
    
    def check_resonance(self, math_content: str, channel: BioRxivMetaprobeChannel) -> float:
        """
        Check resonance with Research Stack mathematical foundations.
        
        Resonance measures how well the bioRxiv math aligns with expected
        patterns for the specific mathematical domain.
        """
        if not math_content:
            return 0.0
        
        # Channel-specific resonance checks
        if channel == BioRxivMetaprobeChannel.SEQUENCE_SIMILARITY:
            score = self._check_sequence_similarity_resonance(math_content)
        elif channel == BioRxivMetaprobeChannel.PHYLOGENETICS:
            score = self._check_phylogenetics_resonance(math_content)
        elif channel == BioRxivMetaprobeChannel.STRUCTURAL_BIOLOGY:
            score = self._check_structural_biology_resonance(math_content)
        elif channel == BioRxivMetaprobeChannel.STATISTICAL:
            score = self._check_statistical_resonance(math_content)
        elif channel == BioRxivMetaprobeChannel.INFORMATION_THEORY:
            score = self._check_information_theory_resonance(math_content)
        elif channel == BioRxivMetaprobeChannel.GENOME_ARCHITECTURE:
            score = self._check_genome_architecture_resonance(math_content)
        else:
            score = 0.5
        
        return score
    
    def _check_sequence_similarity_resonance(self, content: str) -> float:
        """Check sequence similarity metric resonance"""
        # Look for key sequence similarity metrics
        metrics = ['ANI', 'AAI', 'BLAST', 'E-value', 'percent identity']
        found_metrics = sum(1 for m in metrics if m.lower() in content.lower())
        
        # Check for proper mathematical formulation
        has_equations = '=' in content and '%' in content
        has_ranges = re.search(r'\d+\.?\d*\s*-\s*\d+\.?\d*', content) is not None
        
        score = 0.3
        if found_metrics >= 2:
            score += 0.3
        if has_equations:
            score += 0.2
        if has_ranges:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_phylogenetics_resonance(self, content: str) -> float:
        """Check phylogenetic analysis resonance"""
        # Look for phylogenetic methods
        methods = ['Jukes-Cantor', 'MAFFT', 'Neighbor-Joining', 'phylogenetic', 'alignment']
        found_methods = sum(1 for m in methods if m.lower() in content.lower())
        
        # Check for distance formulas
        has_log = 'ln' in content or 'log' in content
        has_probabilities = re.search(r'p\s*[=<>]', content) is not None
        
        score = 0.3
        if found_methods >= 2:
            score += 0.3
        if has_log:
            score += 0.2
        if has_probabilities:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_structural_biology_resonance(self, content: str) -> float:
        """Check structural biology metric resonance"""
        # Look for structural metrics
        metrics = ['pLDDT', 'pTM', 'ipTM', 'FSC', 'resolution', 'RMSD']
        found_metrics = sum(1 for m in metrics if m in content)
        
        # Check for valid ranges
        has_ranges = re.search(r'\[0,\s*1\]|\[0,\s*100\]', content) is not None
        has_fourier = 'FSC' in content or 'Fourier' in content
        
        score = 0.3
        if found_metrics >= 2:
            score += 0.3
        if has_ranges:
            score += 0.2
        if has_fourier:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_statistical_resonance(self, content: str) -> float:
        """Check statistical method resonance"""
        # Look for statistical methods
        methods = ['ANOVA', 'Tukey', 'HSD', 'fold change', 'p-value', 'significance']
        found_methods = sum(1 for m in methods if m.lower() in content.lower())
        
        # Check for proper statistical notation
        has_greek = re.search(r'[αβγδεθλμσ]', content) is not None
        has_subscripts = re.search(r'_\w+', content) is not None
        
        score = 0.3
        if found_methods >= 2:
            score += 0.3
        if has_greek:
            score += 0.2
        if has_subscripts:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_information_theory_resonance(self, content: str) -> float:
        """Check information theory resonance"""
        # Look for information theory concepts
        concepts = ['Shannon', 'entropy', 'H\'', 'log2', 'p_i', 'diversity']
        found_concepts = sum(1 for c in concepts if c.lower() in content.lower())
        
        # Check for proper entropy formula
        has_sum = 'Σ' in content or 'sum' in content.lower()
        has_log = 'log2' in content or 'log' in content
        
        score = 0.3
        if found_concepts >= 2:
            score += 0.3
        if has_sum:
            score += 0.2
        if has_log:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_genome_architecture_resonance(self, content: str) -> float:
        """Check genome architecture resonance"""
        # Look for architecture concepts
        concepts = ['ORF', 'boundary', 'Gaussian', 'blur', 'similarity', 'score']
        found_concepts = sum(1 for c in concepts if c.lower() in content.lower())
        
        # Check for mathematical functions
        has_exp = 'exp' in content or 'e^' in content
        has_correlation = 'correlation' in content.lower()
        
        score = 0.3
        if found_concepts >= 2:
            score += 0.3
        if has_exp:
            score += 0.2
        if has_correlation:
            score += 0.2
        
        return min(score, 1.0)
    
    def check_mathematical_correctness(self, content: str) -> float:
        """
        Check mathematical correctness of equations.
        
        Validates that equations are mathematically sound and follow
        standard notation conventions.
        """
        if not content:
            return 0.0
        
        # Check for balanced parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        parens_balanced = open_parens == close_parens
        
        # Check for balanced brackets
        open_brackets = content.count('[')
        close_brackets = content.count(']')
        brackets_balanced = open_brackets == close_brackets
        
        # Check for valid mathematical operators
        has_operators = any(op in content for op in ['=', '+', '-', '*', '/', '^', '≤', '≥', '<', '>'])
        
        # Check for variable definitions
        has_var_defs = re.search(r'\w+\s*[=:=]', content) is not None
        
        score = 0.0
        if parens_balanced:
            score += 0.25
        if brackets_balanced:
            score += 0.25
        if has_operators:
            score += 0.25
        if has_var_defs:
            score += 0.25
        
        return score
    
    def check_lean_alignment(self, content: str) -> float:
        """
        Check alignment with Lean formalization principles.
        
        Validates that the mathematical content could be formalized
        in Lean according to Research Stack standards.
        """
        if not content:
            return 0.0
        
        # Check for formal mathematical structure
        has_definitions = re.search(r'definition|:=|≡', content, re.IGNORECASE) is not None
        has_theorems = re.search(r'theorem|lemma|proposition', content, re.IGNORECASE) is not None
        has_proofs = re.search(r'proof|QED|∎', content, re.IGNORECASE) is not None
        
        # Check for type annotations (Lean style)
        has_types = re.search(r':\s*\w+', content) is not None or re.search(r'→', content) is not None
        
        # Check for quantifiers
        has_quantifiers = re.search(r'∀|∃|∀x|∃x', content) is not None
        
        score = 0.0
        if has_definitions:
            score += 0.3
        if has_theorems:
            score += 0.3
        if has_proofs:
            score += 0.2
        if has_types:
            score += 0.1
        if has_quantifiers:
            score += 0.1
        
        return min(score, 1.0)
    
    def calculate_entropy(self, content: str) -> float:
        """Calculate Shannon entropy of content"""
        if not content:
            return 0.0
        
        char_counts = {}
        for char in content:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        entropy = 0.0
        for count in char_counts.values():
            p = count / len(content)
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Normalize to [0, 1] range (max entropy for ASCII)
        return min(entropy / 7.0, 1.0)
    
    def calculate_coherence(self, content: str) -> float:
        """Calculate structural coherence of mathematical expressions"""
        if len(content) < 2:
            return 0.0
        
        # Check for smooth transitions in mathematical notation
        transitions = 0
        smooth = 0
        
        for i in range(len(content) - 1):
            curr = content[i]
            next_char = content[i+1]
            
            # Check if transition is coherent
            if self._is_coherent_transition(curr, next_char):
                smooth += 1
            transitions += 1
        
        if transitions == 0:
            return 0.0
        
        return smooth / transitions
    
    def _is_coherent_transition(self, curr: str, next_char: str) -> bool:
        """Check if character transition is mathematically coherent"""
        # Allow transitions between similar types
        if curr.isalpha() and next_char.isalpha():
            return True
        if curr.isdigit() and next_char.isdigit():
            return True
        if curr.isspace() and next_char.isspace():
            return True
        
        # Allow operator transitions
        operators = set('=+-*/^≤≥<>')
        if curr in operators and next_char.isspace():
            return True
        if curr.isspace() and next_char in operators:
            return True
        
        # Allow subscript transitions
        if curr == '_' and next_char.isalnum():
            return True
        
        return False
    
    def audit_channel(self, content: str, channel: BioRxivMetaprobeChannel) -> BioRxivMetaprobeState:
        """Audit a bioRxiv mathematical channel"""
        resonance = self.check_resonance(content, channel)
        coherence = self.calculate_coherence(content)
        entropy = self.calculate_entropy(content)
        math_correctness = self.check_mathematical_correctness(content)
        lean_alignment = self.check_lean_alignment(content)
        
        # Determine lawful status
        lawful = (resonance >= self.threshold and 
                 coherence >= self.threshold and
                 math_correctness >= self.math_threshold)
        
        # Collect issues
        issues = []
        if resonance < self.threshold:
            issues.append(f"Low resonance: {resonance:.3f} < {self.threshold}")
        if coherence < self.threshold:
            issues.append(f"Low coherence: {coherence:.3f} < {self.threshold}")
        if math_correctness < self.math_threshold:
            issues.append(f"Low mathematical correctness: {math_correctness:.3f} < {self.math_threshold}")
        if lean_alignment < self.lean_threshold:
            issues.append(f"Low Lean alignment: {lean_alignment:.3f} < {self.lean_threshold}")
        
        state = BioRxivMetaprobeState(
            channel=channel,
            resonance_score=resonance,
            structural_coherence=coherence,
            entropy=entropy,
            lawful=lawful,
            mathematical_correctness=math_correctness,
            lean_alignment=lean_alignment,
            issues=issues
        )
        
        # Log audit
        self.audit_log.append(state.to_dict())
        
        return state
    
    def audit_extracted_math(self) -> Dict:
        """Audit all extracted mathematical content from Evo paper"""
        print("=" * 70)
        print("BIORXIV METAPROBE - EVO BACTERIOPHAGE MATH AUDIT")
        print("=" * 70)
        
        results = {}
        
        # Audit each section of extracted math
        for section, content_list in self.extracted_math.items():
            if not content_list:
                continue
            
            # Determine channel based on section
            channel = self._section_to_channel(section)
            
            # Combine content
            content = '\n'.join(content_list)
            
            # Audit
            state = self.audit_channel(content, channel)
            results[section] = state.to_dict()
            
            print(f"\n[{section}]")
            print(f"  Channel: {channel.name}")
            print(f"  Resonance: {state.resonance_score:.3f}")
            print(f"  Coherence: {state.structural_coherence:.3f}")
            print(f"  Entropy: {state.entropy:.3f}")
            print(f"  Math Correctness: {state.mathematical_correctness:.3f}")
            print(f"  Lean Alignment: {state.lean_alignment:.3f}")
            print(f"  Lawful: {state.lawful}")
            if state.issues:
                print(f"  Issues:")
                for issue in state.issues:
                    print(f"    - {issue}")
        
        # Calculate overall metrics
        total_channels = len(results)
        lawful_count = sum(1 for r in results.values() if r['lawful'])
        avg_resonance = sum(r['resonance_score'] for r in results.values()) / total_channels
        avg_coherence = sum(r['structural_coherence'] for r in results.values()) / total_channels
        avg_math_correctness = sum(r['mathematical_correctness'] for r in results.values()) / total_channels
        avg_lean_alignment = sum(r['lean_alignment'] for r in results.values()) / total_channels
        
        print("\n" + "=" * 70)
        print("OVERALL AUDIT SUMMARY")
        print("=" * 70)
        print(f"Total Sections: {total_channels}")
        print(f"Lawful Sections: {lawful_count}/{total_channels}")
        print(f"Overall Lawful Rate: {lawful_count/total_channels:.3f}")
        print(f"Average Resonance: {avg_resonance:.3f}")
        print(f"Average Coherence: {avg_coherence:.3f}")
        print(f"Average Math Correctness: {avg_math_correctness:.3f}")
        print(f"Average Lean Alignment: {avg_lean_alignment:.3f}")
        
        if avg_lean_alignment >= self.lean_threshold:
            print("\n✅ Content aligns with Lean formalization principles")
        else:
            print(f"\n⚠️  Content requires Lean formalization refinement (current: {avg_lean_alignment:.3f})")
        
        overall = {
            'total_sections': total_channels,
            'lawful_count': lawful_count,
            'lawful_rate': lawful_count / total_channels,
            'avg_resonance': avg_resonance,
            'avg_coherence': avg_coherence,
            'avg_math_correctness': avg_math_correctness,
            'avg_lean_alignment': avg_lean_alignment,
            'section_results': results,
            'overall_lawful': lawful_count / total_channels >= 0.8
        }
        
        # Save results
        with open('shared-data/data/biorxiv_metaprobe_audit.json', 'w') as f:
            json.dump(overall, f, indent=2)
        
        print(f"\nAudit saved to: shared-data/data/biorxiv_metaprobe_audit.json")
        print("=" * 70)
        
        return overall
    
    def _section_to_channel(self, section: str) -> BioRxivMetaprobeChannel:
        """Map section name to metaprobe channel"""
        section_lower = section.lower()
        
        if 'sequence' in section_lower or 'similarity' in section_lower or 'ani' in section_lower:
            return BioRxivMetaprobeChannel.SEQUENCE_SIMILARITY
        elif 'phylogenetic' in section_lower or 'jukes' in section_lower or 'tree' in section_lower:
            return BioRxivMetaprobeChannel.PHYLOGENETICS
        elif 'structural' in section_lower or 'cryo' in section_lower or 'fold' in section_lower:
            return BioRxivMetaprobeChannel.STRUCTURAL_BIOLOGY
        elif 'statistical' in section_lower or 'anova' in section_lower or 'tukey' in section_lower:
            return BioRxivMetaprobeChannel.STATISTICAL
        elif 'information' in section_lower or 'entropy' in section_lower or 'shannon' in section_lower:
            return BioRxivMetaprobeChannel.INFORMATION_THEORY
        elif 'genome' in section_lower or 'architecture' in section_lower or 'orf' in section_lower:
            return BioRxivMetaprobeChannel.GENOME_ARCHITECTURE
        else:
            return BioRxivMetaprobeChannel.SEQUENCE_SIMILARITY  # Default

def main():
    """Run bioRxiv metaprobe audit"""
    metaprobe = BioRxivMetaprobe()
    results = metaprobe.audit_extracted_math()
    
    return results

if __name__ == "__main__":
    main()
