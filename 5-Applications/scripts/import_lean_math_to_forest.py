#!/usr/bin/env python3
"""
Import Lean Analysis Math to Forest

Extracts mathematical equations from Lean analysis files and imports
them into the equation forest (MATH_MODEL_MAP.tsv), then identifies
intersections/touch points with existing forest equations.
"""

import re
import json
from typing import Dict, List, Tuple, Any


def extract_lean_equations(file_path: str) -> List[Dict[str, str]]:
    """
    Extract mathematical equations from Lean file.
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    equations = []
    
    # Extract def and theorem blocks
    def_pattern = r'def\s+(\w+)\s*[:=]\s*(.+?)(?=\n(?:def|theorem|structure|namespace|end)|$)'
    theorem_pattern = r'theorem\s+(\w+)\s*[:=]\s*(.+?)(?=\n(?:def|theorem|structure|namespace|end)|$)'
    
    def_matches = re.finditer(def_pattern, content, re.DOTALL)
    theorem_matches = re.finditer(theorem_pattern, content, re.DOTALL)
    
    for match in def_matches:
        name = match.group(1)
        body = match.group(2).strip()
        equations.append({
            "name": name,
            "type": "definition",
            "body": body,
            "file": file_path
        })
    
    for match in theorem_matches:
        name = match.group(1)
        body = match.group(2).strip()
        equations.append({
            "name": name,
            "type": "theorem",
            "body": body,
            "file": file_path
        })
    
    return equations


def lean_to_math_model(equations: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Convert Lean equations to MATH_MODEL_MAP format.
    """
    math_models = []
    
    for eq in equations:
        # Extract LaTeX-like equation from Lean body
        body = eq["body"]
        
        # Simplify Lean notation to equation format
        # Remove Lean-specific syntax
        equation_str = body.replace(":=", "=")
        equation_str = re.sub(r'→', '->', equation_str)
        equation_str = re.sub(r'∀', 'forall', equation_str)
        equation_str = re.sub(r'∃', 'exists', equation_str)
        equation_str = re.sub(r'∧', 'and', equation_str)
        equation_str = re.sub(r'∨', 'or', equation_str)
        equation_str = re.sub(r'→', 'implies', equation_str)
        
        # Extract variables (simplified)
        variables = []
        var_pattern = r'(\w+)\s*:\s*ℝ'
        for match in re.finditer(var_pattern, body):
            variables.append(match.group(1))
        
        if not variables:
            var_pattern = r'(\w+)\s*:\s*ℕ'
            for match in re.finditer(var_pattern, body):
                variables.append(match.group(1))
        
        variables_str = ", ".join(variables) if variables else "f, x, ε, δ"
        
        # Determine family based on content
        if "Continuous" in eq["name"]:
            family = "Analysis"
            purpose = "Continuity and differentiability foundations"
        elif "Differentiable" in eq["name"]:
            family = "Analysis"
            purpose = "Differentiability and smoothness theory"
        elif "Convex" in eq["name"]:
            family = "Optimization"
            purpose = "Convexity and optimization theory"
        elif "Lipschitz" in eq["name"]:
            family = "Analysis"
            purpose = "Lipschitz continuity and ODE theory"
        elif "ODE" in eq["name"]:
            family = "Dynamics"
            purpose = "Ordinary differential equation theory"
        elif "Picard" in eq["name"]:
            family = "Dynamics"
            purpose = "Picard-Lindelöf existence theorem"
        elif "Efficiency" in eq["name"] or "Gain" in eq["name"]:
            family = "Efficiency"
            purpose = "Efficiency metrics and calculations"
        elif "Manifold" in eq["name"]:
            family = "Topology"
            purpose = "Manifold structure and topology"
        else:
            family = "General"
            purpose = "Mathematical foundation"
        
        math_models.append({
            "Model_Name": f"Lean_{eq['name']}",
            "Family": family,
            "Equation": equation_str[:200],  # Truncate for display
            "Variables": variables_str,
            "Purpose": purpose,
            "Location": eq["file"],
            "Implemented": "Lean",
            "Status": "✅",
            "Cross_Refs": "",
            "Domain_Type": "mathematical_bind",
            "Bind_Class": "informational_bind"
        })
    
    return math_models


def find_intersections(lean_models: List[Dict[str, str]], forest_path: str) -> Dict[str, Any]:
    """
    Find intersections between Lean equations and forest equations.
    """
    # Read existing forest equations
    forest_equations = []
    with open(forest_path, 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:  # Skip header
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                forest_equations.append({
                    "name": parts[1],
                    "family": parts[2],
                    "equation": parts[3],
                    "variables": parts[4]
                })
    
    intersections = {
        "family_matches": [],
        "variable_matches": [],
        "equation_similarity": []
    }
    
    # Find family matches
    lean_families = set(m["Family"] for m in lean_models)
    forest_families = set(e["family"] for e in forest_equations)
    
    for family in lean_families:
        if family in forest_families:
            lean_eq = [m for m in lean_models if m["Family"] == family]
            forest_eq = [e for e in forest_equations if e["family"] == family]
            intersections["family_matches"].append({
                "family": family,
                "lean_equations": [m["Model_Name"] for m in lean_eq],
                "forest_equations": [e["name"] for e in forest_eq]
            })
    
    # Find variable matches
    for lean_model in lean_models:
        lean_vars = set(v.strip() for v in lean_model["Variables"].split(','))
        for forest_eq in forest_equations:
            forest_vars = set(v.strip() for v in forest_eq["variables"].split(','))
            overlap = lean_vars & forest_vars
            if overlap:
                intersections["variable_matches"].append({
                    "lean_equation": lean_model["Model_Name"],
                    "forest_equation": forest_eq["name"],
                    "shared_variables": list(overlap)
                })
    
    # Find equation similarity (simple keyword matching)
    for lean_model in lean_models:
        lean_eq_lower = lean_model["Equation"].lower()
        for forest_eq in forest_equations:
            forest_eq_lower = forest_eq["equation"].lower()
            
            # Check for common mathematical terms
            math_terms = ["continuity", "differentiable", "convex", "lipschitz", "ode", "energy", "entropy"]
            shared_terms = [term for term in math_terms if term in lean_eq_lower and term in forest_eq_lower]
            
            if shared_terms:
                intersections["equation_similarity"].append({
                    "lean_equation": lean_model["Model_Name"],
                    "forest_equation": forest_eq["name"],
                    "shared_terms": shared_terms
                })
    
    return intersections


def main():
    """Import Lean math to forest and find intersections."""
    print("=" * 70)
    print("IMPORT LEAN ANALYSIS MATH TO FOREST")
    print("=" * 70)
    
    # Extract equations from Lean files
    print("\n[*] Extracting equations from Lean analysis files...")
    
    lean_files = [
        "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/AnalysisFoundations.lean",
        "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/EfficiencyAnalysis.lean",
        "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/SwarmAnalysis.lean"
    ]
    
    all_equations = []
    for lean_file in lean_files:
        equations = extract_lean_equations(lean_file)
        all_equations.extend(equations)
        print(f"    {lean_file}: {len(equations)} equations")
    
    print(f"\n[*] Total equations extracted: {len(all_equations)}")
    
    # Convert to math model format
    print(f"\n[*] Converting to MATH_MODEL_MAP format...")
    math_models = lean_to_math_model(all_equations)
    print(f"    Converted {len(math_models)} equations")
    
    # Show sample equations
    print(f"\n[*] Sample Lean Equations:")
    for i, model in enumerate(math_models[:5]):
        print(f"    {i+1}. {model['Model_Name']} ({model['Family']})")
        print(f"       {model['Equation'][:100]}...")
    
    # Find intersections with forest
    print(f"\n[*] Finding intersections with forest equations...")
    forest_path = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/MATH_MODEL_MAP.tsv"
    intersections = find_intersections(math_models, forest_path)
    
    print(f"\n[*] Family Matches:")
    for match in intersections["family_matches"]:
        print(f"    {match['family']}:")
        print(f"        Lean: {len(match['lean_equations'])} equations")
        print(f"        Forest: {len(match['forest_equations'])} equations")
    
    print(f"\n[*] Variable Matches (sample):")
    for match in intersections["variable_matches"][:10]:
        print(f"    {match['lean_equation']} ↔ {match['forest_equation']}")
        print(f"        Shared: {match['shared_variables']}")
    
    print(f"\n[*] Equation Similarity (sample):")
    for match in intersections["equation_similarity"][:10]:
        print(f"    {match['lean_equation']} ↔ {match['forest_equation']}")
        print(f"        Terms: {match['shared_terms']}")
    
    # Save results
    results = {
        "total_lean_equations": len(all_equations),
        "converted_models": len(math_models),
        "lean_equations": all_equations,
        "math_models": math_models,
        "intersections": intersections
    }
    
    output_path = "/home/allaun/Documents/Research Stack/data/lean_math_forest_import.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[*] Results saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✅ LEAN MATH IMPORT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
