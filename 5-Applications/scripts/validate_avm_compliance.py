import os
import sys

def validate_avm_compliance():
    """
    Checks the AVM path for prohibited types (f32, f64, float, double).
    """
    avm_path = "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/AVM.lean"
    prohibited = ["f32", "f64", "float", "double"]
    
    if not os.path.exists(avm_path):
        print(f"[ERROR] AVM core file not found at {avm_path}")
        return False

    with open(avm_path, "r") as f:
        content = f.read().lower()
        
    violations = []
    for p in prohibited:
        if p in content:
            # Check if it's just part of another word (e.g., 'float' in 'FloatingPoint')
            # But the ban is strict for 'f32', 'f64'.
            violations.append(p)
            
    if violations:
        print(f"[FAIL] AVM Compliance Violation detected! Prohibited types found: {violations}")
        return False
    
    print("[PASS] AVM Compliance: Zero prohibited numeric types found.")
    return True

if __name__ == "__main__":
    if validate_avm_compliance():
        sys.exit(0)
    else:
        sys.exit(1)
