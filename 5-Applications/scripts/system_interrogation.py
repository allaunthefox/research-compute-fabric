import os
import sys
import re

def audit_lean():
    print("--- LEAN 4 AUDIT ---")
    lean_dir = "/home/allaun/Documents/Research Stack/tools/lean"
    sorry_count = 0
    for root, _, files in os.walk(lean_dir):
        for file in files:
            if file.endswith(".lean"):
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    content = f.read()
                    matches = re.findall(r"sorry", content)
                    if matches:
                        print(f"[SORRY] {os.path.relpath(path, lean_dir)}: {len(matches)} occurrences")
                        sorry_count += len(matches)
    print(f"Total 'sorry' blocks: {sorry_count}")
    return sorry_count

def audit_python_math():
    print("\n--- PYTHON PHYSICS AUDIT ---")
    scripts_dir = "/home/allaun/Documents/Research Stack/scratch/exploit_recovery/5-Applications/tools-scripts/physics"
    spectral_core = "/home/allaun/Documents/Research Stack/scratch/exploit_recovery/5-Applications/tools-scripts/physics/usc_spectral_core.py"
    
    # Check for tapered regularization
    with open(spectral_core, "r") as f:
        content = f.read()
        if "burgers_complexity_metric" in content and "epsilon" in content:
            print("[OK] usc_spectral_core.py: Tapered regularization implemented.")
        else:
            print("[WARN] usc_spectral_core.py: Tapered regularization MISSING or incomplete.")
            
    # Check other scripts for nu_eff or Omega
    for root, _, files in os.walk(scripts_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    content = f.read()
                    if "nu_eff" in content and "epsilon" not in content:
                        print(f"[SUSPECT] {os.path.relpath(path, scripts_dir)}: nu_eff used without explicit epsilon regularization.")

def audit_mcp_config():
    print("\n--- MCP CONFIG AUDIT ---")
    config_path = "/home/allaun/.gemini/antigravity/mcp_config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            content = f.read()
            if "YOUR_BRAVE_API_KEY_HERE" in content:
                print("[WARN] mcp_config.json: Brave Search API key is still the placeholder.")
            if "google-surf-mcp" in content:
                print("[OK] mcp_config.json: google-surf-mcp configured.")
    else:
        print("[FAIL] mcp_config.json not found.")

def audit_env():
    print("\n--- ENVIRONMENT AUDIT ---")
    env_path = "/home/allaun/Documents/Research Stack/.env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
            if "DEEPSEEK_API_KEY" not in content:
                print("[WARN] .env: DEEPSEEK_API_KEY is missing. Cloud Pro mode will fail.")
            if "LINEAR_API_KEY=your_linear_api_key_here" in content:
                print("[WARN] .env: Linear API key is a placeholder.")
    else:
        print("[FAIL] .env file not found.")

if __name__ == "__main__":
    print("SOVEREIGN RESEARCH STACK - SYSTEM INTERROGATION")
    print("===============================================")
    audit_lean()
    audit_python_math()
    audit_mcp_config()
    audit_env()
    print("\nInterrogation complete.")
