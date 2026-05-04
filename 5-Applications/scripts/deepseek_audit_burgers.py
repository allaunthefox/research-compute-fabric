#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infra.deepseek_adapter import DeepSeekV4

def main():
    client = DeepSeekV4(use_local=True)
    model = "deepseek-r1:8b"
    
    # The "Suspect Equation" from the ENE ingest
    equation = "u_t + u u_x = nu u_{xx} + eta(x,t) - lambda d_x Phi_Omega(x,t)"
    complexity = "Omega[u] = 1/2 sum_{n=1}^N n^2 |a_n|^2"
    
    prompt = f"""
You are a mathematical physicist and formal verification expert. 
I am auditing a "Field-Native Witness Hierarchy" model based on a regularized Burgers' equation.

Equation under audit:
∂u/∂t + u(∂u/∂x) = ν(∂²u/∂x²) + η(x,t) - λ(∂/∂x)Φ_Ω(x,t)

Where the "Complexity Metric" Ω[u] is defined as:
Ω[u] = (1/2) * ∑_{{n=1}}^N n² |a_n|²

The user claims this allows for "Lossless Symbolic Reconstruction" and "Near-Zero Error" in tracking shock wave development.
An earlier AI audit suggested this model has "suspect math" regarding:
1. UV Divergence in the Ω[u] term.
2. Frame anchoring (the exclusion/trap center problem).
3. Convergence claims (errors going to zero).

TASK:
1. Identify the "Suspect Math": Where does this equation likely break down in a real physical or numerical simulation?
2. Formalize the UV Divergence check: If u(x) has a discontinuity (shock), how does Ω[u] behave? 
3. Propose a Lean 4 theorem statement that would verify the "well-posedness" or "energy boundedness" of this system.

Provide your reasoning in thinking tags and then the final audit report.
"""
    
    print(f"--- Auditing Regularized Burgers Equation with {model} ---")
    
    try:
        # Using the streaming support I just added (but I'll handle the output manually here)
        res = client.chat([{"role": "user", "content": prompt}], model=model)
        print("\nAudit Results:")
        print(res["message"]["content"])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
