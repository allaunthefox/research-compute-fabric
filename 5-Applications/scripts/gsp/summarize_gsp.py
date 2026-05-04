import json
import csv
import numpy as np
from pathlib import Path

def aggregate_metrics():
    out_dir = Path("/home/allaun/Documents/Research Stack/shared-data/artifacts/gsp")
    
    with open(out_dir / "multi_seed_report.json", "r") as f:
        receipts = json.load(f)
        
    # Group by variant
    variants = {}
    for r in receipts:
        v = r["variant"]
        if v not in variants:
            variants[v] = []
        variants[v].append(r)
        
    summary = []
    
    for v, runs in variants.items():
        l2_list = [r["metrics"]["mean_l2_error"] for r in runs]
        corr_list = [r["metrics"]["corr_omega_etail"] for r in runs]
        penalty_list = [r["metrics"]["overdamping_penalty"] for r in runs]
        sat_list = [r["metrics"]["q16_sat_count"] for r in runs]
        drift_list = [r["metrics"]["energy_drift"] for r in runs]
        shock_list = [r["metrics"]["shock_overshoot"] for r in runs]
        runtime_list = [r["metrics"]["runtime_s"] for r in runs]
        closure_err_list = [r["metrics"].get("closure_error", 0.0) for r in runs]
        closure_lag_list = [r["metrics"].get("closure_phase_lag", 0.0) for r in runs]
        failures = sum(1 for r in runs if r["steps_completed"] < 500)
        
        summary.append({
            "variant": v,
            "mean_L2": float(np.mean(l2_list)),
            "std_L2": float(np.std(l2_list)),
            "mean_corr_Ω_Etail": float(np.mean(corr_list)),
            "std_corr_Ω_Etail": float(np.std(corr_list)),
            "mean_closure_error": float(np.mean(closure_err_list)),
            "mean_closure_phase_lag": float(np.mean(closure_lag_list)),
            "mean_overdamping_penalty": float(np.mean(penalty_list)),
            "mean_saturation_count": float(np.mean(sat_list)),
            "mean_energy_drift": float(np.mean(drift_list)),
            "mean_shock_overshoot": float(np.mean(shock_list)),
            "mean_runtime": float(np.mean(runtime_list)),
            "failure_count": failures
        })
        
    # Save JSON summary
    with open(out_dir / "wedge_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    # Save CSV metrics_by_seed
    with open(out_dir / "metrics_by_seed.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["variant", "seed", "mean_L2", "corr_omega_etail", "closure_error", "closure_phase_lag", "energy_drift", "shock_overshoot", "overdamping_penalty", "saturation_count", "runtime", "steps"])
        for r in receipts:
            m = r["metrics"]
            writer.writerow([
                r["variant"], r["seed"], m["mean_l2_error"], m["corr_omega_etail"], 
                m.get("closure_error", 0.0), m.get("closure_phase_lag", 0.0),
                m["energy_drift"], m["shock_overshoot"], m["overdamping_penalty"], 
                m["q16_sat_count"], m["runtime_s"], r["steps_completed"]
            ])

    # Save run_receipts.jsonl
    with open(out_dir / "run_receipts.jsonl", "w") as f:
        for r in receipts:
            f.write(json.dumps(r) + "\n")
            
    # Save aggregated_metrics.json (just the summary)
    with open(out_dir / "aggregated_metrics.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Summary generation complete. Check wedge_summary.json")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    aggregate_metrics()
