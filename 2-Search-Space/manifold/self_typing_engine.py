#!/usr/bin/env python3
"""
Self-Typing Engine — Metatype Generation
First-Principles Derivation: Self-typing via integration (type emerges from interaction)

The self-typing loop:
Substrate (ENE) ↔ Surface (Notion) ↔ Intent (Linear) ⟹ Metatype

Performance Targets:
- Automatic type inference from interaction patterns
- Cached type predictions
- GPU-accelerated pattern matching
- Hierarchical type classification
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from collections import defaultdict


class InteractionType(Enum):
    """Types of interactions between layers"""
    SUBSTRATE_TO_SURFACE = "substrate_to_surface"
    SURFACE_TO_SUBSTRATE = "surface_to_substrate"
    SURFACE_TO_INTENT = "surface_to_intent"
    INTENT_TO_SURFACE = "intent_to_surface"
    SUBSTRATE_TO_INTENT = "substrate_to_intent"
    INTENT_TO_SUBSTRATE = "intent_to_substrate"


@dataclass
class Interaction:
    """Interaction event between layers"""
    interaction_id: str
    interaction_type: InteractionType
    source_layer: str
    target_layer: str
    timestamp: datetime
    context: Dict[str, str]  # Additional context (e.g., operation type, data size)
    
    def __repr__(self) -> str:
        return f"Interaction({self.interaction_type.value}, {self.source_layer} → {self.target_layer})"


@dataclass
class Metatype:
    """Emergent type from integration of layers"""
    metatype_id: str
    type_signature: str  # Type signature derived from interactions
    confidence: float  # Confidence in type inference
    source_interactions: List[str]  # Interaction IDs that contributed to this type
    suggestions: List[str]  # Type suggestions based on neighborhood
    created_at: datetime = field(default_factory=datetime.now)
    
    def __repr__(self) -> str:
        return f"Metatype({self.type_signature}, confidence={self.confidence:.3f})"


class SelfTypingEngine:
    """
    Self-Typing Engine — Metatype Generation
    
    System derives type signature from interaction between layers
    """
    
    def __init__(self):
        self.interactions: List[Interaction] = []
        self.interaction_counter = 0
        self.metatypes: Dict[str, Metatype] = {}
        self.metatype_counter = 0
        self.interaction_patterns: Dict[str, int] = defaultdict(int)
        self.type_cache: Dict[str, Metatype] = {}
    
    def record_interaction(
        self,
        interaction_type: InteractionType,
        source_layer: str,
        target_layer: str,
        context: Optional[Dict[str, str]] = None
    ) -> Interaction:
        """
        Record interaction between layers
        
        Args:
            interaction_type: Type of interaction
            source_layer: Source layer name
            target_layer: Target layer name
            context: Additional context
            
        Returns:
            Interaction record
        """
        self.interaction_counter += 1
        interaction_id = f"interaction_{self.interaction_counter}"
        
        if context is None:
            context = {}
        
        interaction = Interaction(
            interaction_id=interaction_id,
            interaction_type=interaction_type,
            source_layer=source_layer,
            target_layer=target_layer,
            timestamp=datetime.now(),
            context=context
        )
        
        self.interactions.append(interaction)
        
        # Update interaction patterns
        pattern_key = f"{interaction_type.value}:{source_layer}:{target_layer}"
        self.interaction_patterns[pattern_key] += 1
        
        # Invalidate cache
        self.type_cache.clear()
        
        return interaction
    
    def infer_metatype(self, context: Dict[str, str]) -> Metatype:
        """
        Infer metatype from interaction patterns
        
        Args:
            context: Current context (layer names, operation types, etc.)
            
        Returns:
            Inferred metatype
        """
        # Check cache first
        cache_key = self._context_to_key(context)
        if cache_key in self.type_cache:
            return self.type_cache[cache_key]
        
        # Extract interaction pattern
        pattern = self._extract_pattern(context)
        
        # Generate type signature
        type_signature = self._generate_type_signature(pattern)
        
        # Compute confidence based on pattern frequency
        confidence = self._compute_confidence(pattern)
        
        # Get type suggestions from neighborhood
        suggestions = self._get_type_suggestions(pattern)
        
        # Create metatype
        self.metatype_counter += 1
        metatype_id = f"metatype_{self.metatype_counter}"
        
        metatype = Metatype(
            metatype_id=metatype_id,
            type_signature=type_signature,
            confidence=confidence,
            source_interactions=[i.interaction_id for i in self.interactions[-10:]],  # Last 10 interactions
            suggestions=suggestions
        )
        
        self.metatypes[metatype_id] = metatype
        self.type_cache[cache_key] = metatype
        
        return metatype
    
    def _context_to_key(self, context: Dict[str, str]) -> str:
        """Convert context to cache key"""
        items = sorted(context.items())
        return "|".join(f"{k}:{v}" for k, v in items)
    
    def _extract_pattern(self, context: Dict[str, str]) -> Dict[str, str]:
        """Extract interaction pattern from context"""
        pattern = {}
        
        # Extract relevant context fields
        for key in ["operation", "data_type", "layer", "action"]:
            if key in context:
                pattern[key] = context[key]
        
        return pattern
    
    def _generate_type_signature(self, pattern: Dict[str, str]) -> str:
        """
        Generate type signature from pattern
        
        Args:
            pattern: Interaction pattern
            
        Returns:
            Type signature string
        """
        # Build signature from pattern components
        components = []
        
        if "operation" in pattern:
            components.append(f"op:{pattern['operation']}")
        if "data_type" in pattern:
            components.append(f"dt:{pattern['data_type']}")
        if "layer" in pattern:
            components.append(f"lyr:{pattern['layer']}")
        if "action" in pattern:
            components.append(f"act:{pattern['action']}")
        
        # If no components, use default
        if not components:
            components = ["generic"]
        
        signature = ":".join(components)
        
        return signature
    
    def _compute_confidence(self, pattern: Dict[str, str]) -> float:
        """
        Compute confidence based on pattern frequency
        
        Args:
            pattern: Interaction pattern
            
        Returns:
            Confidence score (0-1)
        """
        # Build pattern key
        pattern_key = self._pattern_to_key(pattern)
        
        # Get pattern frequency
        frequency = self.interaction_patterns.get(pattern_key, 0)
        
        # Normalize to confidence (max frequency = 100)
        confidence = min(frequency / 100.0, 1.0)
        
        return confidence
    
    def _pattern_to_key(self, pattern: Dict[str, str]) -> str:
        """Convert pattern to key for frequency lookup"""
        items = sorted(pattern.items())
        return "|".join(f"{k}:{v}" for k, v in items)
    
    def _get_type_suggestions(self, pattern: Dict[str, str]) -> List[str]:
        """
        Get type suggestions based on manifold neighborhood
        
        Args:
            pattern: Interaction pattern
            
        Returns:
            List of type suggestions
        """
        suggestions = []
        
        # Find similar patterns in interaction history
        pattern_key = self._pattern_to_key(pattern)
        
        # Look for patterns with similar keys
        for key in self.interaction_patterns:
            similarity = self._pattern_similarity(pattern_key, key)
            if similarity > 0.5:  # Similarity threshold
                suggestions.append(key)
        
        return suggestions[:5]  # Top 5 suggestions
    
    def _pattern_similarity(self, key1: str, key2: str) -> float:
        """
        Compute similarity between pattern keys
        
        Args:
            key1: First pattern key
            key2: Second pattern key
            
        Returns:
            Similarity score (0-1)
        """
        # Split keys into components
        components1 = set(key1.split("|"))
        components2 = set(key2.split("|"))
        
        # Jaccard similarity
        intersection = components1 & components2
        union = components1 | components2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def get_interaction_history(self, limit: int = 100) -> List[Interaction]:
        """Get recent interaction history"""
        return self.interactions[-limit:]
    
    def get_type_statistics(self) -> Dict:
        """Get statistics about type inference"""
        return {
            "total_interactions": len(self.interactions),
            "unique_patterns": len(self.interaction_patterns),
            "total_metatypes": len(self.metatypes),
            "cache_size": len(self.type_cache)
        }


def main():
    """Test self-typing engine with sample interactions"""
    engine = SelfTypingEngine()
    
    # Record some interactions
    interaction1 = engine.record_interaction(
        InteractionType.SUBSTRATE_TO_SURFACE,
        "ENE",
        "Notion",
        {"operation": "read", "data_type": "concept_vector"}
    )
    print(f"Recorded interaction: {interaction1}")
    
    interaction2 = engine.record_interaction(
        InteractionType.SURFACE_TO_INTENT,
        "Notion",
        "Linear",
        {"operation": "update", "data_type": "task"}
    )
    print(f"Recorded interaction: {interaction2}")
    
    # Infer metatype from context
    context = {"operation": "read", "data_type": "concept_vector", "layer": "ENE"}
    metatype = engine.infer_metatype(context)
    print(f"Inferred metatype: {metatype}")
    
    # Get statistics
    stats = engine.get_type_statistics()
    print(f"Type statistics: {stats}")


if __name__ == "__main__":
    main()
