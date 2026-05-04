import json
import csv
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from .runner import _run_wrapper
from .perceval_backend import PercevalGeometryShaverBackend
from .backends import LearnedClosureBaselineBackend, EddyViscosityROMBackend, SoftwareTriangleBackend, ClassicalHeuristicBackend

def run_sweeps():
    print("Starting Sweep execution for N_shots and nu0 regimes...")
    
    beta, dt = 0.5, 0.01
    steps = 500
    seeds = list(range(42, 45)) # 3 seeds for sweeps
    
    nu0_regimes = [0.005, 0.01, 0.02]
    N_shots_sweep = [64, 128, 256, 512, 1024, 2048]
    
    tasks = []
    
    # N_shots sweep
    for N in N_shots_sweep:
        for seed in seeds:
            # We use variant name format D_N_{N_shots}
            variant = f"D_N_{N}"
            tasks.append((variant, PercevalGeometryShaverBackend, {"M": 6}, 0.01, beta, dt, steps, N, seed, False))
            
    # nu0 regime sweep
    for nu0 in nu0_regimes:
        for seed in seeds:
            variant = f"D_nu0_{nu0}"
            tasks.append((variant, PercevalGeometryShaverBackend, {"M": 6}, nu0, beta, dt, steps, 1000, seed, False))
            
    receipts = []
    out_dir = Path("/home/allaun/Documents/Research Stack/shared-data/artifacts/gsp/sweeps")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_run_wrapper, t): t for t in tasks}
        
        for future in as_completed(futures):
            variant, seed, receipt, trace = future.result()
            print(f"Completed {variant} Seed {seed} (L2: {receipt['metrics']['mean_l2_error']:.4f})")
            receipts.append(receipt)
            with open(out_dir / f"trace_{variant}_seed_{seed}.json", "w") as f:
                json.dump(trace, f, indent=2)
                
    with open(out_dir / "sweep_report.json", "w") as f:
        json.dump(receipts, f, indent=2)
        
    print("Sweeps completed.")

if __name__ == "__main__":
    run_sweeps()
