#!/usr/bin/env python3
"""
BFS-Prover-V2 integration for Research Stack.
Calls various backends (Ollama, Unsloth, Thoth, etc.) to generate Lean 4 proofs for sorry theorems.

Usage:
    python scripts/bf4prover.py <lean_file> [--backend BACKEND] [--model MODEL] [--dry-run]
"""

import argparse
import json
import re
import subprocess
import sys
import textwrap
import time
from pathlib import Path

# Import backend orchestrator
try:
    from prover_backend_interface import ProverOrchestrator, create_backend
except ImportError:
    # Add scripts directory to path
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    from prover_backend_interface import ProverOrchestrator, create_backend

DEFAULT_MODEL = "zeyu-zheng/BFS-Prover-V2-7B:q8_0"


def extract_context(lean_path: Path) -> str:
    """Extract imports and key definitions from the top of a Lean file."""
    with open(lean_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Grab imports and namespace declarations
    context = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("open "):
            context.append(stripped)
        elif stripped.startswith("namespace ") or stripped.startswith("structure "):
            context.append(stripped)
        elif stripped.startswith("def ") or stripped.startswith("theorem "):
            # Stop at first theorem/def unless it's a small helper
            break
    return "\n".join(context)


def extract_sorry_blocks(lean_path: Path):
    """
    Extract theorem statements whose proof body contains `sorry`.
    Returns list of dicts: {name, statement_text, start_line, end_line}
    """
    with open(lean_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks = []
    i = 0
    while i < len(lines):
        # Look for theorem/lemma/def lines
        m = re.match(r"^\s*(theorem|lemma)\s+(\w+)", lines[i])
        if m:
            name = m.group(2)
            start = i
            # Find the end of this declaration (next theorem/lemma/def/end/section at same or lower indent)
            j = i + 1
            while j < len(lines):
                if re.match(r"^\s*(theorem|lemma|def|instance|#|end\b|section\b)", lines[j]):
                    break
                j += 1
            body = "".join(lines[start:j])
            if "sorry" in body and "TODO(lean-port)" in body:
                blocks.append({
                    "name": name,
                    "statement_text": body,
                    "start_line": start + 1,  # 1-indexed
                    "end_line": j,            # 1-indexed exclusive
                })
            i = j
        else:
            i += 1
    return blocks


def build_prompt(context: str, theorem_stmt: str) -> str:
    """Build a prompt for BFS-Prover-V2."""
    # Strip out the old proof attempt / comments / sorry for a clean theorem statement
    clean_stmt = re.sub(r"by\s+--.*TODO\(lean-port\).*sorry", "by", theorem_stmt, flags=re.DOTALL)
    clean_stmt = re.sub(r"by\s+sorry", "by", clean_stmt, flags=re.DOTALL)
    clean_stmt = re.sub(r"/\-.*?\-", "", clean_stmt, flags=re.DOTALL)
    clean_stmt = textwrap.dedent(clean_stmt).strip()

    prompt = f"""You are BFS-Prover-V2, a state-of-the-art Lean 4 theorem prover.
Complete the proof of the following theorem using only standard Lean 4 tactics.
Do not use `sorry`. Output ONLY the tactic block (starting with `by` or the first tactic).

### Context
```lean
{context}
```

### Theorem
```lean
{clean_stmt}
```

### Proof
"""
    return prompt


def call_backend(prompt: str, orchestrator: ProverOrchestrator, model: str, timeout: int = 180) -> str:
    """Call backend through orchestrator."""
    try:
        return orchestrator.generate_proof(prompt, model)
    except Exception as e:
        raise RuntimeError(f"Backend error ({orchestrator.get_backend_name()}): {e}")


def extract_tactics(raw: str) -> str:
    """Extract the tactic block from model output."""
    # If wrapped in ```lean ... ```
    m = re.search(r"```(?:lean)?\s*(.*?)```", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    # If it starts with 'by'
    m = re.search(r"(by\b.*?)(?:\n\n|$)", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Otherwise just return the raw text if it looks like tactics
    raw_stripped = raw.strip()
    if raw_stripped.startswith("by ") or raw_stripped.startswith("  "):
        return raw_stripped
    return raw_stripped


def replace_proof(lean_path: Path, block: dict, tactics: str) -> bool:
    """Replace the sorry block with the suggested tactics. Return True if written."""
    with open(lean_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    start_idx = block["start_line"] - 1
    end_idx = block["end_line"] - 1

    # Find the line with "sorry" and replace it with tactics
    for k in range(start_idx, end_idx):
        if "sorry" in lines[k]:
            # Check if the previous line has ":= by"
            if k > 0 and ":= by" in lines[k-1]:
                # Replace the sorry line with tactics (without "by")
                indent = "  "  # Standard Lean indentation
                new_lines = lines[:k]

                # Add the tactics without "by" prefix if it already exists
                if tactics.startswith("by "):
                    new_lines.append(f"{indent}{tactics[3:]}\n")
                else:
                    new_lines.append(f"{indent}{tactics}\n")

                new_lines.extend(lines[k+1:])

                # Write to file
                backup = lean_path.with_suffix(".lean.bak")
                lean_path.rename(backup)
                with open(lean_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                return True
            else:
                # Replace the sorry line with tactics
                indent = "  "  # Standard Lean indentation
                new_lines = lines[:k]

                # Add the tactics with proper indentation
                if tactics.startswith("sorry"):
                    # Keep as sorry with comment
                    new_lines.append(f"{indent}{tactics}\n")
                else:
                    # Add tactics
                    new_lines.append(f"{indent}{tactics}\n")

                new_lines.extend(lines[k+1:])

                # Write to file
                backup = lean_path.with_suffix(".lean.bak")
                lean_path.rename(backup)
                with open(lean_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                return True

    return False


def try_compile(lean_path: Path, package_dir: Path) -> tuple[bool, str]:
    """Run lake build for the specific module. Returns (success, output)."""
    rel = lean_path.relative_to(package_dir)
    mod_name = str(rel.with_suffix("")).replace("/", ".")
    proc = subprocess.run(
        ["lake", "build", f"+{mod_name}"],
        cwd=package_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    success = proc.returncode == 0
    return success, proc.stdout + proc.stderr


def restore_backup(lean_path: Path):
    backup = lean_path.with_suffix(".lean.bak")
    if backup.exists():
        backup.rename(lean_path)


def main():
    parser = argparse.ArgumentParser(description="BFS-Prover-V2 sorry fixer with multi-backend support")
    parser.add_argument("lean_file", help="Path to the .lean file to repair")
    parser.add_argument("--backend", default=None, help="Backend: ollama, unsloth, thoth (auto-detect if not specified)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name (backend-specific)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling backend")
    parser.add_argument("--package-dir", default="0-Core-Formalism/lean/Semantics", help="Lake package root")
    args = parser.parse_args()

    lean_path = Path(args.lean_file).resolve()
    package_dir = Path(args.package_dir).resolve()

    if not lean_path.exists():
        print(f"ERROR: File not found: {lean_path}")
        sys.exit(1)

    # Initialize orchestrator
    if args.backend:
        backend = create_backend(args.backend)
        orchestrator = ProverOrchestrator(backend)
    else:
        orchestrator = ProverOrchestrator()

    print(f"Using backend: {orchestrator.get_backend_name()}")

    if not orchestrator.is_available():
        print(f"ERROR: Backend {orchestrator.get_backend_name()} is not available")
        sys.exit(1)

    context = extract_context(lean_path)
    blocks = extract_sorry_blocks(lean_path)

    if not blocks:
        print(f"No TODO(lean-port) sorry blocks found in {lean_path}")
        sys.exit(0)

    print(f"Found {len(blocks)} sorry block(s) in {lean_path.name}")

    for block in blocks:
        name = block["name"]
        print(f"\n=== {name} (lines {block['start_line']}-{block['end_line']}) ===")

        prompt = build_prompt(context, block["statement_text"])
        if args.dry_run:
            print("\n--- PROMPT ---")
            print(prompt)
            print("--- END PROMPT ---")
            continue

        print(f"Calling {orchestrator.get_backend_name()} BFS-Prover-V2...")
        try:
            raw = call_backend(prompt, orchestrator, args.model)
        except RuntimeError as e:
            print(f"ERROR: {e}")
            continue

        tactics = extract_tactics(raw)
        print(f"Suggested tactics:\n{tactics}")

        # Apply and test
        ok = replace_proof(lean_path, block, tactics)
        if not ok:
            print("Failed to apply patch.")
            continue

        success, output = try_compile(lean_path, package_dir)
        if success:
            print(f"✅ {name} COMPILES!")
            # Clean up backup
            backup = lean_path.with_suffix(".lean.bak")
            if backup.exists():
                backup.unlink()
        else:
            print(f"❌ {name} FAILED to compile. Restoring backup.")
            print(output[-800:])  # tail of output
            restore_backup(lean_path)

        time.sleep(1)  # Be nice to the backend

    print("\nDone.")


if __name__ == "__main__":
    main()
