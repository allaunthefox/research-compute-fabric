# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Paper Trading Agent - Hutter 8-Hour Stress Test

Single agent: 50 USDC starting capital
Runs for 8 hours (simulated or real-time)
Fragments trades across pools
Tracks profitability, fragments, recoveries
Survives or fails to 0 balance

Multi-instance: parallel runs with different seeds
Find which agents survive longest

DAG Record: Complete history of every trade, decision, and state change
Allows replay and analysis of what caused survival/failure
Live market prediction to guide trading decisions
"""

import json
import time
import random
import os
import hashlib
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple

PHI = 1.618033988749895
SIMULATION_SPEED = 100  # 1 simulated second = 1/100 real seconds (for faster testing)

# ============================================================================
# Pool Model
# ============================================================================

@dataclass
class Pool:
    name: str
    token_a: str
    token_b: str
    reserve_a: float
    reserve_b: float
    fee_bps: int = 25

    def swap(self, amount_in: float, is_a_to_b: bool, slippage_variance: float = 0.5) -> tuple:
        """Execute swap with variance (real pools move)"""
        fee_rate = 1.0 - (self.fee_bps / 10000)
        amount_in_after_fee = amount_in * fee_rate

        # Add slippage variance
        variance = random.gauss(1.0, slippage_variance / 100)
        amount_in_after_fee *= variance

        if is_a_to_b:
            k = self.reserve_a * self.reserve_b
            new_reserve_a = self.reserve_a + amount_in_after_fee
            new_reserve_b = k / new_reserve_a
            amount_out = self.reserve_b - new_reserve_b
            self.reserve_a = new_reserve_a
            self.reserve_b = new_reserve_b
        else:
            k = self.reserve_a * self.reserve_b
            new_reserve_b = self.reserve_b + amount_in_after_fee
            new_reserve_a = k / new_reserve_b
            amount_out = self.reserve_a - new_reserve_a
            self.reserve_a = new_reserve_a
            self.reserve_b = new_reserve_b

        fee_paid = amount_in * (self.fee_bps / 10000)
        return max(0, amount_out), fee_paid

    def get_price(self, is_a_to_b: bool) -> float:
        if is_a_to_b:
            return self.reserve_b / self.reserve_a
        else:
            return self.reserve_a / self.reserve_b


# ============================================================================
# DAG Node for immutable history
# ============================================================================

@dataclass
class DAGNode:
    """Directed Acyclic Graph node for trade history"""
    node_id: str
    timestamp: int  # Seconds since start
    event_type: str  # "trade", "recovery", "checkpoint", "prediction", "failure"
    parent_hash: Optional[str]  # Hash of previous node (chain)
    data: Dict = field(default_factory=dict)
    hash: Optional[str] = None  # Computed hash

    def compute_hash(self) -> str:
        """SHA256 hash of this node (immutable)"""
        content = json.dumps({
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "parent_hash": self.parent_hash,
            "data": self.data
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class PaperTraderState:
    agent_id: int
    session_id: str
    balance_usdc: float
    balance_sol: float = 10.0
    balance_kot: float = 0.0

    lifetime_profit: float = 0.0
    lifetime_loss: float = 0.0
    num_trades: int = 0
    successful_fragments: int = 0
    failed_fragments: int = 0
    recovery_attempts: int = 0
    recovery_successes: int = 0

    went_negative_at: Optional[int] = None
    lowest_balance: float = 0.0
    time_alive_seconds: int = 0

    trade_history: List[Dict] = field(default_factory=list)
    dag_nodes: List[DAGNode] = field(default_factory=list)
    dag_heads: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "balance_usdc": self.balance_usdc,
            "balance_sol": self.balance_sol,
            "lifetime_profit": self.lifetime_profit,
            "lifetime_loss": self.lifetime_loss,
            "num_trades": self.num_trades,
            "went_negative_at": self.went_negative_at,
            "lowest_balance": self.lowest_balance,
            "time_alive_seconds": self.time_alive_seconds,
            "recovery_success_rate": f"{self.recovery_successes}/{self.recovery_attempts}",
            "trade_history": self.trade_history[-10:],
            "num_dag_nodes": len(self.dag_nodes),
            "dag_heads": self.dag_heads[-3:]  # Last 3 heads
        }


class PaperTrader:
    def __init__(self, agent_id: int, session_id: str, starting_usdc: float = 50.0):
        self.agent_id = agent_id
        self.session_id = session_id
        self.state = PaperTraderState(
            agent_id=agent_id,
            session_id=session_id,
            balance_usdc=starting_usdc
        )

        self.pools = [
            Pool("SOL/USDC", "SOL", "USDC", reserve_a=50000, reserve_b=1250000),
            Pool("USDC/BTC", "USDC", "BTC", reserve_a=2000000, reserve_b=50),
        ]

        self.log_file = f"/tmp/paper_trader_{session_id}_agent_{agent_id}.log"
        self.checkpoint_file = f"/tmp/paper_trader_{session_id}_agent_{agent_id}.json"
        self.dag_file = f"/tmp/paper_trader_{session_id}_agent_{agent_id}_dag.json"

        self.price_history = {"SOL/USDC": [], "USDC/BTC": []}
        self.last_dag_node_hash = None

    def log(self, message: str):
        """Log with timestamp"""
        ts = datetime.now().isoformat()
        line = f"[{ts}] {message}\n"
        with open(self.log_file, "a") as f:
            f.write(line)

    def _add_dag_node(self, event_type: str, data: Dict):
        """Add immutable DAG node to history"""
        node = DAGNode(
            node_id=f"{self.agent_id}_{len(self.state.dag_nodes)}",
            timestamp=self.state.time_alive_seconds,
            event_type=event_type,
            parent_hash=self.last_dag_node_hash,
            data=data
        )
        node.hash = node.compute_hash()
        self.state.dag_nodes.append(node)
        self.last_dag_node_hash = node.hash

        if node.hash not in self.state.dag_heads:
            self.state.dag_heads.append(node.hash)

    def predict_price_direction(self, lookback: int = 5) -> Tuple[str, float]:
        """
        Predict next price direction using:
        1. Momentum (rate of change)
        2. Mean reversion (deviation from moving average)
        3. Volatility (price variance)

        Returns: (predicted_direction, confidence_0_to_1)
        """
        sol_prices = self.price_history.get("SOL/USDC", [])

        if len(sol_prices) < lookback:
            return "UNCERTAIN", 0.0

        recent = sol_prices[-lookback:]

        # 1. Momentum: slope of price
        momentum = (recent[-1] - recent[0]) / recent[0] if recent[0] > 0 else 0

        # 2. Mean reversion: deviation from moving average
        ma = sum(recent) / len(recent)
        deviation = (recent[-1] - ma) / ma if ma > 0 else 0

        # 3. Volatility: std dev of returns
        returns = [(recent[i] - recent[i - 1]) / recent[i - 1] for i in range(1, len(recent)) if recent[i - 1] > 0]
        volatility = math.sqrt(sum(r ** 2 for r in returns) / len(returns)) if returns else 0

        # Combine signals
        momentum_signal = 1.0 if momentum > 0.005 else (-1.0 if momentum < -0.005 else 0.0)
        mr_signal = -1.0 if abs(deviation) > 0.02 else 0.0
        vol_signal = -0.5 if volatility > 0.05 else 0.5

        total_signal = momentum_signal + mr_signal + vol_signal
        direction = "UP" if total_signal > 0.5 else ("DOWN" if total_signal < -0.5 else "UNCERTAIN")
        confidence = min(1.0, abs(total_signal) / 3.0)

        return direction, confidence

    def execute_trade(self, amount_usdc: float, num_fragments: int = 3) -> float:
        """Execute fragmented trade, return net profit/loss"""
        if amount_usdc <= 0 or amount_usdc > self.state.balance_usdc:
            return 0.0

        # Predict direction before trade
        predicted_dir, confidence = self.predict_price_direction()
        self._add_dag_node("prediction", {
            "direction": predicted_dir,
            "confidence": confidence,
            "price": self.pools[0].get_price(True)
        })

        amount_per_fragment = amount_usdc / num_fragments
        total_output_sol = 0.0
        confirmed_fragments = {}

        self._add_dag_node("trade_start", {
            "amount_usdc": amount_usdc,
            "fragments": num_fragments,
            "price_when_executed": self.pools[0].get_price(True)
        })

        # Execute fragments (85% success rate)
        for i in range(num_fragments):
            success = random.random() < 0.85

            if success:
                try:
                    output, fee = self.pools[0].swap(amount_per_fragment, is_a_to_b=True)
                    total_output_sol += output
                    confirmed_fragments[i] = output
                    self.state.successful_fragments += 1

                    self._add_dag_node("fragment_success", {
                        "fragment_id": i,
                        "sent_usdc": amount_per_fragment,
                        "received_sol": output,
                        "fee": fee
                    })
                except Exception:
                    self.state.failed_fragments += 1
                    self._add_dag_node("fragment_fail", {
                        "fragment_id": i,
                        "reason": "swap_exception"
                    })
            else:
                self.state.failed_fragments += 1
                self._add_dag_node("fragment_fail", {
                    "fragment_id": i,
                    "reason": "timeout"
                })

        # Recovery
        num_lost = num_fragments - len(confirmed_fragments)
        if num_lost > 0 and len(confirmed_fragments) > 0:
            self.state.recovery_attempts += 1
            self._add_dag_node("recovery_attempt", {
                "confirmed": len(confirmed_fragments),
                "lost": num_lost,
                "threshold": num_fragments * 0.5
            })

            if num_lost <= num_fragments * 0.5:
                mean_confirmed = sum(confirmed_fragments.values()) / len(confirmed_fragments)
                for i in range(num_fragments):
                    if i not in confirmed_fragments:
                        recovered = mean_confirmed * (PHI ** (random.random() - 0.5))
                        total_output_sol += recovered
                        self.state.recovery_successes += 1

                self._add_dag_node("recovery_success", {
                    "recovered_fragments": num_lost,
                    "method": "phi_scale"
                })

        # Convert SOL back to USDC
        current_price = self.pools[0].get_price(False)
        output_usdc = total_output_sol * current_price

        profit = output_usdc - amount_usdc

        if profit > 0:
            self.state.lifetime_profit += profit
        else:
            self.state.lifetime_loss += abs(profit)

        self.state.balance_usdc += profit
        self.state.balance_sol -= amount_usdc / self.pools[0].get_price(True)

        if self.state.balance_usdc < self.state.lowest_balance:
            self.state.lowest_balance = self.state.balance_usdc
            if self.state.went_negative_at is None and self.state.balance_usdc < 0:
                self.state.went_negative_at = self.state.time_alive_seconds
                self._add_dag_node("went_negative", {
                    "balance": self.state.balance_usdc,
                    "timestamp": self.state.time_alive_seconds
                })

        self.state.trade_history.append({
            "timestamp": self.state.time_alive_seconds,
            "amount": amount_usdc,
            "fragments": num_fragments,
            "output_usdc": output_usdc,
            "profit": profit,
            "balance_after": self.state.balance_usdc,
            "predicted_direction": predicted_dir,
            "confidence": confidence
        })

        self.state.num_trades += 1
        return profit

    def save_checkpoint(self):
        """Save state to file"""
        with open(self.checkpoint_file, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)

    def save_dag(self):
        """Save DAG to file for analysis"""
        dag_data = {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "num_nodes": len(self.state.dag_nodes),
            "dag_heads": self.state.dag_heads,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "timestamp": n.timestamp,
                    "event_type": n.event_type,
                    "parent_hash": n.parent_hash,
                    "hash": n.hash,
                    "data": n.data
                }
                for n in self.state.dag_nodes[-100:]  # Keep last 100 nodes
            ]
        }
        with open(self.dag_file, "w") as f:
            json.dump(dag_data, f, indent=2)

    def run_for_duration(self, duration_seconds: int = 28800):  # 8 hours = 28800 seconds
        """Run trading agent for specified duration"""
        self.log(f"Starting paper trader agent {self.agent_id} with {self.state.balance_usdc:.2f} USDC")
        self._add_dag_node("agent_start", {
            "starting_balance_usdc": self.state.balance_usdc,
            "starting_balance_sol": self.state.balance_sol,
            "duration_seconds": duration_seconds
        })

        start_time = time.time()
        last_checkpoint = start_time
        last_dag_save = start_time

        while True:
            elapsed = time.time() - start_time
            self.state.time_alive_seconds = int(elapsed * SIMULATION_SPEED)

            # Record price
            current_price = self.pools[0].get_price(True)
            self.price_history["SOL/USDC"].append(current_price)

            # Stop if out of USDC
            if self.state.balance_usdc < 0.1:
                self.log(f"❌ STOPPED: Balance too low ({self.state.balance_usdc:.2f})")
                self._add_dag_node("agent_stop", {
                    "reason": "balance_depleted",
                    "final_balance": self.state.balance_usdc
                })
                break

            # Stop if duration exceeded
            if self.state.time_alive_seconds >= duration_seconds:
                self.log(f"✅ SURVIVED: Completed {duration_seconds}s with {self.state.balance_usdc:.2f} USDC")
                self._add_dag_node("agent_complete", {
                    "reason": "duration_exceeded",
                    "final_balance": self.state.balance_usdc,
                    "total_trades": self.state.num_trades
                })
                break

            # Execute trade (probability based on prediction confidence)
            pred_dir, confidence = self.predict_price_direction()
            should_trade = (confidence > 0.4) or (random.random() < 0.3)

            if should_trade:
                risk_amount = max(0.1, self.state.balance_usdc * random.uniform(0.01, 0.05))
                self.execute_trade(risk_amount, num_fragments=random.randint(1, 3))

            # Checkpoint every 10 minutes (real time)
            if time.time() - last_checkpoint > 600:
                self.save_checkpoint()
                last_checkpoint = time.time()
                self.log(f"Checkpoint: Balance={self.state.balance_usdc:.2f}, Trades={self.state.num_trades}")

            # Save DAG every 5 minutes
            if time.time() - last_dag_save > 300:
                self.save_dag()
                last_dag_save = time.time()

            time.sleep(0.01 / SIMULATION_SPEED)

        # Final checkpoint and DAG
        self.save_checkpoint()
        self.save_dag()
        self.log(f"Agent {self.agent_id} FINAL STATE: "
                f"USDC={self.state.balance_usdc:.2f}, "
                f"Profit={self.state.lifetime_profit:.2f}, "
                f"Trades={self.state.num_trades}, "
                f"Recovery Rate={self.state.recovery_successes}/{self.state.recovery_attempts}")

        return self.state


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python paper_trader_agent.py <agent_id> <session_id> [duration_seconds]")
        sys.exit(1)

    agent_id = int(sys.argv[1])
    session_id = sys.argv[2]
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 28800

    trader = PaperTrader(agent_id, session_id, starting_usdc=50.0)
    final_state = trader.run_for_duration(duration)

    print(json.dumps(final_state.to_dict(), indent=2))
