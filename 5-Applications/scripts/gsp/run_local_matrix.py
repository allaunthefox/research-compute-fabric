from .runner import _run_wrapper
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
from .backends import VirtualSubstrateBackend, SoftwareTriangleBackend, ClassicalHeuristicBackend, LearnedClosureBaselineBackend, EddyViscosityROMBackend
from .perceval_backend import PercevalGeometryShaverBackend

def run_local_matrix():
    print("Starting full local verification matrix...")
    nu0, beta, dt = 0.01, 0.5, 0.01
    steps = 500
    N_shots = 1000
    seeds = list(range(42, 51)) # 9 seeds
    
    variants_parallel = [
        ("A", SoftwareTriangleBackend, {}),
        ("B", SoftwareTriangleBackend, {}),
        ("C", ClassicalHeuristicBackend, {"c1": 0.1, "c2": 0.1, "c3": 0.01}),
        ("D", PercevalGeometryShaverBackend, {"M": 6}),
        ("D_mem", PercevalGeometryShaverBackend, {"M": 6}),
        ("F", LearnedClosureBaselineBackend, {}),
        ("G", EddyViscosityROMBackend, {"c_smag": 0.1})
    ]
    
    tasks = []
    for variant, backend_cls, kwargs in variants_parallel:
        for seed in seeds:
            use_mem = (variant == "D_mem")
            tasks.append((variant, backend_cls, kwargs, nu0, beta, dt, steps, N_shots, seed, use_mem))
            
    receipts = []
    out_dir = Path("/home/allaun/Documents/Research Stack/shared-data/artifacts/gsp")
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_run_wrapper, t): t for t in tasks}
        for future in as_completed(futures):
            variant, seed, receipt, trace = future.result()
            print(f"Completed Variant {variant} Seed {seed} (L2: {receipt['metrics']['mean_l2_error']:.4f})")
            receipts.append(receipt)
            with open(out_dir / f"trace_variant_{variant}_seed_{seed}.json", "w") as f:
                json.dump(trace, f, indent=2)
                
    with open(out_dir / "local_matrix_receipts.json", "w") as f:
        json.dump(receipts, f, indent=2)

if __name__ == "__main__":
    run_local_matrix()
