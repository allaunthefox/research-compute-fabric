import numpy as np
import json
import time
import hashlib
from pathlib import Path
from typing import Optional
from concurrent.futures import ProcessPoolExecutor, as_completed

from .burgers_triad_core import float_to_q16, q16_to_float, q16_mul, rk2_step, energy3, Q16_ONE, get_sat_count, reset_sat_count
from .reference_tail_oracle import ReferenceTailOracle
from .backends import VirtualSubstrateBackend, SoftwareTriangleBackend, ClassicalHeuristicBackend, LearnedClosureBaselineBackend, EddyViscosityROMBackend

def calculate_metrics(a_history, u_ref_history, E_tail_history, omega_history, dt, sat_count):
    # L2 error vs reference
    l2_errors = []
    for a, (a1_ref, a2_ref, a3_ref) in zip(a_history, u_ref_history):
        err = np.sqrt((a[0]-a1_ref)**2 + (a[1]-a2_ref)**2 + (a[2]-a3_ref)**2)
        l2_errors.append(err)
    mean_l2 = np.mean(l2_errors)
    
    # corr(Omega, E_tail)
    if len(omega_history) > 1 and np.std(omega_history) > 1e-9 and np.std(E_tail_history) > 1e-9:
        corr = np.corrcoef(omega_history, E_tail_history)[0, 1]
    else:
        corr = 0.0
        
    # Phase lag
    if len(omega_history) > 10:
        # Subtract mean
        o_zm = omega_history - np.mean(omega_history)
        e_zm = E_tail_history - np.mean(E_tail_history)
        xcorr = np.correlate(o_zm, e_zm, mode='full')
        lag = np.argmax(xcorr) - (len(omega_history) - 1)
        phase_lag = lag
    else:
        phase_lag = 0
        
    # Closure Error (Scale Omega to E_tail scale and compute MAE)
    if len(omega_history) > 0 and np.std(omega_history) > 1e-9:
        scale = np.std(E_tail_history) / np.std(omega_history)
        scaled_omega = [o * scale for o in omega_history]
        closure_error = np.mean([abs(o - e) for o, e in zip(scaled_omega, E_tail_history)])
    else:
        closure_error = 0.0
        
    # Energy
    energy_drift = (energy3(tuple(int(x * Q16_ONE) for x in a_history[-1])) - energy3(tuple(int(x * Q16_ONE) for x in a_history[0]))) / Q16_ONE
    
    # Oracle true energy drift
    oracle_e0 = 0.5 * sum(x**2 for x in u_ref_history[0])
    oracle_ef = 0.5 * sum(x**2 for x in u_ref_history[-1])
    oracle_drift = oracle_ef - oracle_e0
    
    overdamping_penalty = abs(energy_drift - oracle_drift)
    
    # Shock overshoot (max mode amplitude beyond initial max)
    max_mode = max(max(abs(x) for x in step) for step in a_history)
    shock_overshoot = max(0.0, max_mode - 1.0)
    
    # Digests
    omega_bytes = np.array(omega_history, dtype=np.float64).tobytes()
    etail_bytes = np.array(E_tail_history, dtype=np.float64).tobytes()
    omega_digest = hashlib.sha256(omega_bytes).hexdigest()
    etail_digest = hashlib.sha256(etail_bytes).hexdigest()

    return {
        "mean_l2_error": float(mean_l2),
        "corr_omega_etail": float(corr),
        "closure_phase_lag": int(phase_lag),
        "closure_error": float(closure_error),
        "energy_drift": float(energy_drift),
        "shock_overshoot": float(shock_overshoot),
        "overdamping_penalty": float(overdamping_penalty),
        "q16_sat_count": int(sat_count),
        "stability_time": float(len(a_history) * dt),
        "omega_series_digest": omega_digest,
        "etail_series_digest": etail_digest
    }

def run_simulation(
    backend: VirtualSubstrateBackend,
    nu0_float: float,
    beta_float: float,
    dt_float: float,
    steps: int,
    N_shots: int,
    seed: int,
    variant: str,
    use_memory_kernel: bool = False
):
    start_time = time.time()
    reset_sat_count()
    
    oracle = ReferenceTailOracle(N=256, nu=nu0_float)
    a_init = (1.0, 0.3, 0.1)
    oracle.initialize(*a_init)
    
    a_q16 = (float_to_q16(a_init[0]), float_to_q16(a_init[1]), float_to_q16(a_init[2]))
    nu0 = float_to_q16(nu0_float)
    beta = float_to_q16(beta_float)
    dt = float_to_q16(dt_float)
    
    a_history, u_ref_history, E_tail_history, omega_history, avmr_trace = [], [], [], [], []
    
    hist_digest = "none"

    for step in range(steps):
        oracle.step(dt_float)
        
        theta = backend.encode(a_q16)
        sub_state = backend.program(theta)
        hist = backend.sample(sub_state, N_shots, seed + step)
        
        if step == steps - 1:
            hist_str = json.dumps(hist, sort_keys=True).encode("utf-8")
            hist_digest = hashlib.sha256(hist_str).hexdigest()
            
        omega_q16 = backend.witness(hist)
        
        # Memory kernel logic
        if use_memory_kernel and len(omega_history) >= 2:
            o_prev1 = float_to_q16(omega_history[-1])
            o_prev2 = float_to_q16(omega_history[-2]) if len(omega_history) > 1 else o_prev1
            # Simple EMA/history combination: 0.5*current + 0.3*prev1 + 0.2*prev2
            w_curr = q16_mul(omega_q16, float_to_q16(0.5))
            w_prev1 = q16_mul(o_prev1, float_to_q16(0.3))
            w_prev2 = q16_mul(o_prev2, float_to_q16(0.2))
            omega_q16_eff = w_curr + w_prev1 + w_prev2
        else:
            omega_q16_eff = omega_q16
            
        if variant == "B":
            nu_eff = nu0
        else:
            nu_eff = nu0 + q16_mul(beta, omega_q16_eff)
            
        digest = backend.digest(a_q16, theta, hist, omega_q16, nu_eff)
        avmr_trace.append({
            "step": step,
            "a": [q16_to_float(x) for x in a_q16],
            "omega": q16_to_float(omega_q16_eff),
            "nu_eff": q16_to_float(nu_eff),
            "digest": digest
        })
        
        a_history.append([q16_to_float(x) for x in a_q16])
        u_ref_history.append(oracle.a_k_extracted())
        E_tail_history.append(oracle.E_tail())
        omega_history.append(q16_to_float(omega_q16_eff))
        
        a_q16 = rk2_step(a_q16, nu_eff, dt)
        
        if any(abs(q16_to_float(x)) > 10.0 for x in a_q16):
            break

    sat_count = get_sat_count()
    metrics = calculate_metrics(a_history, u_ref_history, E_tail_history, omega_history, dt_float, sat_count)
    metrics["runtime_s"] = time.time() - start_time
    metrics["histogram_digest"] = hist_digest
    
    receipt = {
        "run_id": f"gsp_v0.1_{variant}_{seed}",
        "variant": variant,
        "backend": backend.__class__.__name__,
        "nu0": nu0_float,
        "beta": beta_float,
        "dt": dt_float,
        "N_shots": N_shots,
        "seed": seed,
        "use_memory_kernel": use_memory_kernel,
        "steps_completed": len(a_history),
        "metrics": metrics,
        "claim_state": "CALIBRATED_ENGINEERING_DELTA_CANDIDATE"
    }
    return receipt, avmr_trace

def _run_wrapper(args):
    variant, backend_cls, kwargs, nu0, beta, dt, steps, N_shots, seed, use_memory_kernel = args
    backend = backend_cls(**kwargs)
    receipt, trace = run_simulation(backend, nu0, beta, dt, steps, N_shots, seed, variant, use_memory_kernel)
    return variant, seed, receipt, trace

def run_benchmark_wedge():
    print("Starting full GSP-v0.1 Verification Matrix...")
    
    nu0, beta, dt = 0.01, 0.5, 0.01
    steps = 500
    N_shots = 1000
    seeds = list(range(42, 51)) # 9 seeds
    
    variants_parallel = [
        ("A", SoftwareTriangleBackend, {}),
        ("B", SoftwareTriangleBackend, {}),
        ("C", ClassicalHeuristicBackend, {"c1": 0.1, "c2": 0.1, "c3": 0.01}),
        ("D", PercevalGeometryShaverBackend, {"M": 6}),
        ("D_mem", PercevalGeometryShaverBackend, {"M": 6}), # Variant D with memory kernel
        ("F", LearnedClosureBaselineBackend, {}),
        ("G", EddyViscosityROMBackend, {"c_smag": 0.1})
    ]
    
    tasks_parallel = []
    for variant, backend_cls, kwargs in variants_parallel:
        for seed in seeds:
            use_mem = (variant == "D_mem")
            tasks_parallel.append((variant, backend_cls, kwargs, nu0, beta, dt, steps, N_shots, seed, use_mem))
            
    receipts = []
    out_dir = Path("/home/allaun/Documents/Research Stack/shared-data/artifacts/gsp")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_run_wrapper, t): t for t in tasks_parallel}
        for future in as_completed(futures):
            variant, seed, receipt, trace = future.result()
            print(f"Completed Variant {variant} Seed {seed} ({receipt['steps_completed']} steps, L2: {receipt['metrics']['mean_l2_error']:.4f})")
            receipts.append(receipt)
            with open(out_dir / f"trace_variant_{variant}_seed_{seed}.json", "w") as f:
                json.dump(trace, f, indent=2)
                
    # Run E sequentially and with N_shots=100 to avoid API 400 / rate limits
    print("Running Variant E (Remote) sequentially to respect API limits...")
    for seed in seeds:
        print(f"Starting Variant E Seed {seed}...")
        backend = QuandelaRemoteBackend(target="sim:ascella", M=12)
        receipt, trace = run_simulation(backend, nu0, beta, dt, steps, 100, seed, "E")
        print(f"Completed Variant E Seed {seed} ({receipt['steps_completed']} steps, L2: {receipt['metrics']['mean_l2_error']:.4f})")
        receipts.append(receipt)
        with open(out_dir / f"trace_variant_E_seed_{seed}.json", "w") as f:
            json.dump(trace, f, indent=2)
            
    with open(out_dir / "multi_seed_report.json", "w") as f:
        json.dump(receipts, f, indent=2)
        
    print(f"Matrix complete. Generated {len(receipts)} receipts.")

if __name__ == "__main__":
    run_benchmark_wedge()
