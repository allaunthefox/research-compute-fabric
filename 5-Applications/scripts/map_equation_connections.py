import sys
import json
import os
from pathlib import Path

# Add project root to path
sys.path.append("/home/allaun/Research Stack")
from infra.deepseek_adapter import DeepSeekV4

def map_equations():
    # Use local DeepSeek V4 client (which will route through Ollama based on previous context)
    client = DeepSeekV4(use_local=True)
    
    equations_file = "/home/allaun/Documents/Research Stack/data/equations_forest.jsonl"
    equations = []
    with open(equations_file, 'r') as f:
        for line in f:
            if line.strip():
                equations.append(json.loads(line))
                
    eq_summary = ""
    for idx, eq in enumerate(equations):
        eq_summary += f"{idx+1}. Name: {eq['name']}\n   Type: {eq['type']}, Field: {eq.get('street_membership', [])}\n   Formula: {eq['formula']}\n\n"
        
    prompt = f"""
You are a mathematical physicist and systems architect.
Analyze the following equations from the Sovereign Research Stack. 
Determine how EVERY equation mathematically, physically, or topologically connects to the others.
Create a comprehensive mapping showing the dependencies, transformations, or conceptual links between them.
Ensure you connect EVERY equation provided. Format your output as a markdown document with clear headings, bullet points, and a concluding summary.

Equations:
{eq_summary}
"""
    print(f"Sending prompt to DeepSeek V4 with {len(equations)} equations...")
    messages = [{"role": "user", "content": prompt}]
    
    try:
        # User explicitly asked for deepseek v4
        res = client.chat(messages, model="deepseek-v4-pro:cloud")
        content = res["message"]["content"]
    except Exception as e:
        print(f"Error using deepseek-v4-pro:cloud: {e}")
        print("Falling back to deepseek-r1:8b...")
        res = client.chat(messages, model="deepseek-r1:8b")
        content = res["message"]["content"]
        
    output_path = "/home/allaun/Documents/Research Stack/artifacts/equation_connections.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
        
    print(f"Mapping complete. Saved to {output_path}")

if __name__ == "__main__":
    map_equations()
