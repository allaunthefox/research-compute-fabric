#!/usr/bin/env python3
import argparse
import os
import sys
import time
import serial
import json
from pathlib import Path

# Protocol Constants
SYNC_REQ = 0xAA
SYNC_RES = 0x55

def verify_trace(port, baud, program, initial_stack, gold_result):
    print(f"Connecting to {port} at {baud} baud...")
    try:
        ser = serial.Serial(port, baud, timeout=2)
    except Exception as e:
        print(f"Failed to open port: {e}")
        return False

    # Construct Packet
    # [SYNC_REQ, prog_len, ...prog..., stack_len, ...stack...]
    packet = bytearray()
    packet.append(SYNC_REQ)
    packet.append(len(program))
    packet.extend(program)
    
    packet.append(len(initial_stack))
    for val in initial_stack:
        # 32-bit Big Endian
        packet.extend(val.to_bytes(4, byteorder='big', signed=True))

    print(f"Sending packet: {packet.hex()}")
    ser.write(packet)
    ser.flush()

    # Wait for Response
    print("Waiting for response...")
    sync = ser.read(1)
    if not sync or sync[0] != SYNC_RES:
        print(f"Invalid sync byte received: {sync.hex() if sync else 'TIMEOUT'}")
        ser.close()
        return False

    res_len_byte = ser.read(1)
    if not res_len_byte:
        print("Timeout reading response length")
        ser.close()
        return False
    
    res_len = res_len_byte[0]
    results = []
    for _ in range(res_len):
        data = ser.read(4)
        if len(data) < 4:
            print("Truncated result received")
            break
        results.append(int.from_bytes(data, byteorder='big', signed=True))

    ser.close()
    
    print(f"Received results: {results}")
    if results and results[0] == gold_result:
        print("SUCCESS: Result matches gold trace!")
        return True
    else:
        print(f"FAILURE: Result {results[0] if results else 'NONE'} does not match gold {gold_result}")
        return False

def main():
    root = Path("/home/allaun/Documents/Research Stack")
    manifest_path = root / "shared-data/burgers_avm_trace_manifest.json"
    gold_path = root / "shared-data/burgers_avm_gold_traces.json"

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    with open(gold_path, 'r') as f:
        gold_data = json.load(f)

    port = "/dev/ttyUSB1" # Default, maybe override from env
    baud = manifest["uart_config"]["baud_rate"]

    results = []

    # Test nu_eff
    print("\n--- Verifying nu_eff ---")
    nu_prog = gold_data["nu_eff"]["program"]
    # Stack inputs are [omega, nu0] based on nuEffProgram structure
    nu_inputs = [gold_data["nu_eff"]["inputs"]["omega"], gold_data["nu_eff"]["inputs"]["nu0"]]
    nu_gold = gold_data["nu_eff"]["final_result"]
    
    pass_nu = verify_trace(port, baud, nu_prog, nu_inputs, nu_gold)
    results.append({"kernel": "nu_eff", "status": "pass" if pass_nu else "fail"})

    # Test q_eff
    print("\n--- Verifying q_eff ---")
    q_prog = gold_data["q_eff"]["program"]
    # Stack inputs are [omega, q0] based on qEffProgram structure
    q_inputs = [gold_data["q_eff"]["inputs"]["omega"], gold_data["q_eff"]["inputs"]["q0"]]
    q_gold = gold_data["q_eff"]["final_result"]
    
    pass_q = verify_trace(port, baud, q_prog, q_inputs, q_gold)
    results.append({"kernel": "q_eff", "status": "pass" if pass_q else "fail"})

    # Generate parity report
    report_path = root / "shared-data/burgers_avm_fpga_loopback_report.md"
    with open(report_path, 'w') as f:
        f.write("# Burgers AVM FPGA Loopback Report\n\n")
        f.write(f"- Timestamp: {time.ctime()}\n")
        f.write(f"- Port: {port}\n")
        f.write(f"- Baud: {baud}\n")
        f.write("| Kernel | Status |\n")
        f.write("| --- | --- |\n")
        for r in results:
            f.write(f"| {r['kernel']} | {r['status']} |\n")
    
    print(f"\nReport saved to: {report_path}")

if __name__ == "__main__":
    main()
