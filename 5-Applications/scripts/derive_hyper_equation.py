import json
from pathlib import Path
from infra.deepseek_adapter import DeepSeekV4, DeepSeekProver

def derive_hyper_equation():
    client = DeepSeekV4(use_local=True)
    prover = DeepSeekProver(client)
    
    forest_path = Path("/home/allaun/Documents/Research Stack/data/equations_forest.jsonl")
    equations = []
    if forest_path.exists():
        with open(forest_path, "r") as f:
            for line in f:
                equations.append(json.loads(line))
    
    if not equations:
        print("[ERROR] No equations found in forest.")
        return

    eq_list = "\n".join([f"- {eq['name']}: {eq['formula']}" for eq in equations])
    
    prompt = f"""
You are a master mathematical physicist. 
I have a collection of 15 canonical equations from the Sovereign Research Stack:

{eq_list}

Your task:
1. Review all these equations.
2. Derive a single 'Hyper Equation' or 'Unified Manifold Operator' that generalizes these disparate domains (Fluid Dynamics, GR, Neural Lattice, Hardware Encoding).
3. The hyper equation should use a generalized tensor or operator notation that captures the essence of all 15.
4. Provide the formal derivation and the final Hyper Equation in LaTeX.
"""
    
    print("Synthesizing Hyper Equation using DeepSeek-R1 (this may take time)...")
    # Force R1 for deep reasoning
    messages = [{"role": "user", "content": prompt}]
    result = client.chat(messages, model="qwen2.5-coder:14b")
    print("\n--- HYPER EQUATION DERIVATION ---\n")
    content = result['message']['content']
    print(content)
    
    # Save the result to a new artifact
    with open("/home/allaun/Documents/Research Stack/data/hyper_equation.md", "w") as f:
        f.write(content)
    print(f"\n[OK] Hyper Equation saved to /home/allaun/Documents/Research Stack/data/hyper_equation.md")

if __name__ == "__main__":
    derive_hyper_equation()
