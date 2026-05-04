#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infra.deepseek_adapter import DeepSeekV4, DeepSeekProver

def main():
    # Note: We are using the Cloud models pulled in Ollama
    # Ollama maps these to its internal API.
    # We will use the 'local' mode in our adapter but point to the cloud-backed tag.
    
    client = DeepSeekV4(use_local=True)
    prover = DeepSeekProver(client)
    
    statement = "The sum of the first n squares is n(n+1)(2n+1)/6."
    print(f"--- Task: Formalizing '{statement}' in Lean 4 ---")
    
    try:
        # Using the cloud reasoning model via Ollama
        # Note: If this fails due to login, we'll suggest the local R1:8b fallback
        code = prover.formalize(statement)
        print("\nGenerated Lean 4 Code:")
        print(code)
    except Exception as e:
        print(f"\nError: {e}")
        print("Note: Ollama Cloud models require 'ollama login'.")
        print("Falling back to local Reasoning model (DeepSeek-R1:8b)...")
        
        # Fallback to local distilled model
        try:
            res = client.chat(
                [{"role": "user", "content": f"Formalize in Lean 4: {statement}"}],
                model="deepseek-r1:8b"
            )
            print("\nGenerated Lean 4 Code (Local R1-Distill):")
            print(res["message"]["content"])
        except Exception as e2:
            print(f"Fallback failed: {e2}")

if __name__ == "__main__":
    main()
