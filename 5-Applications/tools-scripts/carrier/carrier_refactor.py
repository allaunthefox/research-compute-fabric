import os
import re
from pathlib import Path

# Define replacement rules (more specific first)
REPLACEMENTS = [
    (r'soliton spacing', 'carrier spacing'),
    (r'Soliton spacing', 'Carrier spacing'),
    (r'soliton factory', 'carrier factory'),
    (r'Soliton factory', 'Carrier factory'),
    (r'soliton engine', 'carrier engine'),
    (r'Soliton engine', 'Carrier engine'),
    (r'soliton constants', 'carrier constants'),
    (r'Soliton constants', 'Carrier constants'),
    (r'Soliton Field Collapse', 'Carrier Field Collapse'),
    (r'Quantum Solitons', 'Quantum Carrier States'),
    (r'soliton_factory', 'carrier_factory'),
    (r'soliton_engine', 'carrier_engine'),
    (r'soliton_constants', 'carrier_constants'),
]

# Noun replacements (with plural support and Davydov exemption)
def replace_solitons(text):
    # Exempt Davydov solitons
    # This regex looks for 'soliton' NOT preceded by 'Davydov' (case insensitive)
    # We'll do it in steps for safety.
    
    # Step 1: Protect Davydov solitons
    text = re.sub(r'(Davydov\s+)(solitons?)', r'\1PROTECTED_SOLITON_\2', text, flags=re.IGNORECASE)
    
    # Step 2: Global replacements from REPLACEMENTS list
    for pattern, replacement in REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    
    # Step 3: Generic noun replacements
    text = re.sub(r'solitons', 'carrier states', text)
    text = re.sub(r'Solitons', 'Carrier states', text)
    text = re.sub(r'soliton', 'carrier state', text)
    text = re.sub(r'Soliton', 'Carrier state', text)
    
    # Step 4: Unprotect Davydov solitons
    text = re.sub(r'PROTECTED_SOLITON_(solitons?)', r'\1', text)
    
    return text

# Paths to scan
ROOT_DIR = Path(__file__).resolve().parents[2]
EXCLUDE_DIRS = {'5-Applications/audit/sessions', '5-Applications/audit/logs', '.git', '__pycache__', 'target', 'external/vendor'}

def refactor_file(file_path):
    if not os.path.isfile(file_path):
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return # Skip binary files

    new_content = replace_solitons(content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Refactored: {file_path}")

def run_refactor():
    for root, dirs, files in os.walk(ROOT_DIR):
        rel_path = os.path.relpath(root, ROOT_DIR)
        
        # Check if we should skip this entire subtree
        is_excluded = any(rel_path == d or rel_path.startswith(d + os.sep) for d in EXCLUDE_DIRS)
        
        if is_excluded:
            dirs[:] = [] # Don't recurse
            continue # Don't process files in this directory

        for file in files:
            if file.startswith('.') or file.endswith(('.png', '.pdf', '.zip', '.enc', '.pyc')):
                continue
            
            file_path = os.path.join(root, file)
            refactor_file(file_path)

if __name__ == "__main__":
    run_refactor()
