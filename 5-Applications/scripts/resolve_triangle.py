import os
import sys
from infra.deepseek_adapter import DeepSeekV4, DeepSeekProver

def resolve_triangle_inequality():
    client = DeepSeekV4(use_local=True)
    prover = DeepSeekProver(client)
    
    context = """
    We are in a Lean 4 environment. 
    Variable (V : Type) [DecidableEq V]
    Structure AdmissibilityGraph where
      edge : V -> V -> Option Score
      edge_symm : ∀ x y, edge x y = edge y x
    
    Definition Path (x y : V) ...
    Definition pathCost (p : Path x y) : Score ...
    Definition shortestPathDist (x y : V) : Score := 
      -- infimum of path costs
    
    Theorem: shortestPathDist_triangle (x y z : V) : 
      shortestPathDist x z ≤ shortestPathDist x y + shortestPathDist y z
    
    The user needs the full proof block using Lean 4.
    """
    
    theorem_code = "theorem shortestPathDist_triangle (x y z : V) : shortestPathDist x z ≤ shortestPathDist x y + shortestPathDist y z"
    
    print("Generating proof for shortestPathDist_triangle...")
    proof = prover.formalize(context + "\n" + theorem_code)
    print("\nProposed Proof:\n", proof)
    return proof

if __name__ == "__main__":
    resolve_triangle_inequality()
