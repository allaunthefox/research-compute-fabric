#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Graph OS Meta-MoE Zcash Accumulation Algorithm
Expert: DeepSeek_Tunnel (Market Impact Analysis)
Strategy: Low-Impact TWAP with explicit loss-aware action policy
Objective: Acquire ~3 ZEC without triggering "Planck Scope" (IRS/Market) panic.
"""

import time
import json
import random
import hashlib
import asyncio
import os
from datetime import datetime, timezone
from z_bridge_protocol import ZBridgeProtocol
from coinbase_client_helper import CoinbaseClient
try:
    from scripts.market_action_policy import MarketActionPolicy
except ImportError:
    from market_action_policy import MarketActionPolicy

class ZecAccumulator:
    def __init__(self, target_zec=3.0, duration_hours=4):
        self.target_zec = target_zec
        self.acquired_zec = 0.0
        self.total_spent_usd = 0.0
        self.duration_seconds = duration_hours * 3600
        self.start_time = time.time()
        self.bridge = ZBridgeProtocol()
        self.policy = MarketActionPolicy.from_env(prefix="ZEC_ACTION")
        self.client = CoinbaseClient(policy=self.policy)
        self.market_avg_price = 0.0
        self.last_market_price = None
        self.adverse_streak = 0
        self.last_price_snapshot = {}
        # ZEC-2 fix: record initial price separately for fair performance benchmark.
        # market_avg_price drifts via EMA(α=0.05) and is not a stable reference.
        self.initial_price: float = 0.0
        
    async def get_live_price(self):
        snapshot = await self.client.get_zec_price_snapshot()
        self.last_price_snapshot = snapshot
        price = float(snapshot.get("market_price", 0.0) or 0.0)
        if self.market_avg_price == 0.0:
            self.market_avg_price = price
            self.initial_price = price  # ZEC-2: snapshot at start for clean benchmark
        else:
            self.market_avg_price = (self.market_avg_price * 0.95) + (price * 0.05)
        return price

    def calculate_entry_reference(self, current_price):
        basis_price = self.market_avg_price if self.market_avg_price > 0.0 else current_price
        return self.policy.entry_reference_price(basis_price)

    async def run_live_accumulation(self):
        print(f"[*] Starting LIVE ZEC Accumulation: Target {self.target_zec} ZEC")
        print("[*] Strategy: TWAP + explicit risk-aware action policy")
        print(f"[*] Policy: {self.policy.brief()}")
        
        intervals = 10 
        zec_per_nibble = self.target_zec / intervals
        
        while self.acquired_zec < self.target_zec:
            current_price = await self.get_live_price()
            if current_price == 0.0:
                await asyncio.sleep(self.policy.activation_pause_seconds)
                continue

            entry_reference = self.calculate_entry_reference(current_price)
            loss_reinforcement = self.policy.detects_loss_reinforcement(
                current_price=current_price,
                reference_price=entry_reference,
                last_price=self.last_market_price,
                adverse_streak=self.adverse_streak,
            )
            wait_seconds = self.policy.activation_pause_for(
                loss_reinforcement=loss_reinforcement,
                adverse_streak=self.adverse_streak,
            )
            
            if current_price <= entry_reference:
                # Calculate USD amount for nibble
                buy_usd = zec_per_nibble * current_price
                print(f"[LIVE BUY] Triggering buy for ${buy_usd:.2f} ZEC...")
                
                order_result = await self.client.place_market_buy(buy_usd)
                
                if order_result.get("success"):
                    # ZEC-1 fix: use actual filled quantity, not planned nibble size.
                    # Partial fills are common for IOC market orders on illiquid markets.
                    filled_str = order_result.get("filled_size")
                    try:
                        actual_fill = float(filled_str) if filled_str else zec_per_nibble
                    except (ValueError, TypeError):
                        # Exchange returned non-numeric filled_size (e.g. "N/A")
                        actual_fill = zec_per_nibble
                    self.acquired_zec += actual_fill
                    actual_usd = actual_fill * current_price
                    self.total_spent_usd += actual_usd
                    self.bridge.update_accumulation(actual_fill)
                    print(f"      SUCCESS: Acquired {actual_fill:.4f} ZEC at ${current_price:.2f}"
                          + (f" (partial: planned {zec_per_nibble:.4f})" if abs(actual_fill - zec_per_nibble) > 1e-8 else ""))
                    self.adverse_streak = 0
                else:
                    print(f"      FAILURE: {order_result.get('error_response', 'Unknown Error')}")
            else:
                if loss_reinforcement:
                    self.adverse_streak += 1
                    print(
                        "[LIVE PAUSE] "
                        f"Price ${current_price:.2f} > Entry Ref ${entry_reference:.2f}. "
                        f"Adverse reinforcement detected; activation pause {wait_seconds}s."
                    )
                else:
                    self.adverse_streak = 0
                    print(
                        "[LIVE WAIT] "
                        f"Price ${current_price:.2f} > Entry Ref ${entry_reference:.2f}. "
                        f"Monitoring with base pause {wait_seconds}s."
                    )
            
            self.last_market_price = current_price
            await asyncio.sleep(wait_seconds)
            
        avg_cost = self.total_spent_usd / self.acquired_zec
        # ZEC-2 fix: benchmark against initial_price (snapshot at first fetch), not
        # market_avg_price (EMA α=0.05 that drifts over the whole run duration).
        reference_price = self.initial_price if self.initial_price > 0.0 else self.market_avg_price
        performance = ((reference_price - avg_cost) / reference_price) * 100
        
        print("\n[+] LIVE ACQUISITION SEQUENCE COMPLETE")
        print(f"    Total ZEC: {self.acquired_zec:.4f}")
        print(f"    Avg Cost:  ${avg_cost:.2f}")
        print(f"    Performance: {performance:+.2f}% vs Initial Price (${reference_price:.2f})")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    accumulator = ZecAccumulator()
    asyncio.run(accumulator.run_live_accumulation())
