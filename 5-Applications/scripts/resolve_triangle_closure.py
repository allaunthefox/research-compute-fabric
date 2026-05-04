import os
import sys
from infra.deepseek_adapter import DeepSeekV4, DeepSeekProver

def resolve_triangle_closure():
    client = DeepSeekV4(use_local=True)
    prover = DeepSeekProver(client)
    
    # Provide the actual code from the library for context
    context = """
    import Semantics.RealityContractMassNumber
    namespace HolyDiver.ENE

    structure AdmissibilityEdge where
      u     : CandidateRecord
      v     : CandidateRecord
      cost  : Score
      symm  : cost = cost

    def Path := List AdmissibilityEdge

    def pathCost (p : Path) : Score :=
      p.foldl (fun acc e => acc.add e.cost) { num := 0, den := 1, den_ne := by simp }

    def is_path (g : AdmissibilityGraph) (x y : CandidateRecord) (p : Path) : Prop :=
      match p with
      | [] => x = y
      | [e] => e.u = x ∧ e.v = y ∧ e ∈ g.edges ∧ edgeAdmissible g e
      | e :: es => e.u = x ∧ e ∈ g.edges ∧ edgeAdmissible g e ∧ is_path g e.v y es

    def allPaths (g : AdmissibilityGraph) (x y : CandidateRecord) : Set Path :=
      {p | is_path g x y p}

    def shortestPathDist (g : AdmissibilityGraph) (x y : CandidateRecord) : Score :=
      -- We assume a well-defined infimum of pathCosts for all p in allPaths g x y
      -- For this proof, just use the property: 
      -- for any p such that is_path g x y p, shortestPathDist g x y ≤ pathCost p

    Theorem to prove:
    theorem shortestPathDist_triangle (g : AdmissibilityGraph) (x y z : CandidateRecord) :
      Score.le (shortestPathDist g x z) ((shortestPathDist g x y).add (shortestPathDist g y z))
    
    Hint: If p1 is a path from x to y and p2 is a path from y to z, 
    then p1 ++ p2 is a path from x to z. 
    And pathCost (p1 ++ p2) = (pathCost p1).add (pathCost p2).
    Since shortestPathDist x z is the infimum, it must be ≤ pathCost (p1 ++ p2).
    """
    
    print("Generating proof for shortestPathDist_triangle...")
    proof = prover.formalize(context)
    print("\nProposed Proof:\n", proof)
    return proof

if __name__ == "__main__":
    resolve_triangle_closure()
