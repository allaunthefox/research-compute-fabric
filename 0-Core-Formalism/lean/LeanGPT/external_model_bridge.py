#!/usr/bin/env python3
"""
External Model Validation Bridge

Routes our Lean-verified equations through external math models
for independent peer review.

Architecture:
- Lean = Ground truth (AGENTS.md §0)
- External models = Peer reviewers (additional validation layer)
- Final decision = Triumvirate consensus
"""

import subprocess
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ModelProvider(Enum):
    QWEN2_MATH = "qwen2-math"
    NUMINA_MATH = "numinamath"
    LLEMMA = "llemma"
    METAMATH = "metamath"


@dataclass
class ExternalValidation:
    """Result from external model validation."""
    model: str
    verdict: str  # "valid", "invalid", "uncertain"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    physical_consistency: Optional[bool] = None
    mathematical_soundness: Optional[bool] = None
    concerns: List[str] = None


class ExternalModelBridge:
    """
    Bridge to external math models for peer review.
    
    IMPORTANT: These models are VALIDATORS ONLY.
    Lean remains the source of truth per AGENTS.md.
    """
    
    def __init__(self):
        self.models = [
            ModelProvider.QWEN2_MATH,
            ModelProvider.NUMINA_MATH,
            ModelProvider.LLEMMA,
            ModelProvider.METAMATH
        ]
        
    def _call_model(self, model: ModelProvider, equation: str, 
                    context: Dict) -> ExternalValidation:
        """
        Call external model for validation.
        
        NOTE: These are subprocess calls to locally-running models.
        No external API calls. Models must be self-hosted.
        """
        
        # Construct validation prompt
        prompt = f"""
You are a mathematical validator. Review this equation for physical consistency.

EQUATION: {equation}

CONTEXT:
- Proposed as universal field equation for information-thermodynamics
- Must respect Landauer Principle: E_min = k_B T ln N (cost increases with N)
- Must be thermodynamically consistent
- Must not violate Shannon entropy bounds

VALIDATION TASK:
1. Check if equation respects Landauer scaling (cost ∝ ln N, not 1/ln N)
2. Check mathematical soundness
3. Check physical consistency
4. Identify any concerns or violations

Respond in JSON format:
{{
    "verdict": "valid" | "invalid" | "uncertain",
    "confidence": 0.0-1.0,
    "physical_consistency": true/false,
    "mathematical_soundness": true/false,
    "reasoning": "explanation",
    "concerns": ["list of issues"]
}}
"""
        
        try:
            # Attempt to call local model instance
            # Models should be running as local services
            result = self._query_local_model(model, prompt)
            return self._parse_response(model, result)
            
        except Exception as e:
            # If model unavailable, return uncertain
            return ExternalValidation(
                model=model.value,
                verdict="uncertain",
                confidence=0.0,
                reasoning=f"Model unavailable: {str(e)}",
                physical_consistency=None,
                mathematical_soundness=None,
                concerns=["Model not accessible for validation"]
            )
    
    def _query_local_model(self, model: ModelProvider, prompt: str) -> str:
        """Query locally-hosted model."""
        
        # Map models to local endpoints
        endpoints = {
            ModelProvider.QWEN2_MATH: "http://localhost:8001/v1/chat/completions",
            ModelProvider.NUMINA_MATH: "http://localhost:8002/v1/chat/completions",
            ModelProvider.LLEMMA: "http://localhost:8003/v1/chat/completions",
            ModelProvider.METAMATH: "http://localhost:8004/v1/chat/completions"
        }
        
        endpoint = endpoints.get(model)
        if not endpoint:
            raise ValueError(f"No endpoint configured for {model}")
        
        # Use curl for subprocess call (no external dependencies)
        cmd = [
            "curl", "-s", "-X", "POST", endpoint,
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": model.value,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,  # Deterministic for validation
                "max_tokens": 500
            })
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise RuntimeError(f"Model query failed: {result.stderr}")
        
        return result.stdout
    
    def _parse_response(self, model: ModelProvider, response: str) -> ExternalValidation:
        """Parse model response into structured validation."""
        
        try:
            data = json.loads(response)
            
            # Extract content from typical API response
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
            else:
                content = response
            
            # Try to parse JSON from content
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, treat as uncertain
                return ExternalValidation(
                    model=model.value,
                    verdict="uncertain",
                    confidence=0.0,
                    reasoning=f"Could not parse structured response: {content[:200]}",
                    concerns=["Unparseable model output"]
                )
            
            return ExternalValidation(
                model=model.value,
                verdict=result.get("verdict", "uncertain"),
                confidence=result.get("confidence", 0.0),
                reasoning=result.get("reasoning", "No reasoning provided"),
                physical_consistency=result.get("physical_consistency"),
                mathematical_soundness=result.get("mathematical_soundness"),
                concerns=result.get("concerns", [])
            )
            
        except Exception as e:
            return ExternalValidation(
                model=model.value,
                verdict="uncertain",
                confidence=0.0,
                reasoning=f"Parse error: {str(e)}",
                concerns=["Response parsing failed"]
            )
    
    def peer_review(self, equation: str, lean_verdict: Dict,
                    proposer: str = "Unknown") -> Dict:
        """
        Get peer review from external models.
        
        This is ADDITIONAL VALIDATION ONLY.
        Lean remains the ground truth per AGENTS.md §0.
        """
        
        print("="*70)
        print("EXTERNAL MODEL PEER REVIEW")
        print("="*70)
        print(f"\nEquation: {equation}")
        print(f"Proposer: {proposer}")
        print(f"\nLean Verdict: {'✅ VALID' if lean_verdict.get('valid') else '❌ INVALID'}")
        print()
        
        # Get validation from each model
        reviews = []
        for model in self.models:
            print(f"Querying {model.value}...")
            review = self._call_model(model, equation, lean_verdict)
            reviews.append(review)
            
            # Print verdict
            status = "✅" if review.verdict == "valid" else "❌" if review.verdict == "invalid" else "❓"
            print(f"  {status} {model.value}: {review.verdict.upper()} (confidence: {review.confidence:.0%})")
            if review.concerns:
                for c in review.concerns[:2]:  # Show top 2 concerns
                    print(f"     ⚠️  {c}")
        
        # Aggregate results
        valid_count = sum(1 for r in reviews if r.verdict == "valid")
        invalid_count = sum(1 for r in reviews if r.verdict == "invalid")
        uncertain_count = len(reviews) - valid_count - invalid_count
        
        print()
        print("-"*70)
        print("PEER REVIEW SUMMARY")
        print("-"*70)
        print(f"  ✅ Valid: {valid_count}/{len(reviews)}")
        print(f"  ❌ Invalid: {invalid_count}/{len(reviews)}")
        print(f"  ❓ Uncertain: {uncertain_count}/{len(reviews)}")
        
        # Consensus logic
        if invalid_count >= 2:
            peer_consensus = "REJECTED_BY_PEERS"
            recommendation = "External models independently found issues. High confidence rejection."
        elif valid_count >= 3:
            peer_consensus = "VALIDATED_BY_PEERS"
            recommendation = "Strong independent validation from multiple models."
        elif valid_count >= 2 and invalid_count == 0:
            peer_consensus = "WEAKLY_VALIDATED"
            recommendation = "Some validation, but uncertainty remains."
        else:
            peer_consensus = "INCONCLUSIVE"
            recommendation = "Peer review is split or uncertain."
        
        print()
        print(f"Peer Consensus: {peer_consensus}")
        print(f"Recommendation: {recommendation}")
        
        # Triumvirate decision matrix
        print()
        print("-"*70)
        print("TRIUMVIRATE DECISION MATRIX")
        print("-"*70)
        print(f"  Lean Verdict:       {'✅ VALID' if lean_verdict.get('valid') else '❌ INVALID'}")
        print(f"  Peer Consensus:     {peer_consensus}")
        print()
        
        # Final recommendation
        if lean_verdict.get('valid') and peer_consensus.startswith("VALIDATED"):
            final = "✅ ACCEPT — Both Lean and peers validate"
        elif not lean_verdict.get('valid') or peer_consensus.startswith("REJECTED"):
            final = "❌ REJECT — Found invalid by ground truth or peers"
        elif lean_verdict.get('valid') and peer_consensus == "INCONCLUSIVE":
            final = "⚠️  CONDITIONAL — Lean validates but peers uncertain"
        else:
            final = "🔄 REVIEW — Mixed signals require human adjudication"
        
        print(f"Final Recommendation: {final}")
        print()
        print("="*70)
        
        return {
            'equation': equation,
            'lean_verdict': lean_verdict,
            'peer_reviews': [self._review_to_dict(r) for r in reviews],
            'peer_consensus': peer_consensus,
            'recommendation': recommendation,
            'final_adjudication': final
        }
    
    def _review_to_dict(self, review: ExternalValidation) -> Dict:
        """Convert review to dictionary."""
        return {
            'model': review.model,
            'verdict': review.verdict,
            'confidence': review.confidence,
            'reasoning': review.reasoning,
            'physical_consistency': review.physical_consistency,
            'mathematical_soundness': review.mathematical_soundness,
            'concerns': review.concerns or []
        }


def main():
    """Demonstrate external model bridge."""
    
    bridge = ExternalModelBridge()
    
    test_cases = [
        {
            'equation': 'Φ = Σ w·lnN - Σ v·lnN',
            'lean_verdict': {'valid': True, 'reason': 'Landauer compliant'},
            'proposer': 'Builder'
        },
        {
            'equation': 'Φ = Σ w/lnN + Σ v/lnN',
            'lean_verdict': {'valid': False, 'reason': 'Inverted Landauer'},
            'proposer': 'Old_Code'
        }
    ]
    
    for test in test_cases:
        result = bridge.peer_review(
            test['equation'],
            test['lean_verdict'],
            test['proposer']
        )
        print("\n")


if __name__ == '__main__':
    main()
