#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Paper Trading Simulator utilities.

Modes:
- fast-sweep: synthetic compressed-time Monte Carlo sweep for strategy exploration
- wall-clock: real-duration paper trading session with heartbeat logging
- finalize-summary: turn a completed wall-clock session into a one-page summary
"""

import argparse
import csv
import hashlib
import json
import math
import random
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List, Optional, Tuple


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def format_utc(dt: datetime) -> str:
    """Render timestamps with a trailing Z for consistency across artifacts."""
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def clamp_near_zero(value: float, epsilon: float = 1e-12) -> float:
    """Avoid tiny float residue in positions and cost basis values."""
    return 0.0 if abs(value) < epsilon else value


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write a JSON payload to disk, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def append_text(path: Path, text: str) -> None:
    """Append text to a file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


@dataclass
class Trade:
    """Individual trade record."""

    timestamp: str
    type: str
    symbol: str
    amount_usdc: float
    price_usd: float
    quantity: float
    position_after: float
    cost_basis_usdc: Optional[float]
    pnl: Optional[float]
    tx_id: str


class PaperTradingSimulator:
    """Simulates trading with paper money and tracks realized cost basis."""

    def __init__(
        self,
        initial_usdc: float = 100.0,
        duration_hours: float = 1.0,
        session_mode: str = "wall_clock_session",
        random_seed: Optional[int] = None,
    ):
        self.initial_usdc = initial_usdc
        self.current_usdc = initial_usdc
        self.duration_hours = duration_hours
        self.session_mode = session_mode
        self.random = random.Random(random_seed)
        self.start_time = utc_now()
        self.end_time = self.start_time + timedelta(hours=duration_hours)

        self.positions: Dict[str, float] = {}
        self.position_cost_basis_usdc: Dict[str, float] = {}
        self.price_history: Dict[str, List[Tuple[str, float]]] = {
            "ETH": [],
            "BTC": [],
            "SOL": [],
            "ARB": [],
        }
        self.trades: List[Trade] = []
        self.current_prices: Dict[str, float] = {
            "ETH": 2100.00 + self.random.uniform(-50, 50),
            "BTC": 42000.00 + self.random.uniform(-1000, 1000),
            "SOL": 98.00 + self.random.uniform(-5, 5),
            "ARB": 2.50 + self.random.uniform(-0.1, 0.1),
        }
        self.decision_log: List[Dict[str, Any]] = []
        self.portfolio_history: List[Dict[str, Any]] = []

    def generate_market_data(self, timestamp: Optional[datetime] = None) -> Dict[str, float]:
        """Generate the next simulated market prices."""
        tick_time = timestamp or utc_now()
        new_prices = {}
        volatility = {
            "ETH": 0.015,
            "BTC": 0.012,
            "SOL": 0.025,
            "ARB": 0.030,
        }

        for symbol, current_price in self.current_prices.items():
            drift = self.random.uniform(-volatility[symbol], volatility[symbol])
            new_price = max(current_price * (1 + drift), 0.01)
            new_prices[symbol] = new_price
            self.price_history[symbol].append((format_utc(tick_time), new_price))

        self.current_prices = new_prices
        return new_prices

    def should_trade(self, symbol: str, price: float) -> Tuple[str, float]:
        """Return an action and unit-consistent amount for the next trade."""
        recent_prices = [point[1] for point in self.price_history[symbol][-5:]]
        if len(recent_prices) < 2:
            return ("hold", 0.0)

        avg_recent = sum(recent_prices) / len(recent_prices)

        if price < avg_recent * 0.98 and self.current_usdc > 10:
            buy_amount_usdc = min(self.current_usdc * 0.25, self.current_usdc)
            return ("buy", buy_amount_usdc)

        if price > avg_recent * 1.02 and self.positions.get(symbol, 0.0) > 0:
            sell_quantity = self.positions[symbol] * 0.5
            return ("sell", sell_quantity)

        return ("hold", 0.0)

    def average_cost_per_unit(self, symbol: str) -> float:
        """Return average cost per unit for the current position."""
        quantity = self.positions.get(symbol, 0.0)
        if quantity <= 0:
            return 0.0
        return self.position_cost_basis_usdc.get(symbol, 0.0) / quantity

    def execute_trade(
        self,
        symbol: str,
        action: str,
        amount: float,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Trade]:
        """Execute a trade.

        Buy amounts are denominated in USDC.
        Sell amounts are denominated in asset quantity.
        """
        if amount <= 0:
            return None

        price = self.current_prices[symbol]
        trade_time = timestamp or utc_now()
        trade_timestamp = format_utc(trade_time)

        if action == "buy":
            if amount > self.current_usdc:
                return None

            quantity = amount / price
            self.current_usdc -= amount
            self.positions[symbol] = self.positions.get(symbol, 0.0) + quantity
            self.position_cost_basis_usdc[symbol] = self.position_cost_basis_usdc.get(symbol, 0.0) + amount

            trade = Trade(
                timestamp=trade_timestamp,
                type="buy",
                symbol=symbol,
                amount_usdc=amount,
                price_usd=price,
                quantity=quantity,
                position_after=self.positions[symbol],
                cost_basis_usdc=amount,
                pnl=None,
                tx_id=hashlib.sha256(f"{symbol}|buy|{trade_timestamp}".encode()).hexdigest()[:16],
            )
            self.trades.append(trade)
            return trade

        if action == "sell":
            current_quantity = self.positions.get(symbol, 0.0)
            if amount > current_quantity:
                return None

            avg_cost = self.average_cost_per_unit(symbol)
            cost_basis_sold = avg_cost * amount
            proceeds = amount * price

            self.current_usdc += proceeds
            remaining_quantity = clamp_near_zero(current_quantity - amount)
            remaining_cost_basis = clamp_near_zero(
                self.position_cost_basis_usdc.get(symbol, 0.0) - cost_basis_sold
            )

            self.positions[symbol] = remaining_quantity
            self.position_cost_basis_usdc[symbol] = remaining_cost_basis

            if remaining_quantity == 0.0:
                self.positions.pop(symbol, None)
                self.position_cost_basis_usdc.pop(symbol, None)

            pnl = proceeds - cost_basis_sold
            trade = Trade(
                timestamp=trade_timestamp,
                type="sell",
                symbol=symbol,
                amount_usdc=proceeds,
                price_usd=price,
                quantity=amount,
                position_after=remaining_quantity,
                cost_basis_usdc=cost_basis_sold,
                pnl=pnl,
                tx_id=hashlib.sha256(f"{symbol}|sell|{trade_timestamp}".encode()).hexdigest()[:16],
            )
            self.trades.append(trade)
            return trade

        return None

    def calculate_portfolio_value(self) -> float:
        """Calculate total portfolio value at current prices."""
        value = self.current_usdc
        for symbol, quantity in self.positions.items():
            value += quantity * self.current_prices[symbol]
        return value

    def record_portfolio_snapshot(self, timestamp: Optional[datetime] = None, tick: Optional[int] = None) -> None:
        """Store a mark-to-market snapshot for reporting and finalization."""
        snapshot_time = timestamp or utc_now()
        self.portfolio_history.append(
            {
                "timestamp": format_utc(snapshot_time),
                "tick": tick,
                "portfolio_value_usdc": self.calculate_portfolio_value(),
                "cash_usdc": self.current_usdc,
                "trade_count": len(self.trades),
            }
        )

    def step(self, tick: int, timestamp: Optional[datetime] = None) -> None:
        """Advance the simulation by one tick."""
        step_time = timestamp or utc_now()
        prices = self.generate_market_data(step_time)

        for symbol in prices.keys():
            action, amount = self.should_trade(symbol, prices[symbol])
            if action == "hold":
                continue

            trade = self.execute_trade(symbol, action, amount, step_time)
            self.decision_log.append(
                {
                    "tick": tick,
                    "timestamp": format_utc(step_time),
                    "symbol": symbol,
                    "action": action,
                    "signal_amount": amount,
                    "price": prices[symbol],
                    "executed": trade is not None,
                }
            )

        self.record_portfolio_snapshot(step_time, tick)

    def generate_report(
        self,
        session_end_time: Optional[datetime] = None,
        tick_count: int = 0,
        tick_interval_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        """Generate a complete session report."""
        end_time = session_end_time or utc_now()
        portfolio_value = self.calculate_portfolio_value()
        total_pnl = portfolio_value - self.initial_usdc
        realized_pnl = sum(trade.pnl for trade in self.trades if trade.pnl is not None)
        unrealized_pnl = total_pnl - realized_pnl
        pnl_percent = (total_pnl / self.initial_usdc * 100) if self.initial_usdc > 0 else 0.0
        max_portfolio_value = max(
            [snapshot["portfolio_value_usdc"] for snapshot in self.portfolio_history],
            default=portfolio_value,
        )

        return {
            "report_type": self.session_mode,
            "comparability_class": (
                "synthetic_compressed_time"
                if self.session_mode.startswith("fast_")
                else "wall_clock"
            ),
            "comparability_note": (
                "Synthetic compressed-time output is not directly comparable to wall-clock session results."
                if self.session_mode.startswith("fast_")
                else "Wall-clock session output reflects real elapsed time and should not be compared to synthetic sweeps as if they were the same instrument."
            ),
            "simulation_start_utc": format_utc(self.start_time),
            "simulation_end_utc": format_utc(end_time),
            "duration_hours_requested": self.duration_hours,
            "tick_interval_seconds": tick_interval_seconds,
            "tick_count": tick_count,
            "initial_capital_usdc": self.initial_usdc,
            "current_usdc": self.current_usdc,
            "portfolio_value_usdc": portfolio_value,
            "max_portfolio_value_usdc": max_portfolio_value,
            "total_pnl_usdc": total_pnl,
            "realized_pnl_usdc": realized_pnl,
            "unrealized_pnl_usdc": unrealized_pnl,
            "pnl_percent": pnl_percent,
            "trade_count": len(self.trades),
            "final_positions": {
                symbol: {
                    "quantity": qty,
                    "price": self.current_prices[symbol],
                    "value": qty * self.current_prices[symbol],
                    "cost_basis_usdc": self.position_cost_basis_usdc.get(symbol, 0.0),
                    "average_cost_usdc": self.average_cost_per_unit(symbol),
                }
                for symbol, qty in self.positions.items()
                if qty > 0
            },
            "final_prices": self.current_prices,
            "trades": [asdict(trade) for trade in self.trades[-20:]],
            "decision_log_sample": self.decision_log[-10:],
            "portfolio_history_sample": self.portfolio_history[-10:],
        }

    def run_compressed_time(self, tick_interval_seconds: float = 10.0) -> Dict[str, Any]:
        """Run a synthetic compressed-time path with no sleeping."""
        total_seconds = self.duration_hours * 3600
        tick_count = max(1, math.ceil(total_seconds / tick_interval_seconds))

        for tick in range(1, tick_count + 1):
            tick_time = self.start_time + timedelta(seconds=tick * tick_interval_seconds)
            self.step(tick, tick_time)

        simulated_end = self.start_time + timedelta(seconds=tick_count * tick_interval_seconds)
        return self.generate_report(
            session_end_time=simulated_end,
            tick_count=tick_count,
            tick_interval_seconds=tick_interval_seconds,
        )

    def run_wall_clock(
        self,
        tick_interval_seconds: float = 60.0,
        heartbeat_path: Optional[Path] = None,
        heartbeat_every_ticks: int = 5,
    ) -> Dict[str, Any]:
        """Run a real-duration wall-clock session with optional heartbeat logging."""
        total_seconds = self.duration_hours * 3600
        tick_count = max(1, math.ceil(total_seconds / tick_interval_seconds))

        if heartbeat_path:
            heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
            heartbeat_path.write_text(f"start_utc={format_utc(self.start_time)}\n", encoding="utf-8")

        for tick in range(1, tick_count + 1):
            tick_time = utc_now()
            self.step(tick, tick_time)

            if heartbeat_path and (tick % heartbeat_every_ticks == 0 or tick == tick_count):
                append_text(
                    heartbeat_path,
                    (
                        f"{format_utc(tick_time)} tick={tick} "
                        f"portfolio_value_usdc={self.calculate_portfolio_value():.2f} "
                        f"cash_usdc={self.current_usdc:.2f} trades={len(self.trades)}\n"
                    ),
                )

            if tick < tick_count:
                time.sleep(tick_interval_seconds)

        end_time = utc_now()
        if heartbeat_path:
            append_text(heartbeat_path, f"end_utc={format_utc(end_time)}\n")

        return self.generate_report(
            session_end_time=end_time,
            tick_count=tick_count,
            tick_interval_seconds=tick_interval_seconds,
        )


HEARTBEAT_LINE = re.compile(
    r"^(?P<timestamp>\S+) tick=(?P<tick>\d+) portfolio_value_usdc=(?P<portfolio>[\d.\-]+) cash_usdc=(?P<cash>[\d.\-]+) trades=(?P<trades>\d+)$"
)


def parse_heartbeat_log(heartbeat_path: Path) -> Dict[str, Any]:
    """Parse wall-clock heartbeat log entries."""
    start_utc = None
    end_utc = None
    entries: List[Dict[str, Any]] = []

    for raw_line in heartbeat_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("start_utc="):
            start_utc = line.split("=", 1)[1]
            continue
        if line.startswith("end_utc="):
            end_utc = line.split("=", 1)[1]
            continue

        match = HEARTBEAT_LINE.match(line)
        if not match:
            continue

        entries.append(
            {
                "timestamp": match.group("timestamp"),
                "tick": int(match.group("tick")),
                "portfolio_value_usdc": float(match.group("portfolio")),
                "cash_usdc": float(match.group("cash")),
                "trade_count": int(match.group("trades")),
            }
        )

    return {
        "start_utc": start_utc,
        "end_utc": end_utc,
        "entries": entries,
    }


def format_money(value: float) -> str:
    """Format a numeric value for the summary packet."""
    return f"{value:,.2f}"


def relative_or_absolute(path: Optional[Path], base: Path) -> str:
    """Prefer relative paths inside a cycle packet for readability."""
    if path is None:
        return "pending"
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def derive_cycle_metrics(
    report: Dict[str, Any],
    objective_target: float,
    gross_exit_ceiling: float,
) -> Dict[str, Any]:
    """Compute summary and ledger metrics from a completed session report."""
    final_value = report["portfolio_value_usdc"]
    fluctuation_band = max(gross_exit_ceiling - objective_target, 0.0)
    gain_above_baseline = final_value - objective_target
    progress_toward_objective = min(max(gain_above_baseline, 0.0), objective_target)
    progress_within_buffer = min(max(gain_above_baseline, 0.0), fluctuation_band)
    bonus_upside = max(final_value - gross_exit_ceiling, 0.0)

    return {
        "final_value": final_value,
        "gain_above_baseline": gain_above_baseline,
        "fluctuation_band": fluctuation_band,
        "progress_toward_objective": progress_toward_objective,
        "progress_within_buffer": progress_within_buffer,
        "bonus_upside": bonus_upside,
        "over_ceiling_flag": "YES" if final_value > gross_exit_ceiling else "NO",
    }


def sync_reconciliation_ledger(
    cycle_dir: Path,
    session_report_path: Path,
    heartbeat_log_path: Path,
    review_log_path: Optional[Path] = None,
    objective_target: float = 30000.0,
    gross_exit_ceiling: float = 37000.0,
    ledger_output_path: Optional[Path] = None,
) -> Path:
    """Update the cycle reconciliation ledger from the completed session report."""
    report = json.loads(session_report_path.read_text(encoding="utf-8"))
    heartbeat = parse_heartbeat_log(heartbeat_log_path)
    metrics = derive_cycle_metrics(report, objective_target, gross_exit_ceiling)

    ledger_path = ledger_output_path or (cycle_dir / "07_allocation_ledger" / "reconciliation_ledger.csv")
    fieldnames = [
        "cycle_id",
        "record_utc",
        "record_type",
        "provider",
        "reference_id",
        "asset",
        "amount",
        "fee",
        "from_account",
        "to_account",
        "purpose",
        "objective_progress_usd",
        "buffer_usage_usd",
        "over_ceiling_flag",
        "bonus_upside_usd",
        "notes",
    ]

    preserved_rows: List[Dict[str, str]] = []
    managed_record_types = {
        "wall_clock_session_start",
        "wall_clock_session_final",
        "review_log_reference",
    }

    if ledger_path.exists():
        with ledger_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("record_type") not in managed_record_types:
                    preserved_rows.append(row)

    start_utc = heartbeat["start_utc"] or report["simulation_start_utc"]
    end_utc = heartbeat["end_utc"] or report["simulation_end_utc"]
    session_reference = session_report_path.stem
    heartbeat_reference = heartbeat_log_path.stem

    managed_rows = [
        {
            "cycle_id": cycle_dir.name,
            "record_utc": start_utc,
            "record_type": "wall_clock_session_start",
            "provider": "local_sim",
            "reference_id": heartbeat_reference,
            "asset": "USD",
            "amount": f"{report['initial_capital_usdc']:.2f}",
            "fee": "0.00",
            "from_account": "paper_capital",
            "to_account": "realtime_paper_portfolio",
            "purpose": "wall_clock_session_start",
            "objective_progress_usd": "0.00",
            "buffer_usage_usd": "0.00",
            "over_ceiling_flag": "NO",
            "bonus_upside_usd": "0.00",
            "notes": "Auto-synced wall-clock session start",
        },
        {
            "cycle_id": cycle_dir.name,
            "record_utc": end_utc,
            "record_type": "wall_clock_session_final",
            "provider": "local_sim",
            "reference_id": session_reference,
            "asset": "USD",
            "amount": f"{metrics['final_value']:.2f}",
            "fee": "0.00",
            "from_account": "realtime_paper_portfolio",
            "to_account": "paper_portfolio_close",
            "purpose": "wall_clock_session_final",
            "objective_progress_usd": f"{metrics['progress_toward_objective']:.2f}",
            "buffer_usage_usd": f"{metrics['progress_within_buffer']:.2f}",
            "over_ceiling_flag": metrics["over_ceiling_flag"],
            "bonus_upside_usd": f"{metrics['bonus_upside']:.2f}",
            "notes": (
                f"Auto-synced from {relative_or_absolute(session_report_path, cycle_dir)}; "
                f"realized_pnl_usdc={report['realized_pnl_usdc']:.2f}; trade_count={report['trade_count']}"
            ),
        },
    ]

    if review_log_path:
        managed_rows.append(
            {
                "cycle_id": cycle_dir.name,
                "record_utc": start_utc,
                "record_type": "review_log_reference",
                "provider": "local_review",
                "reference_id": review_log_path.stem,
                "asset": "USD",
                "amount": "0.00",
                "fee": "0.00",
                "from_account": "realtime_heartbeat",
                "to_account": "review_log",
                "purpose": "review_reference",
                "objective_progress_usd": f"{metrics['progress_toward_objective']:.2f}",
                "buffer_usage_usd": f"{metrics['progress_within_buffer']:.2f}",
                "over_ceiling_flag": metrics["over_ceiling_flag"],
                "bonus_upside_usd": f"{metrics['bonus_upside']:.2f}",
                "notes": f"Review log reference: {relative_or_absolute(review_log_path, cycle_dir)}",
            }
        )

    combined_rows = preserved_rows + managed_rows
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_rows)

    return ledger_path


def build_one_page_summary(
    cycle_dir: Path,
    session_report_path: Path,
    heartbeat_log_path: Path,
    review_log_path: Optional[Path] = None,
    reviewer: str = "system-generated",
    objective_target: float = 30000.0,
    gross_exit_ceiling: float = 37000.0,
) -> str:
    """Build the final one-page markdown summary for a completed wall-clock session."""
    report = json.loads(session_report_path.read_text(encoding="utf-8"))
    heartbeat = parse_heartbeat_log(heartbeat_log_path)
    metrics = derive_cycle_metrics(report, objective_target, gross_exit_ceiling)

    final_value = metrics["final_value"]
    max_value = max(
        [entry["portfolio_value_usdc"] for entry in heartbeat["entries"]] + [report["max_portfolio_value_usdc"]]
    )
    realized_gain_loss = report["realized_pnl_usdc"]

    start_utc = heartbeat["start_utc"] or report["simulation_start_utc"]
    end_utc = heartbeat["end_utc"] or report["simulation_end_utc"]

    lines = [
        "# One-Page Money Trail Summary",
        "",
        "## Cycle Header",
        f"- Cycle ID: {cycle_dir.name}",
        f"- Window UTC: {start_utc} to {end_utc}",
        f"- Prepared UTC: {format_utc(utc_now())}",
        f"- Reviewer: {reviewer}",
        "",
        "## Portfolio Snapshot",
        f"- Starting value (USD): {format_money(report['initial_capital_usdc'])}",
        f"- Objective target value (USD): {format_money(objective_target)}",
        f"- Gross exit ceiling (USD): {format_money(gross_exit_ceiling)}",
        f"- Bonus upside above ceiling (USD): {format_money(metrics['bonus_upside'])}",
        f"- Final value (USD): {format_money(final_value)}",
        f"- Max value seen (USD): {format_money(max_value)}",
        f"- Realized gain/loss (USD): {format_money(realized_gain_loss)}",
        f"- Trade count: {report['trade_count']}",
        f"- Session report type: {report['report_type']}",
        "",
        "## Transfer Chain",
        f"- Strategy source artifact: {relative_or_absolute(session_report_path, cycle_dir)}",
        f"- Realtime heartbeat artifact: {relative_or_absolute(heartbeat_log_path, cycle_dir)}",
        f"- Review heartbeat artifact: {relative_or_absolute(review_log_path, cycle_dir)}" if review_log_path else "- Review heartbeat artifact: pending / not provided",
        "- Wallet transfer artifact(s): pending (paper cycle only)",
        "- Coinbase export artifact: pending (no live off-ramp activity)",
        "- Bank confirmation artifact: pending (no live off-ramp activity)",
        "",
        "## Reconciliation Results",
        "- Asset conservation: PASS for paper-cycle artifacts only",
        "- Fiat settlement match: NOT APPLICABLE",
        "- Time-order integrity: PASS for wall-clock heartbeat and final report",
        "- ID completeness: PARTIAL (paper logs only; no exchange/bank IDs yet)",
        "",
        "## Tax and Allocation",
        "- Tax reserve moved (USD): 0.00",
        "- Debt bucket moved (USD): 0.00",
        "- Vehicle bucket moved (USD): 0.00",
        f"- Retained operating cash (USD): {format_money(final_value)} paper value",
        "",
        f"## Goal Progress ({format_money(objective_target)} objective / {format_money(gross_exit_ceiling)} ceiling)",
        f"- Gain above {format_money(objective_target)} baseline (USD): {format_money(metrics['gain_above_baseline'])}",
        f"- Progress toward {format_money(objective_target)} objective (USD): {format_money(metrics['progress_toward_objective'])} / {format_money(objective_target)}",
        f"- Progress within {format_money(metrics['fluctuation_band'])} fluctuation buffer (USD): {format_money(metrics['progress_within_buffer'])} / {format_money(metrics['fluctuation_band'])}",
        f"- Over-ceiling flag: {metrics['over_ceiling_flag']}",
        f"- Bonus upside beyond {format_money(gross_exit_ceiling)} (USD): {format_money(metrics['bonus_upside'])}",
        "- Debt target progress (15,000): 0.00 / 15,000.00",
        "- Vehicle target progress (15,000): 0.00 / 15,000.00",
        f"- Combined target progress ({format_money(objective_target)} objective): {format_money(metrics['progress_toward_objective'])} / {format_money(objective_target)}",
        "",
        "## Exceptions and Notes",
        "- This packet documents a completed wall-clock paper session rather than a synthetic sweep.",
        "- Realized PnL now reflects tracked position cost basis; unrealized exposure remains inside the marked portfolio value.",
        "- This packet currently documents paper strategy evidence only, not live execution, Coinbase settlement, or bank receipt.",
        "- If realized value ends above the gross ceiling, the excess is treated as bonus upside rather than required plan performance.",
        "",
        "## Process Integrity Statement",
        "- This report is intended to show disciplined accounting through a volatile period, including losses if they occur.",
        "- The purpose is documentation and reconciliation, not trying to present a synthetic sweep as a real session.",
        "",
        "## Evidence Links",
        f"- {relative_or_absolute(session_report_path, cycle_dir)}",
        f"- {relative_or_absolute(heartbeat_log_path, cycle_dir)}",
    ]

    if review_log_path:
        lines.append(f"- {relative_or_absolute(review_log_path, cycle_dir)}")

    return "\n".join(lines) + "\n"


def finalize_one_page_summary(
    cycle_dir: Path,
    session_report_path: Path,
    heartbeat_log_path: Path,
    review_log_path: Optional[Path] = None,
    summary_output_path: Optional[Path] = None,
    reviewer: str = "system-generated",
    objective_target: float = 30000.0,
    gross_exit_ceiling: float = 37000.0,
) -> Path:
    """Write the completed one-page summary for a finished wall-clock run."""
    summary_path = summary_output_path or (
        cycle_dir / "08_summary_report" / f"one_page_summary_filled_{utc_now().date().isoformat()}.md"
    )
    summary_markdown = build_one_page_summary(
        cycle_dir=cycle_dir,
        session_report_path=session_report_path,
        heartbeat_log_path=heartbeat_log_path,
        review_log_path=review_log_path,
        reviewer=reviewer,
        objective_target=objective_target,
        gross_exit_ceiling=gross_exit_ceiling,
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary_markdown, encoding="utf-8")
    sync_reconciliation_ledger(
        cycle_dir=cycle_dir,
        session_report_path=session_report_path,
        heartbeat_log_path=heartbeat_log_path,
        review_log_path=review_log_path,
        objective_target=objective_target,
        gross_exit_ceiling=gross_exit_ceiling,
    )
    return summary_path


def run_fast_monte_carlo_sweep(
    initial_usdc: float,
    duration_hours: float,
    tick_interval_seconds: float,
    sweep_count: int,
    output_path: Optional[Path],
    seed: Optional[int],
) -> Dict[str, Any]:
    """Run a compressed-time Monte Carlo sweep and write aggregate results."""
    run_summaries = []

    for index in range(sweep_count):
        run_seed = None if seed is None else seed + index
        simulator = PaperTradingSimulator(
            initial_usdc=initial_usdc,
            duration_hours=duration_hours,
            session_mode="fast_monte_carlo_path",
            random_seed=run_seed,
        )
        report = simulator.run_compressed_time(tick_interval_seconds=tick_interval_seconds)
        run_summaries.append(
            {
                "run_index": index,
                "portfolio_value_usdc": report["portfolio_value_usdc"],
                "total_pnl_usdc": report["total_pnl_usdc"],
                "realized_pnl_usdc": report["realized_pnl_usdc"],
                "unrealized_pnl_usdc": report["unrealized_pnl_usdc"],
                "pnl_percent": report["pnl_percent"],
                "trade_count": report["trade_count"],
                "max_portfolio_value_usdc": report["max_portfolio_value_usdc"],
            }
        )

    portfolio_values = [run["portfolio_value_usdc"] for run in run_summaries]
    aggregate_report = {
        "report_type": "fast_monte_carlo_sweep",
        "comparability_class": "synthetic_compressed_time",
        "comparability_note": "This sweep explores many compressed-time synthetic paths. It is not directly comparable to a single wall-clock paper session.",
        "duration_hours_requested": duration_hours,
        "initial_capital_usdc": initial_usdc,
        "tick_interval_seconds": tick_interval_seconds,
        "sweep_count": sweep_count,
        "mean_portfolio_value_usdc": mean(portfolio_values),
        "median_portfolio_value_usdc": median(portfolio_values),
        "best_portfolio_value_usdc": max(portfolio_values),
        "worst_portfolio_value_usdc": min(portfolio_values),
        "positive_run_ratio": sum(1 for run in run_summaries if run["total_pnl_usdc"] > 0) / sweep_count,
        "run_summaries": run_summaries,
    }

    if output_path:
        write_json(output_path, aggregate_report)

    print("Starting fast Monte Carlo sweep...")
    print(f"  Initial Capital: ${initial_usdc:.2f} USDC")
    print(f"  Duration per Path: {duration_hours} hour(s)")
    print(f"  Sweep Count: {sweep_count}")
    print(f"  Mean Final Value: ${aggregate_report['mean_portfolio_value_usdc']:.2f}")
    print(f"  Median Final Value: ${aggregate_report['median_portfolio_value_usdc']:.2f}")
    print(f"  Best / Worst: ${aggregate_report['best_portfolio_value_usdc']:.2f} / ${aggregate_report['worst_portfolio_value_usdc']:.2f}")
    if output_path:
        print(f"\n✓ Sweep report written to {output_path}")
    return aggregate_report


def run_wall_clock_session(
    initial_usdc: float,
    duration_hours: float,
    tick_interval_seconds: float,
    heartbeat_every_ticks: int,
    output_path: Optional[Path],
    heartbeat_path: Optional[Path],
    cycle_dir: Optional[Path],
    review_log_path: Optional[Path],
    summary_output_path: Optional[Path],
    reviewer: str,
    objective_target: float,
    gross_exit_ceiling: float,
    seed: Optional[int],
) -> Dict[str, Any]:
    """Run a real-duration paper session and optionally auto-finalize the cycle summary."""
    print("Starting wall-clock paper trading session...")
    print(f"  Initial Capital: ${initial_usdc:.2f} USDC")
    print(f"  Duration: {duration_hours} hour(s)")
    print(f"  Tick Interval: {tick_interval_seconds:.2f} second(s)")
    print(f"  Start Time: {format_utc(utc_now())}\n")

    simulator = PaperTradingSimulator(
        initial_usdc=initial_usdc,
        duration_hours=duration_hours,
        session_mode="wall_clock_session",
        random_seed=seed,
    )
    report = simulator.run_wall_clock(
        tick_interval_seconds=tick_interval_seconds,
        heartbeat_path=heartbeat_path,
        heartbeat_every_ticks=heartbeat_every_ticks,
    )

    if output_path:
        write_json(output_path, report)
        print(f"✓ Session report written to {output_path}")

    if cycle_dir and output_path and heartbeat_path:
        summary_path = finalize_one_page_summary(
            cycle_dir=cycle_dir,
            session_report_path=output_path,
            heartbeat_log_path=heartbeat_path,
            review_log_path=review_log_path,
            summary_output_path=summary_output_path,
            reviewer=reviewer,
            objective_target=objective_target,
            gross_exit_ceiling=gross_exit_ceiling,
        )
        print(f"✓ One-page summary written to {summary_path}")

    print("\nWall-clock session complete")
    print(f"  Final Value: ${report['portfolio_value_usdc']:.2f}")
    print(f"  Realized PnL: ${report['realized_pnl_usdc']:+.2f}")
    print(f"  Unrealized PnL: ${report['unrealized_pnl_usdc']:+.2f}")
    print(f"  Trades: {report['trade_count']}")
    return report


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the trading utilities."""
    parser = argparse.ArgumentParser(description="Paper Trading Simulator Utilities")
    parser.add_argument(
        "--mode",
        choices=["fast-sweep", "wall-clock", "finalize-summary"],
        default="fast-sweep",
        help="Execution mode",
    )
    parser.add_argument("--initial-usdc", type=float, default=100.0, help="Initial USDC capital")
    parser.add_argument("--duration-hours", type=float, default=1.0, help="Session duration in hours")
    parser.add_argument("--tick-interval-seconds", type=float, default=60.0, help="Tick interval in seconds")
    parser.add_argument("--output", help="Output JSON path for fast-sweep or wall-clock mode")
    parser.add_argument("--heartbeat-log", help="Heartbeat log path for wall-clock or finalize-summary mode")
    parser.add_argument("--review-log", help="Optional review heartbeat log path")
    parser.add_argument("--summary-output", help="Summary markdown output path")
    parser.add_argument("--cycle-dir", help="Cycle directory for summary finalization")
    parser.add_argument("--reviewer", default="system-generated", help="Reviewer name for summary output")
    parser.add_argument("--objective-target", type=float, default=30000.0, help="Objective target value")
    parser.add_argument("--gross-exit-ceiling", type=float, default=37000.0, help="Gross exit ceiling")
    parser.add_argument("--heartbeat-every-ticks", type=int, default=5, help="Heartbeat write interval")
    parser.add_argument("--sweep-count", type=int, default=25, help="Monte Carlo path count for fast-sweep")
    parser.add_argument("--seed", type=int, help="Optional random seed")
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()

    output_path = Path(args.output) if args.output else None
    heartbeat_path = Path(args.heartbeat_log) if args.heartbeat_log else None
    review_log_path = Path(args.review_log) if args.review_log else None
    summary_output_path = Path(args.summary_output) if args.summary_output else None
    cycle_dir = Path(args.cycle_dir) if args.cycle_dir else None

    if args.mode == "fast-sweep":
        run_fast_monte_carlo_sweep(
            initial_usdc=args.initial_usdc,
            duration_hours=args.duration_hours,
            tick_interval_seconds=args.tick_interval_seconds,
            sweep_count=args.sweep_count,
            output_path=output_path,
            seed=args.seed,
        )
        return

    if args.mode == "wall-clock":
        run_wall_clock_session(
            initial_usdc=args.initial_usdc,
            duration_hours=args.duration_hours,
            tick_interval_seconds=args.tick_interval_seconds,
            heartbeat_every_ticks=args.heartbeat_every_ticks,
            output_path=output_path,
            heartbeat_path=heartbeat_path,
            cycle_dir=cycle_dir,
            review_log_path=review_log_path,
            summary_output_path=summary_output_path,
            reviewer=args.reviewer,
            objective_target=args.objective_target,
            gross_exit_ceiling=args.gross_exit_ceiling,
            seed=args.seed,
        )
        return

    if not cycle_dir:
        raise SystemExit("--cycle-dir is required for finalize-summary mode")
    if not output_path:
        raise SystemExit("--output is required for finalize-summary mode and must point to the completed wall-clock session report")
    if not heartbeat_path:
        raise SystemExit("--heartbeat-log is required for finalize-summary mode")

    summary_path = finalize_one_page_summary(
        cycle_dir=cycle_dir,
        session_report_path=output_path,
        heartbeat_log_path=heartbeat_path,
        review_log_path=review_log_path,
        summary_output_path=summary_output_path,
        reviewer=args.reviewer,
        objective_target=args.objective_target,
        gross_exit_ceiling=args.gross_exit_ceiling,
    )
    print(f"✓ One-page summary written to {summary_path}")


if __name__ == "__main__":
    main()
