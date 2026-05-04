import os
import re
from pathlib import Path

# Define replacement rules (more specific first)
REPLACEMENTS = [
    (r'nanonibble spacing', 'soliton spacing'),
    (r'Nanonibble spacing', 'Soliton spacing'),
    (r'P_nanonibble', 'P_microvoxel'),
    (r'nanonibbles', 'microvoxels'),
    (r'Nanonibbles', 'Microvoxels'),
    (r'nanonibble', 'microvoxel'),
    (r'Nanonibble', 'Microvoxel'),
]

# Paths to scan
ROOT_DIR = Path(__file__).resolve().parents[2]
EXCLUDE_DIRS = {'5-Applications/audit/sessions', '5-Applications/audit/logs', '.git', '__pycache__', 'target', 'external/vendor'}

FILES_PROCESSED = 0
FILES_CHANGED = 0

def refactor_file(file_path):
    if not os.path.isfile(file_path):
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return # Skip binary files

    new_content = content
    for pattern, replacement in REPLACEMENTS:
        new_content = re.sub(pattern, replacement, new_content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        global FILES_CHANGED
        FILES_CHANGED += 1
        print(f"Refactored: {file_path}")
    
    global FILES_PROCESSED
    FILES_PROCESSED += 1
    if FILES_PROCESSED % 1000 == 0:
        print(f"Progress: {FILES_PROCESSED} files scanned, {FILES_CHANGED} changed...")

def run_refactor():
    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter directories
        rel_path = os.path.relpath(root, ROOT_DIR)
        
        # Check if we should skip this entire subtree
        is_excluded = any(rel_path == d or rel_path.startswith(d + os.sep) for d in EXCLUDE_DIRS)
        
        if is_excluded:
            dirs[:] = [] # Don't recurse
            continue # Don't process files in this directory

        for file in files:
            # Skip hidden files and some extensions
            if file.startswith('.') or file.endswith(('.png', '.pdf', '.zip', '.enc', '.pyc')):
                continue
            
            file_path = os.path.join(root, file)
            refactor_file(file_path)

if __name__ == "__main__":
    run_refactor()
    print(f"COMPLETE: {FILES_PROCESSED} files scanned, {FILES_CHANGED} files refactored.")
