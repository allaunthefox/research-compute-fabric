#!/usr/bin/env python3
"""
S3C Lean Code Review via Gemma 4
Submits S3C.lean for code review by Gemma 4
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from infra.gemma_4_integration import GemmaVariant, GemmaTask, GemmaTaskRequest, Gemma4Integration

def main():
    print("=" * 70)
    print("S3C LEAN CODE REVIEW VIA GEMMA 4")
    print("=" * 70)
    
    # Read S3C.lean file
    s3c_lean_path = "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/S3C.lean"
    with open(s3c_lean_path, 'r') as f:
        s3c_code = f.read()
    
    print(f"\nRead S3C.lean: {len(s3c_code)} characters")
    
    # Initialize Gemma integration
    gemma = Gemma4Integration(default_variant=GemmaVariant.E4B)
    
    # Create review task
    task_id = f"s3c_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    review_task = GemmaTaskRequest(
        task_id=task_id,
        task_type=GemmaTask.REASONING,
        variant=GemmaVariant.E4B,
        input_data={
            "prompt": """Review the following Lean 4 code for S3C manifold processing. Check for:
1. Adherence to AGENTS.md rules (naming conventions, no Float, bind primitive, etc.)
2. Mathematical correctness of shell decomposition n = k^2 + a
3. Correctness of J-score calculation: J(n) = ab*F_m + (a-b)*F_p + <chi, F_c>
4. Emission gate logic: kappa_A AND kappa_C AND J > 0
5. Proper use of Q16_16 fixed-point arithmetic
6. Missing theorems or correctness proofs
7. Potential improvements or optimizations

Provide specific feedback on any issues found.""",
            "code": s3c_code,
            "file": "S3C.lean",
            "enable_thinking": True
        },
        enable_thinking=True,
        max_tokens=2048,
        priority=9
    )
    
    print(f"\nSubmitting review task: {task_id}")
    submitted_id = gemma.submit_task(review_task)
    print(f"Task submitted: {submitted_id}")
    
    # Execute the task
    print(f"\nExecuting review task...")
    result = gemma.execute_task(submitted_id)
    
    print(f"\nReview Result:")
    print(json.dumps(result, indent=2))
    
    # Save review to file
    review_path = f"/home/allaun/Documents/Research Stack/data/s3c_lean_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(review_path, 'w') as f:
        json.dump({
            "task_id": task_id,
            "submitted_id": submitted_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\nReview saved to: {review_path}")
    
    print("\n" + "=" * 70)
    print("S3C LEAN CODE REVIEW COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
