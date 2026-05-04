import os
import sys
import json
import requests
from typing import List, Dict

# DeepSeek API Configuration
API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/v1/chat/completions"

def solve_lean_goal(prompt: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "model": "deepseek-chat", # Using V3/V4 Pro
        "messages": [
            {"role": "system", "content": "You are a Lean 4 formalization expert. Your task is to provide the proof script for a specific Lean 4 goal. Use the provided context and ensure the proof is complete and valid. Output ONLY the proof script enclosed in ```lean ... ``` blocks."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    response = requests.post(API_URL, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]

# Context for the solver
CONTEXT = """
import Semantics.RealityContractMassNumber
namespace HolyDiver.ENE

/-- Score addition (cross-multiplying to common denominator). -/
def Score.add (a b : Score) : Score :=
  { num := a.num * b.den + b.num * a.den,
    den := a.den * b.den,
    den_ne := by
      apply Nat.mul_ne_zero
      · exact a.den_ne
      · exact b.den_ne }

/-- Score addition is commutative. -/
theorem Score.add_comm (a b : Score) : a.add b = b.add a := by
  unfold Score.add
  simp
  rw [Nat.add_comm, Nat.mul_comm]
  congr 1
  rw [Nat.mul_comm]

/-- Score addition is associative. -/
theorem Score.add_assoc (a b c : Score) : (a.add b).add c = a.add (b.add c) := by
  unfold Score.add
  simp
  constructor
  · ring
  · ring

/-- Structure for Metric Closure -/
structure AdmissibilityEdge where
  u     : CandidateRecord
  v     : CandidateRecord
  cost  : Score
  symm  : cost = cost

def Path := List AdmissibilityEdge

def pathCost (p : Path) : Score :=
  p.foldl (fun acc e => acc.add e.cost)
    { num := 0, den := 1, den_ne := by simp }

/-- Reversing an edge swaps endpoints and preserves cost. -/
def AdmissibilityEdge.reverse (e : AdmissibilityEdge) : AdmissibilityEdge :=
  { u := e.v, v := e.u, cost := e.cost, symm := rfl }

def Path.reversePath (p : Path) : Path :=
  p.reverse.map AdmissibilityEdge.reverse
"""

GOALS = [
    {
        "id": "foldl_add_reverse",
        "goal": "theorem foldl_add_reverse (l : List Score) (init : Score) :\n    l.reverse.foldl Score.add init = l.foldl Score.add init",
        "hint": "Use induction on l. You'll need a helper lemma that foldl add (init.add x) xs = (foldl add init xs).add x which follows from associativity."
    },
    {
        "id": "pathCost_reverse",
        "goal": "theorem pathCost_reverse (p : Path) : pathCost (p.reversePath) = pathCost p",
        "hint": "Use foldl_add_reverse and the fact that AdmissibilityEdge.reverse.cost = e.cost."
    },
    {
        "id": "shellMass_max_at_midpoint",
        "goal": "theorem shellMass_max_at_midpoint (k : Nat) :\n    let n := k * k + k\n    shellMass n = k * (k + 1)",
        "hint": "unfold shellMass and use the fact that Nat.sqrt (k*k + k) = k for k > 0. Then simplify a = (k*k+k) - k*k and b = (k+1)^2 - (k*k+k)."
    }
]

def main():
    if not API_KEY:
        print("Error: DEEPSEEK_API_KEY not set.")
        sys.exit(1)

    results = {}
    for g in GOALS:
        print(f"Solving {g['id']}...")
        prompt = f"Context:\n{CONTEXT}\n\nGoal:\n{g['goal']}\n\nHint: {g['hint']}\n\nProvide the complete proof script."
        proof = solve_lean_goal(prompt)
        results[g['id']] = proof
        print(f"Result for {g['id']}:\n{proof}\n")

    with open("/home/allaun/Documents/Research Stack/scratch/mass_number_proofs.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
