import os
import re

root_dir = "/home/allaun/Documents/Research Stack"
scripts_dir = os.path.join(root_dir, "5-Applications/scripts")
infra_dir = os.path.join(root_dir, "4-Infrastructure/infra")

replacements = [
    (re.compile(r'Path\(__file__\)\.parent\.parent\.parent\s*/\s*"infra"'), 'Path(__file__).parent.parent.parent / "4-Infrastructure" / "infra"'),
    (re.compile(r'project_root\s*/\s*"infra"'), 'project_root / "4-Infrastructure" / "infra"'),
    (re.compile(r'ROOT\s*/\s*"infra"'), 'ROOT / "4-Infrastructure" / "infra"'),
    (re.compile(r'BASE_DIR\s*/\s*"infra"'), 'BASE_DIR / "4-Infrastructure" / "infra"'),
    (re.compile(r'"/home/allaun/Documents/Research Stack/infra"'), '"/home/allaun/Documents/Research Stack/4-Infrastructure/infra"'),
    (re.compile(r"'/home/allaun/Documents/Research Stack/infra'"), "'/home/allaun/Documents/Research Stack/4-Infrastructure/infra'"),
    (re.compile(r'"/home/allaun/Research Stack/infra"'), '"/home/allaun/Documents/Research Stack/4-Infrastructure/infra"'),
    (re.compile(r"'/home/allaun/Research Stack/infra'"), "'/home/allaun/Documents/Research Stack/4-Infrastructure/infra'"),
    (re.compile(r'RESEARCH_STACK\s*/\s*"infra"'), 'RESEARCH_STACK / "4-Infrastructure" / "infra"'),
]

files_to_check = []
for d in [scripts_dir, infra_dir]:
    for f in os.listdir(d):
        if f.endswith(".py"):
            files_to_check.append(os.path.join(d, f))

# Add the specific one in infra subdirectory
files_to_check.append(os.path.join(infra_dir, "embedded_surface/server.py"))

for file_path in files_to_check:
    if not os.path.isfile(file_path):
        continue
    with open(file_path, 'r') as f:
        content = f.read()

    new_content = content
    for pattern, replacement in replacements:
        new_content = pattern.sub(replacement, new_content)

    if new_content != content:
        print(f"Updating {file_path}")
        with open(file_path, 'w') as f:
            f.write(new_content)

# Special case for manifold_perception.py
manifold_path = os.path.join(infra_dir, "manifold_perception.py")
if os.path.exists(manifold_path):
    with open(manifold_path, 'r') as f:
        content = f.read()
    new_content = content.replace('RESEARCH_STACK = Path("/home/allaun/Research Stack")', 'RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")')
    if new_content != content:
        print(f"Updating {manifold_path} RESEARCH_STACK")
        with open(manifold_path, 'w') as f:
            f.write(new_content)
