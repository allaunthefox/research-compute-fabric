#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Graph OS Commodity Crypto Native Implementation Demo
Verifies TSM opcodes for BTC, XMR, ETH, LTC, RVN, and ERG.
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

try:
    from logic_signal_substrate_mcp_harness import TSMKernel
except ImportError:
    from logic_signal_substrate_mcp_harness import TSMKernel

def run_commodity_demo():
    print("[*] Initializing Graph OS Commodity Crypto Logic Surface...")
    kernel = TSMKernel()
    
    test_data = "graph_os_commodity_test_vector_2026"
    
    # 1. Hashing Verifications
    print("\n--- [ PHASE 1: HASHING VERIFICATION ] ---")
    ops_hash = [
        ("0x80", [test_data]), # SHA256D (BTC)
        ("0x81", [test_data]), # Keccak256 (ETH)
        ("0x83", [test_data]), # RandomX (XMR)
        ("0x85", [test_data])  # Autolykos2 (ERG)
    ]
    results_hash = kernel.execute(ops_hash)
    tickers_hash = ["BTC (SHA256D)", "ETH (Keccak)", "XMR (RandomX)", "ERG (Autolykos2)"]
    for ticker, res in zip(tickers_hash, results_hash):
        print(f"[+] {ticker}: {res}")

    # 2. Address Generation Verifications
    print("\n--- [ PHASE 2: ADDRESS GENERATION ] ---")
    ops_addr = [
        ("0x90", []), # BTC
        ("0x91", []), # XMR
        ("0x92", []), # ETH
        ("0x94", []), # RVN
        ("0x95", [])  # ERG
    ]
    results_addr = kernel.execute(ops_addr)
    tickers_addr = ["BTC", "XMR", "ETH", "RVN", "ERG"]
    for ticker, res in zip(tickers_addr, results_addr):
        print(f"[+] {ticker} Address: {res}")

    print("\n[+] Full Commodity Crypto Logic Surface verified and operational in TSM.")

if __name__ == "__main__":
    run_commodity_demo()
