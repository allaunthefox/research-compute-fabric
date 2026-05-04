import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append("/home/allaun/Research Stack")
from infra.deepseek_adapter import DeepSeekV4

def solve_famm_sorry():
    # Use DeepSeek API for better reliability
    api_key = "sk-62e23a21b1054ae2986b97876e5c1265"
    client = DeepSeekV4(api_key=api_key, use_local=False)
    model = "deepseek-v4-pro"
    
    file_path = "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/FAMM.lean"
    with open(file_path, 'r') as f:
        content = f.read()
        
    prompt = f"""
You are a Lean 4 formalization expert.
The following Lean 4 file `FAMM.lean` has duplicate definitions and 'sorry' axioms.
Please refactor it to:
1. Remove duplicate structures and definitions (e.g., FAMMThermalBank, fammMetadataCollapse).
2. Complete the proof for `famm_compression_property`.
3. Ensure the file is valid Lean 4 code.

File Content:
{content}

Provide the complete refactored file content in a code block.
"""

    print(f"Sending request to {model}...")
    messages = [{"role": "user", "content": prompt}]
    
    try:
        res = client.chat(messages, model=model)
        # Check if it's Ollama response format
        if "message" in res:
            new_content = res["message"]["content"]
        else:
            new_content = res["choices"][0]["message"]["content"]
            
        # Extract from code block
        if "```lean" in new_content:
            new_content = new_content.split("```lean")[1].split("```")[0].strip()
        elif "```" in new_content:
            new_content = new_content.split("```")[1].split("```")[0].strip()
            
        output_path = "/home/allaun/Documents/Research Stack/scratch/FAMM_refactored.lean"
        with open(output_path, 'w') as f:
            f.write(new_content)
        print(f"Refactored file saved to {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    solve_famm_sorry()
