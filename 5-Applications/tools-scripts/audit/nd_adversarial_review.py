#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
import sys
from pathlib import Path

# PERSONAS from nd_gauntlet_live.html
PERSONAS = {
    "DR_NULL": {
        "name": "Dr. Null",
        "role": "Computational physicist",
        "catch": '"Your epsilon is showing."',
        "focus": ["dimensional analysis", "units", "thermodynamic consistency", "equation errors"]
    },
    "DR_ENTROPY": {
        "name": "Dr. Entropy",
        "role": "Thermodynamicist",
        "catch": '"Where does the entropy GO?"',
        "focus": ["entropy budget", "Landauer limit", "hidden entropy export", "reservoir accounting"]
    },
    "DR_IMPL": {
        "name": "Dr. Impl",
        "role": "MEMS experimentalist",
        "catch": '"What\'s your ACTUAL Q at 300K?"',
        "focus": ["fabrication tolerances", "thermal noise", "Q factor", "real-world break points"]
    },
    "DR_PROOFS": {
        "name": "Dr. Proofs",
        "role": "Formal mathematician",
        "catch": '"That\'s a wish with arrows."',
        "focus": ["unstated assumptions", "missing lemmas", "formal proof logic", "mathematical rigor"]
    },
    "DR_COHERENCE": {
        "name": "Dr. Coherence",
        "role": "QEC specialist",
        "catch": '"Room temperature. Always."',
        "focus": ["decoherence time", "phonon bath", "EM coupling", "measurement backaction"]
    }
}

def generate_adversarial_prompt(filename: str, code: str, persona_id: str) -> str:
    p = PERSONAS[persona_id]
    prompt = f"""You are {p['name']} — {p['role']}. My catchphrase is {p['catch']}.
I am reviewing a piece of code from ProofMode (Android) for non-obvious security exploits in N-Dimensional semantic space.

My specific focus: {', '.join(p['focus'])}

FILE: {filename}
CODE:
{code}

I must find the 'exploits' that a regular human auditor would miss. I'm looking for 'blind spots' where the code's structural entropy or magnetization deviates from the AETHER_floor (0.5).

I respond ONLY with valid JSON in this format:
{{
  "verdict": "REJECT" | "MAJOR_REVISION" | "MINOR_REVISION" | "ACCEPT",
  "score": -3 to 2,
  "one_liner": "A brutal one-liner from my persona",
  "detailed_review": "Deep technical critique focused on my specialty",
  "fatal_flaw": "The specific non-obvious exploit or structural weakness found",
  "mutation_suggestion": "A specific ZK-STARK constraint or structural fix to address the flaw"
}}
"""
    return prompt

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python nd_adversarial_review.py <source_file>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        # Use first 2000 chars for review to fit context nicely
        code_snippet = content[:2000]
        
        print(f"[*] Analyzing {file_path.name} via 5-PhD ND-Gauntlet...")
        
        raise RuntimeError("Remote LLM API calls are permanently disabled. Only local agent logic is allowed.")
        for pid in PERSONAS:
            print(f"    - Prompting {PERSONAS[pid]['name']}...")
            
    except Exception as e:
        print(f"[!] Error: {e}")
