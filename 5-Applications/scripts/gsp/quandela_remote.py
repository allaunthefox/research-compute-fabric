import numpy as np
import perceval as pcvl
import os
from .backends import VirtualSubstrateBackend

# (Assuming PercevalGeometryShaverBackend is already here)

class QuandelaRemoteBackend(VirtualSubstrateBackend):
    def __init__(self, target="sim:ascella", M=12, exhaust_modes=(3, 4, 5)):
        self.M = M
        self.exhaust_modes = exhaust_modes
        
        token = ""
        try:
            with open("/home/allaun/Documents/Research Stack/.env", "r") as f:
                for line in f:
                    if line.startswith("QUANDELA_API_KEY"):
                        token = line.split("=")[1].strip()
        except:
            pass
            
        if not token:
            raise ValueError("QUANDELA_API_KEY not found in .env")
            
        self.rp = pcvl.RemoteProcessor(target, token)
        
    def encode(self, a: tuple[int, int, int]) -> dict:
        Q16_ONE = 1 << 16
        a_f = [x / Q16_ONE for x in a]
        
        norm = np.linalg.norm(a_f)
        if norm < 1e-9:
            return {"theta": [0.0, 0.0, 0.0], "norm": 0.0}
            
        theta = [float(np.pi * (x / norm)) for x in a_f]
        return {"theta": theta, "norm": float(norm)}

    def program(self, theta: dict) -> dict:
        return {
            "theta": theta["theta"],
            "norm": theta["norm"],
            "M": self.M
        }

    def sample(self, substrate_state: dict, N: int, seed: int) -> dict:
        M = substrate_state["M"]
        theta = substrate_state["theta"]
        norm = substrate_state["norm"]
        
        if norm < 1e-9:
            return {str(i): 0.0 for i in range(M)}
            
        circuit = pcvl.Circuit(M)
        for i in range(3):
            circuit.add(i, pcvl.PS(theta[i]))
            
        for i in range(M - 1):
            circuit.add((i, i+1), pcvl.BS())
            
        self.rp.set_circuit(circuit)
        
        input_state = pcvl.BasicState([1, 1, 1] + [0] * (M - 3))
        self.rp.with_input(input_state)
        self.rp.min_detected_photons_filter(3)
        
        import time
        sampler = pcvl.algorithm.Sampler(self.rp, max_shots_per_call=100) # smaller chunks
        res = None
        for attempt in range(3):
            try:
                time.sleep(0.5) # rate limit mitigation
                res = sampler.sample_count(N)
                break
            except Exception as e:
                print(f"Sampling error on attempt {attempt+1}:", e)
                time.sleep(2.0)
                
        hist = {str(i): 0.0 for i in range(M)}
        if res is not None and "results" in res:
            for state, count in res["results"].items():
                prob = count / N
                for mode, photons in enumerate(state):
                    hist[str(mode)] += photons * prob
        else:
            print("Warning: Remote API returned None or invalid result after retries.")
            
        for k in hist:
            hist[k] *= (norm**2)
            
        return hist

    def witness(self, histogram: dict) -> int:
        omega_float = 0.0
        for m in self.exhaust_modes:
            omega_float += histogram.get(str(m), 0.0)
            
        Q16_ONE = 1 << 16
        return int(omega_float * Q16_ONE)
