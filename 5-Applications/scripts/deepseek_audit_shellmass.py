#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infra.deepseek_adapter import DeepSeekV4

def main():
    client = DeepSeekV4(use_local=True)
    
    # We'll use the local R1 model for deep reasoning
    model = "deepseek-r1:8b"
    
    with open(project_root / "0-Core-Formalism/lean/Semantics/Semantics/MassNumberMetricClosure.lean", "r") as f:
        code = f.read()
        
    prompt = f"""
You are a formal verification auditor. I have found "suspect math" in a Lean 4 file.
Specifically, look at §7 "Shell Mass as Throat Curvature (Conjecture 2)".

Definition:
def shellMass (n : Nat) : Nat :=
  let k := Nat.sqrt n
  let a := n - k * k
  let b := (k + 1) * (k + 1) - n
  a * b

The file claims:
theorem shellMass_not_distance :
    ¬ (∀ n m p, shellMass n ≤ shellMass m + shellMass p)
with a comment:
-- Counterexample: shellMass(2) = 2, but shellMass(1) + shellMass(3) = 0 + 0 = 0

Audit the following:
1. Is the comment about shellMass(3)=0 correct? (Check the math).
2. Is the statement of `shellMass_not_distance` mathematically sound? Usually, a distance is a function of two points d(x,y). If shellMass is intended to be a metric on Nat, what would the metric be? Or is it a "mass potential"?
3. Provide the correct Lean 4 proof for `shellMass_max_at_midpoint` and find a TRUE counterexample for the "not a distance" claim if one exists.

File Context:
{code}
"""
    
    print(f"--- Auditing Shell Mass with {model} ---")
    
    try:
        messages = [{"role": "user", "content": prompt}]
        res = client.chat(messages, model=model)
        print("\nAudit Results:")
        print(res["message"]["content"])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
