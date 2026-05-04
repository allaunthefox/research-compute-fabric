#!/usr/bin/env python3
import re
import hashlib
import sys

def canonicalize_formula(formula):
    """
    Normalize a math formula by replacing variable names with generic placeholders.
    Example: 'F = m * a' -> 'x0 = x1 * x2'
    """
    if not formula:
        return ""

    # 1. Clean up spacing and common LaTeX symbols
    formula = formula.replace('\\', '')
    formula = formula.replace('{', '(').replace('}', ')')
    formula = re.sub(r'\s+', ' ', formula).strip()

    # 2. Identify variables (words that are not known functions or constants)
    # This is a heuristic.
    known_functions = {'sin', 'cos', 'tan', 'exp', 'log', 'sqrt', 'sum', 'prod', 'delta', 'nabla', 'partial'}
    
    # Extract all words
    tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', formula)
    
    variables = []
    for token in tokens:
        if token.lower() not in known_functions and token not in variables:
            variables.append(token)
    
    # 3. Replace variables with x0, x1, ...
    canonical = formula
    for i, var in enumerate(variables):
        # Use word boundaries to avoid partial matches
        canonical = re.sub(r'\b' + re.escape(var) + r'\b', f'x{i}', canonical)
    
    return canonical

def generate_shape_uuid(canonical_formula):
    """Generate a stable UUID for a formula shape."""
    if not canonical_formula:
        return "00000000-0000-0000-0000-000000000000"
    
    hash_obj = hashlib.sha256(canonical_formula.encode())
    digest = hash_obj.digest()
    
    # Construct a UUIDv4-like string from the hash (but deterministic)
    return str(hashlib.sha256(canonical_formula.encode()).hexdigest())[:36] # Simplification for now

def main():
    if len(sys.argv) < 2:
        print("Usage: canonicalize_formula.py <formula>")
        print("Example: canonicalize_formula.py 'F = m * a'")
        return

    formula = " ".join(sys.argv[1:])
    canonical = canonicalize_formula(formula)
    shape_id = generate_shape_uuid(canonical)
    
    print(f"Original:  {formula}")
    print(f"Canonical: {canonical}")
    print(f"Shape ID:  {shape_id}")

if __name__ == '__main__':
    main()
