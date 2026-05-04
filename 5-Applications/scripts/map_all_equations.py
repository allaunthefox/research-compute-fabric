import sys
import json
import os
import csv
from pathlib import Path

# Add project root to path
sys.path.append("/home/allaun/Research Stack")
from infra.deepseek_adapter import DeepSeekV4

def map_all_equations():
    client = DeepSeekV4(use_local=True)
    
    equations_file = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/MATH_MODEL_MAP.tsv"
    
    equations = []
    with open(equations_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            equations.append({
                "name": row.get("Model_Name", ""),
                "family": row.get("Family", ""),
                "domain": row.get("Domain_Type", ""),
                "bind": row.get("Bind_Class", ""),
            })
            
    # Compress the list to just essential info to fit in context
    # format: Name [Family/Domain]
    eq_summary = []
    for eq in equations:
        eq_summary.append(f"{eq['name']} [{eq['family']}/{eq['domain']}]")
        
    eq_text = "\n".join(eq_summary)
    
    print(f"Total equations loaded: {len(equations)}")
    print(f"Total prompt length (chars): {len(eq_text)}")
    
    prompt = f"""
You are a mathematical physicist and systems architect.
I am providing you with the names and domains of EVERY equation ({len(equations)} in total) from the Sovereign Research Stack, including core primitives like PIST, Tree Fiddy, BHOCS, and more.

Your task is to analyze this massive corpus and find where EVERY equation connects to the grand unified topology.
Since there are too many to list 1-by-1, you must:
1. Identify the central HUB equations (the most fundamental roots, e.g., PIST, Tree Fiddy, RGFlow, Burgers).
2. Trace the major pathways: How do the physics equations connect to the topological and informational (neural) equations?
3. Synthesize the Grand Unified Topology of this research stack based on the families and domains provided.

Provide a comprehensive markdown report.

Equation List:
{eq_text}
"""
    print("Sending prompt to DeepSeek V4...")
    messages = [{"role": "user", "content": prompt}]
    
    try:
        # User explicitly asked for deepseek v4
        res = client.chat(messages, model="deepseek-v4-pro:cloud")
        content = res["message"]["content"]
    except Exception as e:
        print(f"Error using deepseek-v4-pro:cloud: {e}")
        print("Falling back to deepseek-r1:32b...")
        try:
            res = client.chat(messages, model="deepseek-r1:32b")
            content = res["message"]["content"]
        except:
            print("Falling back to deepseek-r1:8b...")
            res = client.chat(messages, model="deepseek-r1:8b")
            content = res["message"]["content"]
        
    output_path = "/home/allaun/Documents/Research Stack/artifacts/master_equation_topology.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
        
    print(f"Mapping complete. Saved to {output_path}")

if __name__ == "__main__":
    map_all_equations()
