"""
AlphaProof-inspired proof search loop.

Generates Lean proof candidates via a local LLM (Ollama), verifies them
through lake build, and iterates with error feedback until a valid proof
is found or max iterations exhausted.

Logs all iterations to JSONL for replay analysis.
"""

import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("ALPHAPROOF_MODEL", "deepseek-coder-v2:16b")
LOG_DIR = Path(__file__).parent / "alphaproof_logs"

Q16_SCALE = 65536  # 2^16 for Q16.16 fixed-point


# ---------------------------------------------------------------------------
# Ollama LLM interface
# ---------------------------------------------------------------------------

def generate_candidate(prompt: str, model: str = DEFAULT_MODEL,
                       temperature: float = 0.7) -> str:
    """Call Ollama API to generate a candidate Lean proof.

    Args:
        prompt: The problem description + error feedback.
        model: Ollama model name.
        temperature: Sampling temperature.

    Returns:
        Generated Lean code string.
    """
    if not HAS_REQUESTS:
        raise ImportError("requests library required. pip install requests")

    system_prompt = (
        "You are a Lean 4 theorem prover. Given a mathematical problem, "
        "generate a complete, compilable Lean 4 module with all necessary "
        "imports. Use `import Mathlib` for standard library. "
        "Output ONLY the Lean code, no markdown fences or explanations. "
        "The module must compile with `lake build`."
    )

    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 4096,
        }
    }

    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload,
                             timeout=120)
        resp.raise_for_status()
        result = resp.json()
        code = result.get("response", "")
        # Strip markdown fences if present
        code = re.sub(r'^```(?:lean|lean4)?\s*\n?', '', code, flags=re.MULTILINE)
        code = re.sub(r'\n?```\s*$', '', code, flags=re.MULTILINE)
        return code.strip()
    except requests.RequestException as e:
        return f"-- ERROR: Ollama request failed: {e}"


# ---------------------------------------------------------------------------
# Lean verification
# ---------------------------------------------------------------------------

def verify_proof(lean_code: str, module_name: str = "Candidate",
                 lake_project: Optional[str] = None,
                 timeout: int = 120) -> dict:
    """Write Lean code to a temp file and verify via lake build.

    Args:
        lean_code: Complete Lean 4 module source.
        module_name: Name for the temp module file.
        lake_project: Path to existing lake project. If None, creates a temp one.
        timeout: Build timeout in seconds.

    Returns:
        {'success': bool, 'errors': list[str], 'warnings': list[str]}
    """
    errors = []
    warnings = []

    with tempfile.TemporaryDirectory(prefix="alphaproof_") as tmpdir:
        tmpdir = Path(tmpdir)

        if lake_project is None:
            # Create a minimal lake project
            lakefile = tmpdir / "lakefile.lean"
            lakefile.write_text(
                'import Lake\n'
                'open Lake DSL in\n'
                'package «candidate» where\n'
                '  leanOptions := #[\n'
                '    ⟨`pp.unicode.fun, true⟩\n'
                '  ]\n\n'
                'require mathlib from git\n'
                '  "https://github.com/leanprover-community/mathlib4" @ "master"\n'
            )
            project_dir = tmpdir
        else:
            project_dir = Path(lake_project)

        # Write candidate file
        candidate_dir = project_dir / "Candidate"
        candidate_dir.mkdir(exist_ok=True)
        candidate_file = candidate_dir / f"{module_name}.lean"
        candidate_file.write_text(lean_code)

        # Run lake build
        try:
            result = subprocess.run(
                ["lake", "build", f"Candidate.{module_name}"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "LAKE_PATH": str(project_dir)}
            )

            if result.returncode == 0:
                return {'success': True, 'errors': [], 'warnings': []}

            # Parse errors from stderr
            stderr = result.stderr
            error_lines = []
            for line in stderr.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if 'error' in line.lower():
                    error_lines.append(line)
                elif 'warning' in line.lower():
                    warnings.append(line)
                elif line.startswith('error:') or 'Error' in line:
                    error_lines.append(line)

            if not error_lines and stderr:
                error_lines = [stderr[:500]]

            return {
                'success': False,
                'errors': error_lines,
                'warnings': warnings
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'errors': [f'Build timed out after {timeout}s'],
                'warnings': []
            }
        except FileNotFoundError:
            return {
                'success': False,
                'errors': ['lake command not found. Is Lean/Lake installed?'],
                'warnings': []
            }


# ---------------------------------------------------------------------------
# FPGA Q16 acceleration (Python placeholder)
# ---------------------------------------------------------------------------

def q16_multiply(a: int, b: int) -> int:
    """Q16.16 fixed-point multiplication.

    (a * b) >> 16 with overflow clamping.
    """
    result = (a * b) >> 16
    # Clamp to Q16.16 range
    INT32_MAX = 2147483647
    INT32_MIN = -2147483648
    return max(INT32_MIN, min(INT32_MAX, result))


def q16_from_float(f: float) -> int:
    """Convert float to Q16.16."""
    return max(-2147483648, min(2147483647, round(f * Q16_SCALE)))


def q16_to_float(q: int) -> float:
    """Convert Q16.16 to float."""
    return q / Q16_SCALE


def fpga_accelerate(candidates: list[dict]) -> list[dict]:
    """Rank candidates using Q16.16 fixed-point scoring.

    This is a Python placeholder for FPGA Q16 LUT acceleration.
    In production, this would route through UART to the Tang Nano 9K
    or direct memory-mapped LUT access.

    Scoring heuristic:
        - Shorter proofs score higher (fewer tokens)
        - Proofs with fewer sorry/axiom/admit score higher
        - Previous success patterns boost score

    Args:
        candidates: list of {'code': str, 'iteration': int, ...}

    Returns:
        Candidates sorted by Q16 score (descending), with 'q16_score' added.
    """
    scored = []
    for c in candidates:
        code = c.get('code', '')

        # Length penalty (shorter is better)
        length_score = q16_from_float(1.0 / (1.0 + len(code) / 1000.0))

        # Penalty for incomplete proofs
        penalty = 0
        for bad_word in ['sorry', 'admit', 'axiom', 'by omega']:
            count = code.count(bad_word)
            penalty += q16_from_float(count * 0.1)

        # Base score from length
        base = length_score

        # Bonus for having structure (def, theorem, proof)
        if 'theorem' in code or 'lemma' in code:
            base = q16_multiply(base, q16_from_float(1.2))

        final_score = max(0, base - penalty)
        c['q16_score'] = final_score
        c['q16_score_float'] = q16_to_float(final_score)
        scored.append(c)

    scored.sort(key=lambda x: x.get('q16_score', 0), reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Main search loop
# ---------------------------------------------------------------------------

def search_loop(problem: str, max_iterations: int = 50,
                model: str = DEFAULT_MODEL,
                lake_project: Optional[str] = None,
                temperature: float = 0.7,
                build_timeout: int = 120) -> dict:
    """Main AlphaProof search loop: generate → verify → feedback → retry.

    Args:
        problem: Natural language description of the problem to prove.
        max_iterations: Maximum number of generate-verify cycles.
        model: Ollama model to use.
        lake_project: Optional path to existing lake project.
        temperature: LLM temperature.
        build_timeout: Lean build timeout per iteration.

    Returns:
        {'solution': str, 'iterations': int, 'success': bool,
         'candidates': list[dict], 'log_path': str}
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"search_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"

    candidates = []
    best_solution = ""
    feedback = ""

    with open(log_path, 'w') as log_f:
        for iteration in range(1, max_iterations + 1):
            t0 = time.time()

            # Build prompt with feedback from previous iterations
            if feedback:
                prompt = (
                    f"Problem:\n{problem}\n\n"
                    f"Previous attempt failed with these errors:\n{feedback}\n\n"
                    f"Please fix the Lean code and try again. "
                    f"Iteration {iteration}/{max_iterations}."
                )
            else:
                prompt = f"Problem:\n{problem}\n\nPlease write a Lean 4 proof."

            # Generate candidate
            code = generate_candidate(prompt, model=model,
                                      temperature=temperature)
            gen_time = time.time() - t0

            # Verify
            t1 = time.time()
            result = verify_proof(code, module_name=f"Iter{iteration}",
                                  lake_project=lake_project,
                                  timeout=build_timeout)
            ver_time = time.time() - t1

            candidate = {
                'iteration': iteration,
                'code': code,
                'success': result['success'],
                'errors': result['errors'],
                'warnings': result['warnings'],
                'gen_time': round(gen_time, 2),
                'verify_time': round(ver_time, 2),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            candidates.append(candidate)

            # Log to JSONL
            log_entry = {**candidate, 'code_length': len(code)}
            log_f.write(json.dumps(log_entry) + '\n')
            log_f.flush()

            if result['success']:
                best_solution = code
                # Rank remaining candidates via FPGA Q16 path
                candidates = fpga_accelerate(candidates)
                return {
                    'solution': best_solution,
                    'iterations': iteration,
                    'success': True,
                    'candidates': candidates,
                    'log_path': str(log_path),
                }

            # Build feedback for next iteration
            feedback = '\n'.join(result['errors'][:5])  # Top 5 errors
            print(f"[alphaproof] iter {iteration}/{max_iterations}: "
                  f"FAIL ({len(result['errors'])} errors, "
                  f"gen={gen_time:.1f}s, ver={ver_time:.1f}s)")

    # Exhausted iterations
    candidates = fpga_accelerate(candidates)
    return {
        'solution': best_solution,
        'iterations': max_iterations,
        'success': False,
        'candidates': candidates,
        'log_path': str(log_path),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python alphaproof_loop.py <problem_file_or_text> "
              "[--max-iter N] [--model MODEL]")
        sys.exit(1)

    problem_arg = sys.argv[1]
    if os.path.isfile(problem_arg):
        problem_text = Path(problem_arg).read_text()
    else:
        problem_text = problem_arg

    max_iter = 50
    model_name = DEFAULT_MODEL

    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == '--max-iter' and i + 1 < len(sys.argv):
            max_iter = int(sys.argv[i + 1])
        elif arg == '--model' and i + 1 < len(sys.argv):
            model_name = sys.argv[i + 1]

    result = search_loop(problem_text, max_iterations=max_iter,
                         model=model_name)

    print(f"\n{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Log: {result['log_path']}")
    if result['success']:
        print(f"\nSolution:\n{result['solution']}")
