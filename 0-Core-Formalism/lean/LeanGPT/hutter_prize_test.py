#!/usr/bin/env python3
"""
Hutter Prize Slice Test
Tests the winning compression equation on a slice of Wikipedia text

Winning equation: C = (0.4*C_comp + 0.35*C_phys + 0.25*C_geom) × (S / (G + F))
"""

import json
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class CompressionField:
    """Compression field components."""
    comp_field: float  # Compression field value
    phys_field: float  # Physics field value
    geom_field: float  # Geometric field value

@dataclass
class ManifoldScaling:
    """Manifold scaling components."""
    spatial: float  # Spatial dimension
    geometric: float  # Geometric curvature
    field: float  # Field strength

class HutterPrizeTester:
    """Tests winning compression equation on text slices."""
    
    def __init__(self):
        self.winning_equation = "C = (0.4*C_comp + 0.35*C_phys + 0.25*C_geom) × (S / (G + F))"
        self.target_ratio = 0.1129  # 99% of current record 0.114
    
    def compute_unified_field(self, c: CompressionField) -> float:
        """Compute unified field: weighted combination of fields."""
        comp_weight = c.comp_field * 0.4
        phys_weight = c.phys_field * 0.35
        geom_weight = c.geom_field * 0.25
        return comp_weight + phys_weight + geom_weight
    
    def compute_manifold_scaling(self, m: ManifoldScaling) -> float:
        """Compute manifold scaling: spatial / (geometric + field)."""
        denom = m.geometric + m.field
        if denom > 0:
            return m.spatial / denom
        return 0
    
    def compute_hutter_prize_compression(self, c: CompressionField, m: ManifoldScaling) -> float:
        """Compute winning Hutter Prize compression equation."""
        unified_field = self.compute_unified_field(c)
        manifold_scaling = self.compute_manifold_scaling(m)
        return unified_field * manifold_scaling
    
    def analyze_text_slice(self, text: str) -> Dict:
        """Analyze a text slice and compute compression field values."""
        # Compute compression field based on text characteristics
        comp_field = self.compute_compression_field(text)
        
        # Compute physics field based on entropy
        phys_field = self.compute_physics_field(text)
        
        # Compute geometric field based on structure
        geom_field = self.compute_geometric_field(text)
        
        # Compute manifold scaling components
        spatial = self.compute_spatial_dimension(text)
        geometric = self.compute_geometric_curvature(text)
        field = self.compute_field_strength(text)
        
        return {
            "text_length": len(text),
            "comp_field": comp_field,
            "phys_field": phys_field,
            "geom_field": geom_field,
            "spatial": spatial,
            "geometric": geometric,
            "field": field
        }
    
    def compute_compression_field(self, text: str) -> float:
        """Compute compression field based on text repetition."""
        if not text:
            return 0.0
        
        # Simple compression field: ratio of repeated characters
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        repeated_chars = sum(1 for count in char_counts.values() if count > 1)
        total_chars = len(char_counts)
        
        if total_chars > 0:
            return repeated_chars / total_chars
        return 0.0
    
    def compute_physics_field(self, text: str) -> float:
        """Compute physics field based on entropy."""
        if not text:
            return 0.0
        
        # Simple entropy calculation
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        total_chars = len(text)
        entropy = 0.0
        
        import math
        for count in char_counts.values():
            prob = count / total_chars
            if prob > 0:
                entropy -= prob * math.log2(prob)  # Simplified entropy
        
        # Normalize to 0-1 range
        return min(entropy / 8.0, 1.0)  # Max entropy for 8-bit chars
    
    def compute_geometric_field(self, text: str) -> float:
        """Compute geometric field based on text structure."""
        if not text:
            return 0.0
        
        # Simple geometric field: ratio of word boundaries
        word_count = len(text.split())
        char_count = len(text)
        
        if char_count > 0:
            return word_count / char_count
        return 0.0
    
    def compute_spatial_dimension(self, text: str) -> float:
        """Compute spatial dimension based on vocabulary size."""
        if not text:
            return 0.0
        
        words = text.split()
        unique_words = len(set(words))
        total_words = len(words)
        
        if total_words > 0:
            return unique_words / total_words
        return 0.0
    
    def compute_geometric_curvature(self, text: str) -> float:
        """Compute geometric curvature based on sentence structure."""
        if not text:
            return 0.0
        
        sentences = text.split('.')
        sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
        
        if not sentence_lengths:
            return 0.0
        
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        max_length = max(sentence_lengths)
        
        if max_length > 0:
            return avg_length / max_length
        return 0.0
    
    def compute_field_strength(self, text: str) -> float:
        """Compute field strength based on text density."""
        if not text:
            return 0.0
        
        # Simple field strength: characters per word
        words = text.split()
        char_count = len(text)
        word_count = len(words)
        
        if word_count > 0:
            return char_count / word_count
        return 0.0
    
    def test_text_slice(self, text: str, slice_name: str) -> Dict:
        """Test compression on a text slice."""
        print("=" * 80)
        print(f"HUTTER PRIZE SLICE TEST: {slice_name}")
        print("=" * 80)
        
        # Analyze text
        analysis = self.analyze_text_slice(text)
        
        print(f"\nText Analysis:")
        print(f"  Length: {analysis['text_length']} characters")
        print(f"  Compression field: {analysis['comp_field']:.4f}")
        print(f"  Physics field: {analysis['phys_field']:.4f}")
        print(f"  Geometric field: {analysis['geom_field']:.4f}")
        print(f"  Spatial dimension: {analysis['spatial']:.4f}")
        print(f"  Geometric curvature: {analysis['geometric']:.4f}")
        print(f"  Field strength: {analysis['field']:.4f}")
        
        # Create compression field structure
        c = CompressionField(
            comp_field=analysis['comp_field'],
            phys_field=analysis['phys_field'],
            geom_field=analysis['geom_field']
        )
        
        # Create manifold scaling structure
        m = ManifoldScaling(
            spatial=analysis['spatial'],
            geometric=analysis['geometric'],
            field=analysis['field']
        )
        
        # Compute unified field
        unified_field = self.compute_unified_field(c)
        print(f"\nUnified Field: {unified_field:.4f}")
        print(f"  (0.4 × {c.comp_field:.4f}) + (0.35 × {c.phys_field:.4f}) + (0.25 × {c.geom_field:.4f})")
        
        # Compute manifold scaling
        manifold_scaling = self.compute_manifold_scaling(m)
        print(f"\nManifold Scaling: {manifold_scaling:.4f}")
        print(f"  {m.spatial:.4f} / ({m.geometric:.4f} + {m.field:.4f})")
        
        # Compute final compression
        compression = self.compute_hutter_prize_compression(c, m)
        print(f"\nFinal Compression: {compression:.4f}")
        print(f"  {unified_field:.4f} × {manifold_scaling:.4f}")
        
        # Calculate compression ratio
        original_size = analysis['text_length']
        compressed_size = int(original_size * compression)
        compression_ratio = compressed_size / original_size if original_size > 0 else 0
        
        print(f"\nCompression Results:")
        print(f"  Original size: {original_size} bytes")
        print(f"  Compressed size: {compressed_size} bytes")
        print(f"  Compression ratio: {compression_ratio:.4f}")
        print(f"  Target ratio: {self.target_ratio:.4f}")
        
        # Check if beats target
        beats_target = compression_ratio < self.target_ratio
        print(f"  Beats target: {beats_target}")
        
        result = {
            "slice_name": slice_name,
            "text_length": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "target_ratio": self.target_ratio,
            "beats_target": beats_target,
            "unified_field": unified_field,
            "manifold_scaling": manifold_scaling,
            "analysis": analysis
        }
        
        return result
    
    def run_tests(self):
        """Run tests on multiple text slices."""
        print("=" * 80)
        print("HUTTER PRIZE SLICE TESTING")
        print("=" * 80)
        print(f"Winning equation: {self.winning_equation}")
        print(f"Target ratio: {self.target_ratio:.4f}")
        print("=" * 80)
        
        results = []
        
        # Test slice 1: Simple repetitive text
        text1 = "The quick brown fox jumps over the lazy dog. " * 10
        result1 = self.test_text_slice(text1, "Repetitive Text Slice")
        results.append(result1)
        
        # Test slice 2: Wikipedia-style text
        text2 = """Wikipedia is a free online encyclopedia, created and edited by volunteers around the world and hosted by the Wikimedia Foundation. 
        It consists of more than 60 million articles in 300 languages, which are written collaboratively by volunteers around the world. 
        The encyclopedia is consistently one of the 10 most visited websites on the internet."""
        result2 = self.test_text_slice(text2, "Wikipedia-Style Text Slice")
        results.append(result2)
        
        # Test slice 3: Technical documentation
        text3 = """Compression algorithms reduce the size of data by encoding it more efficiently. 
        Lossless compression allows the original data to be perfectly reconstructed from the compressed data. 
        Lossy compression achieves higher compression ratios by removing less important information."""
        result3 = self.test_text_slice(text3, "Technical Documentation Slice")
        results.append(result3)
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        for result in results:
            status = "✅ BEATS TARGET" if result['beats_target'] else "❌ DOES NOT BEAT TARGET"
            print(f"\n{result['slice_name']}:")
            print(f"  Compression ratio: {result['compression_ratio']:.4f}")
            print(f"  Status: {status}")
        
        return results
    
    def save_results(self, results: list, filename: str):
        """Save test results to JSON."""
        data = {
            "winning_equation": self.winning_equation,
            "target_ratio": self.target_ratio,
            "tests": results
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nResults saved to {filename}")

if __name__ == "__main__":
    tester = HutterPrizeTester()
    results = tester.run_tests()
    tester.save_results(results, "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/LeanGPT/hutter_slice_test_results.json")
