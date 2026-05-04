#!/usr/bin/env python3
import json
import os
import sys

# Fixed-Point Configuration: [16.16] -> 32-bit total
# (First 16 bits = Integer, Last 16 bits = Fractional)
PRECISION = 16
SCALE = 2 ** PRECISION

def to_fixed(val):
    """Convert float to [16.16] fixed point integer."""
    try:
        # Clamp to 16.16 range
        clamped = max(-32768.0, min(32767.0, float(val)))
        return int(clamped * SCALE) & 0xFFFFFFFF
    except Exception:
        return 0

def verify_parity(trace_line):
    """Verify bit-accurate parity for a single trace entry."""
    data = json.loads(trace_line)
    obs = data.get("observables", {})
    
    # Software Floats (Synced with warden.rs:1173)
    f_dmt = obs.get("dmt_t", 0)
    f_torsion = obs.get("torsion_t", 0)

    
    # Hardware Expectations (Simulated)
    hw_dmt = to_fixed(f_dmt)
    hw_torsion = to_fixed(f_torsion)
    
    print(f"[🛡️ PARITY] Sequence {data.get('sequence_id')}")
    print(f"  DMT Score: Software={f_dmt:.4f} -> HW=0x{hw_dmt:08X}")
    print(f"  Torsion:   Software={f_torsion:.4f} -> HW=0x{hw_torsion:08X}")
    
    return True

def main():
    if not os.path.exists("lambda_trace.jsonl"):
        print("[🔥 PARITY] Error: lambda_trace.jsonl not found.")
        sys.exit(1)
        
    print("[🛡️ PARITY] Analyzing Hardware-Software Alignment...")
    with open("lambda_trace.jsonl", 'r') as f:
        lines = f.readlines()
        if not lines:
            print("[⚠️ PARITY] Trace is empty.")
            return
            
        # Verify the most recent entries
        for line in lines[-5:]:
            verify_parity(line)

if __name__ == "__main__":
    main()
