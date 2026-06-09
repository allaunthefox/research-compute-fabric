from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import json
import subprocess
from pathlib import Path
import time
from typing import Optional
import sys

# Add path to projection engine
sys.path.append("/home/allaun/Research Stack/5-Applications/cff/nuvmap")
from projection_engine import NUVMAPProjectionEngine

app = FastAPI(title="Sovereign Surface")

# Paths
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
EQUATION_FOREST = Path("/home/allaun/Documents/Research Stack/data/equations_forest.jsonl")

# Serve static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def get_index():
    with open(STATIC_DIR / "index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/forest")
async def get_forest():
    equations = []
    if EQUATION_FOREST.exists():
        with open(EQUATION_FOREST, "r") as f:
            for line in f:
                equations.append(json.loads(line))
    return {"equations": equations}

@app.get("/api/nuvmap")
async def get_nuvmap():
    receipt_path = Path("/home/allaun/Research Stack/shared-data/data/stack_solidification/braid_shock_receipt.json")
    if not receipt_path.exists():
        return {"error": f"Receipt not found at {receipt_path}"}
    
    with open(receipt_path, "r") as f:
        receipt = json.load(f)
        
    u_q16 = receipt.get("u_final_q16", [])
    q_q16 = receipt.get("q_final_q16", [])
    r_q16 = receipt.get("r_final_q16", [])
    
    eigenmass_data = []
    for i in range(len(u_q16)):
        ui = u_q16[i] / 65536.0
        qi = q_q16[i] / 65536.0
        ri = r_q16[i] / 65536.0
        
        if ri > 0.05:
            chiral_state = "chiral_scarred"
        else:
            chiral_state = "achiral_stable"
            
        eigenmass_data.append({
            "equation_id": i,
            "amvr": ui,
            "avmr": qi,
            "chiral_residual": ri,
            "chiral_state": chiral_state
        })
        
    engine = NUVMAPProjectionEngine(total_qubit_budget=2000)
    surface = engine.project(eigenmass_data)
    
    cells_json = []
    for c in surface.cells:
        cells_json.append({
            "u_i": c.u_i,
            "v_i": c.v_i,
            "k_i": c.k_i,
            "E_i": c.E_i,
            "R_i": c.R_i,
            "chi_i": c.chi_i,
            "S_i": c.S_i,
            "L_i": c.L_i,
            "q_i": c.q_i,
            "admissible": c.admissible,
            "equation_id": c.equation_id,
            "fingerprint": c.fingerprint
        })
        
    return {
        "summary": engine.summary(),
        "cells": cells_json
    }

def get_gpu_load():
    try:
        res = subprocess.check_output(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,power.draw", "--format=csv,noheader,nounits"])
        util, mem, power = res.decode().strip().split(",")
        return {"util": int(util), "mem": int(mem), "power": float(power)}
    except:
        return {"util": 0, "mem": 0, "power": 0}

@app.get("/api/telemetry")
async def get_telemetry():
    gpu = get_gpu_load()
    # Check if derivation script is running
    is_deriving = False
    try:
        res = subprocess.check_output(["ps", "-ef"])
        if b"derive_hyper_equation.py" in res:
            is_deriving = True
    except:
        pass
    
    # Statistical ETC: If deriving and GPU is pinned, estimate ~3-5 mins total
    etc = "Calculating..."
    if is_deriving and gpu["util"] > 80:
        etc = "2.5m" # Heuristic for R1 8B on this hardware
    elif not is_deriving:
        etc = "0s"

    return {
        "gpu": gpu,
        "is_deriving": is_deriving,
        "etc": etc,
        "phi": 0.3547
    }

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            telemetry = await get_telemetry()
            await websocket.send_json({
                "type": "heartbeat",
                **telemetry
            })
            import asyncio
            await asyncio.sleep(2)
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
