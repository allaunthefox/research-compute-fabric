import os
import json
import csv
import time
import requests
from datetime import datetime

# Path to the data
TSV_PATH = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/MATH_MODEL_MAP.tsv"
OUTPUT_PATH = "/home/allaun/Documents/Research Stack/shared-data/artifacts/preprocessed_equation_connections.jsonl"

def get_newest_model():
    """Return a model that fits in local VRAM (deepseek-r1:8b)"""
    model = "deepseek-r1:8b"
    print(f"Selected viable local model: {model}")
    return model

def query_model(model_name, equation_data):
    """Query the local model for connection mapping"""
    prompt = f"""
You are an expert topological architect for the Sovereign Research Stack.
Analyze the following equation and determine its topological connections to other domains, families, and core primitives (like PIST, Burgers, Tree Fiddy).

Equation Name: {equation_data['Model_Name']}
Family: {equation_data['Family']}
Domain: {equation_data['Domain_Type']}
Bind Class: {equation_data['Bind_Class']}
Purpose: {equation_data['Purpose']}
Formula: {equation_data['Equation']}

Output a valid JSON object with the following schema exactly (no markdown formatting, just JSON):
{{
  "connected_domains": ["list", "of", "domains"],
  "parent_hubs": ["list", "of", "hub", "equations"],
  "structural_role": "brief description of how it connects"
}}
"""
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json" # Force JSON output if supported
            }
        )
        if resp.status_code == 200:
            content = resp.json().get("response", "")
            try:
                # Some models might still wrap in markdown or return extra text
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:-3]
                return json.loads(content)
            except:
                return {"error": "Failed to parse JSON", "raw": content}
    except Exception as e:
        return {"error": str(e)}
        
    return {"error": "Unknown error"}

def main():
    model_name = get_newest_model()
    
    # Load equations
    equations = []
    with open(TSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row.get("Model_Name"):
                equations.append(row)
                
    print(f"Loaded {len(equations)} equations to preprocess.")
    
    # Track existing progress to allow resuming
    processed = set()
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    processed.add(data.get("Model_Name"))
                    
    print(f"Already processed: {len(processed)}")
    
    # Process equations
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    with open(OUTPUT_PATH, 'a', encoding='utf-8') as f:
        for i, eq in enumerate(equations):
            name = eq.get("Model_Name")
            if name in processed:
                continue
                
            print(f"[{i+1}/{len(equations)}] Preprocessing {name}...")
            
            result = query_model(model_name, eq)
            
            # Combine original data with new topological data
            out_data = {
                "Model_Name": name,
                "Family": eq.get("Family"),
                "connections": result,
                "timestamp": datetime.now().isoformat(),
                "model_used": model_name
            }
            
            f.write(json.dumps(out_data) + '\n')
            f.flush()
            
            # Rate limiting / cooling to prevent local GPU overheating
            time.sleep(1)

if __name__ == "__main__":
    main()
