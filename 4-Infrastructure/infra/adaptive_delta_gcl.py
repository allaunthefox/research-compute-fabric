#!/usr/bin/env python3
"""
Adaptive Delta GCL Compression

Adaptive compression system that analyzes data patterns and selects optimal
compression strategies based on historical performance.

Features:
- Pattern detection in metadata
- Adaptive strategy selection
- Performance tracking
- Automatic strategy optimization

AUDIT-ONLY SHIM:
This script is not a source-of-truth implementation under docs/AGENTS.md.
It may generate exploratory JSON/audit evidence only. Any curvature,
compression strategy, invariant, or branching logic here must be ported to
Lean before being used by the core model or release claims.
"""

import sys
from pathlib import Path
# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum

from infra.delta_gcl_compression_service import DeltaGCLCompressionService, CompressionResult


class CompressionStrategy(Enum):
    """Compression strategy types."""
    DELTA_ONLY = "delta_only"
    PTOS_ONLY = "ptos_only"
    GCL_ONLY = "gcl_only"
    DELTA_PTOS = "delta_ptos"
    DELTA_GCL = "delta_gcl"
    FULL_STACK = "full_stack"
    ADAPTIVE = "adaptive"


@dataclass
class PatternFeatures:
    """Features extracted from data patterns."""
    field_change_rate: float  # Rate at which fields change
    value_variance: float  # Variance in field values
    sequence_length: int  # Length of data sequence
    entropy: float  # Shannon entropy of data
    temporal_correlation: float  # Correlation with previous data


@dataclass
class StrategyPerformance:
    """Performance metrics for a compression strategy."""
    strategy: CompressionStrategy
    avg_compression_ratio: float
    avg_compression_time: float
    success_rate: float
    total_uses: int
    last_used: float


class PatternAnalyzer:
    """Analyzes data patterns to guide compression strategy selection."""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.pattern_history: deque = deque(maxlen=history_size)
    
    def extract_features(self, manifest: Dict[str, Any], 
                        previous: Optional[Dict[str, Any]] = None) -> PatternFeatures:
        """Extract pattern features from manifest."""
        # Field change rate
        if previous:
            changed_fields = sum(1 for k in manifest.keys() if k in previous and manifest[k] != previous[k])
            field_change_rate = changed_fields / len(manifest)
        else:
            field_change_rate = 1.0  # All fields "changed" (no previous)
        
        # Value variance (simplified)
        values = list(manifest.values())
        if values and isinstance(values[0], (int, float)):
            value_variance = (max(values) - min(values)) / (len(values) or 1)
        else:
            value_variance = 0.5
        
        # Sequence length
        sequence_length = len(json.dumps(manifest))
        
        # Entropy (simplified character distribution)
        manifest_str = json.dumps(manifest)
        char_counts = defaultdict(int)
        for char in manifest_str:
            char_counts[char] += 1
        if manifest_str:
            # Shannon entropy: -sum(p * log2(p))
            import math
            entropy = -sum((count / len(manifest_str)) * math.log2(count / len(manifest_str))
                          for count in char_counts.values())
        else:
            entropy = 0
        
        # Temporal correlation (simplified)
        if previous:
            prev_str = json.dumps(previous)
            common_chars = sum(1 for c in set(manifest_str + prev_str) if c in manifest_str and c in prev_str)
            temporal_correlation = common_chars / len(set(manifest_str + prev_str))
        else:
            temporal_correlation = 0.0
        
        return PatternFeatures(
            field_change_rate=field_change_rate,
            value_variance=value_variance,
            sequence_length=sequence_length,
            entropy=entropy,
            temporal_correlation=temporal_correlation
        )
    
    def predict_best_strategy(self, features: PatternFeatures) -> CompressionStrategy:
        """Predict best compression strategy based on patterns."""
        # Simple heuristic-based strategy selection
        if features.field_change_rate < 0.2:
            # Low change rate: delta encoding very effective
            return CompressionStrategy.DELTA_PTOS
        elif features.temporal_correlation > 0.8:
            # High correlation: delta encoding effective
            return CompressionStrategy.DELTA_GCL
        elif features.entropy < 0.5:
            # Low entropy: GCL compression effective
            return CompressionStrategy.GCL_ONLY
        else:
            # Default: full stack
            return CompressionStrategy.FULL_STACK


class AdaptiveDeltaGCLCompressor:
    """
    Adaptive compression system that learns optimal strategies from data patterns.
    """
    
    def __init__(self):
        self.compression_service = DeltaGCLCompressionService()
        self.pattern_analyzer = PatternAnalyzer()
        self.strategy_performance: Dict[CompressionStrategy, StrategyPerformance] = {}
        self.previous_manifests: Dict[str, Dict[str, Any]] = {}
        self.compression_history: List[Tuple[PatternFeatures, CompressionStrategy, CompressionResult]] = []
    
    def compress_adaptive(self, manifest: Dict[str, Any], 
                         manifest_id: str) -> CompressionResult:
        """
        Compress manifest using adaptive strategy selection.
        """
        # Get previous manifest for pattern analysis
        previous = self.previous_manifests.get(manifest_id)
        
        # Extract pattern features
        features = self.pattern_analyzer.extract_features(manifest, previous)
        
        # Predict best strategy
        strategy = self.pattern_analyzer.predict_best_strategy(features)
        
        # Apply strategy
        result = self._apply_strategy(manifest, manifest_id, strategy, previous)
        
        # Track performance
        self._track_performance(features, strategy, result)
        
        # Store manifest for future delta encoding
        self.previous_manifests[manifest_id] = manifest
        
        return result
    
    def _apply_strategy(self, manifest: Dict[str, Any], manifest_id: str,
                       strategy: CompressionStrategy, 
                       previous: Optional[Dict[str, Any]] = None) -> CompressionResult:
        """Apply specific compression strategy."""
        use_delta = previous is not None
        
        match strategy:
            case CompressionStrategy.DELTA_ONLY:
                # Delta encoding only
                return self.compression_service.compress_manifest(manifest, manifest_id, use_delta=use_delta)
            case CompressionStrategy.PTOS_ONLY:
                # PTOS dictionary only (no delta)
                return self.compression_service.compress_manifest(manifest, manifest_id, use_delta=False)
            case CompressionStrategy.GCL_ONLY:
                # GCL only (no delta, no PTOS)
                # For now, use standard compression
                return self.compression_service.compress_manifest(manifest, manifest_id, use_delta=False)
            case CompressionStrategy.DELTA_PTOS:
                # Delta + PTOS
                return self.compression_service.compress_manifest(manifest, manifest_id, use_delta=use_delta)
            case CompressionStrategy.DELTA_GCL:
                # Delta + GCL
                return self.compression_service.compress_manifest(manifest, manifest_id, use_delta=use_delta)
            case CompressionStrategy.FULL_STACK:
                # Full stack (delta + PTOS + GCL)
                return self.compression_service.compress_manifest(manifest, manifest_id, use_delta=use_delta)
            case CompressionStrategy.ADAPTIVE:
                # Let the service decide
                return self.compression_service.compress_manifest(manifest, manifest_id, use_delta=use_delta)
    
    def _track_performance(self, features: PatternFeatures, 
                          strategy: CompressionStrategy, 
                          result: CompressionResult):
        """Track performance of compression strategies."""
        # Update strategy performance metrics
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = StrategyPerformance(
                strategy=strategy,
                avg_compression_ratio=0.0,
                avg_compression_time=0.0,
                success_rate=1.0,
                total_uses=0,
                last_used=0.0
            )
        
        perf = self.strategy_performance[strategy]
        perf.total_uses += 1
        perf.last_used = datetime.now().timestamp()
        
        # Update average compression ratio
        current_ratio = result.stats["reduction_percent"] / 100
        perf.avg_compression_ratio = (
            (perf.avg_compression_ratio * (perf.total_uses - 1) + current_ratio)
            / perf.total_uses
        )
        
        # Store in history
        self.compression_history.append((features, strategy, result))
        
        # Limit history size
        if len(self.compression_history) > 1000:
            self.compression_history = self.compression_history[-1000:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for all strategies."""
        report = {
            "total_compressions": len(self.compression_history),
            "strategies": {}
        }
        
        for strategy, perf in self.strategy_performance.items():
            report["strategies"][strategy.value] = {
                "avg_compression_ratio": perf.avg_compression_ratio,
                "avg_compression_time": perf.avg_compression_time,
                "success_rate": perf.success_rate,
                "total_uses": perf.total_uses,
                "last_used": perf.last_used
            }
        
        return report
    
    def optimize_strategies(self):
        """Optimize strategy selection based on historical performance."""
        if not self.compression_history:
            return
        
        # Find best performing strategy overall
        best_strategy = max(
            self.strategy_performance.items(),
            key=lambda x: x[1].avg_compression_ratio
        )
        
        print(f"[Adaptive] Best performing strategy: {best_strategy[0].value}")
        print(f"[Adaptive] Average compression ratio: {best_strategy[1].avg_compression_ratio:.2%}")


# Singleton instance
_adaptive_instance: Optional[AdaptiveDeltaGCLCompressor] = None


def get_adaptive_compressor() -> AdaptiveDeltaGCLCompressor:
    """Get singleton adaptive compressor instance."""
    global _adaptive_instance
    if _adaptive_instance is None:
        _adaptive_instance = AdaptiveDeltaGCLCompressor()
    return _adaptive_instance


def compress_adaptive_manifest(manifest: Dict[str, Any], manifest_id: str) -> CompressionResult:
    """Convenience function to compress manifest with adaptive strategy."""
    compressor = get_adaptive_compressor()
    return compressor.compress_adaptive(manifest, manifest_id)


if __name__ == "__main__":
    # Test adaptive compression
    print("=" * 70)
    print("ADAPTIVE DELTA GCL COMPRESSION")
    print("=" * 70)
    
    compressor = AdaptiveDeltaGCLCompressor()
    
    # Create test manifests
    manifest1 = {
        "layer": "CORE",
        "domain": "COMPUTE",
        "tier": "FOAM",
        "condition": "STABLE",
        "data": {"value": 100, "status": "active"}
    }
    
    print("\n[1] Compressing first manifest...")
    result1 = compressor.compress_adaptive(manifest1, "adaptive_test_1")
    print(f"  Compression: {result1.stats['reduction_percent']:.2f}% reduction")
    print(f"  Strategy: Adaptive")
    
    # Second manifest (similar to first - should use delta)
    manifest2 = manifest1.copy()
    manifest2["data"]["value"] = 105
    
    print("\n[2] Compressing second manifest (similar to first)...")
    result2 = compressor.compress_adaptive(manifest2, "adaptive_test_1")
    print(f"  Compression: {result2.stats['reduction_percent']:.2f}% reduction")
    
    # Third manifest (different - should use different strategy)
    manifest3 = {
        "layer": "CARRY",
        "domain": "TOKEN",
        "tier": "PLASMA",
        "condition": "EXPERIMENTAL",
        "data": {"value": 200, "status": "pending", "priority": "high"}
    }
    
    print("\n[3] Compressing third manifest (different)...")
    result3 = compressor.compress_adaptive(manifest3, "adaptive_test_2")
    print(f"  Compression: {result3.stats['reduction_percent']:.2f}% reduction")
    
    # Optimize strategies
    print("\n[4] Optimizing strategies...")
    compressor.optimize_strategies()
    
    # Performance report
    print("\n[5] Performance report...")
    report = compressor.get_performance_report()
    print(f"  Total compressions: {report['total_compressions']}")
    for strategy, metrics in report['strategies'].items():
        print(f"  {strategy}: {metrics['total_uses']} uses, {metrics['avg_compression_ratio']:.2%} avg ratio")
    
    print("\n" + "=" * 70)
    print("ADAPTIVE COMPRESSION OPERATIONAL")
    print("=" * 70)
