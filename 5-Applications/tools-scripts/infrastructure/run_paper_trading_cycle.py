#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Run paper-trading artifacts against a cycle directory with canonical paths."""

import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.paper_trading_simulator import (
        finalize_one_page_summary,
        run_fast_monte_carlo_sweep,
        run_wall_clock_session,
    )
except ModuleNotFoundError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from paper_trading_simulator import (
        finalize_one_page_summary,
        run_fast_monte_carlo_sweep,
        run_wall_clock_session,
    )


def summary_filename() -> str:
    """Return the default one-page summary filename for the current UTC date."""
    return f"one_page_summary_filled_{datetime.now(timezone.utc).date().isoformat()}.md"


def cycle_paths(cycle_dir: Path) -> dict[str, Path]:
    """Return canonical artifact locations inside a cycle packet."""
    return {
        "fast_sweep_output": cycle_dir / "01_strategy_outputs" / "fast_monte_carlo_sweep.json",
        "wall_clock_report": cycle_dir / "01_strategy_outputs" / "wall_clock_session_report.json",
        "wall_clock_heartbeat": cycle_dir / "01_strategy_outputs" / "wall_clock_heartbeat.log",
        "review_heartbeat": cycle_dir / "01_strategy_outputs" / "review_heartbeat.log",
        "summary_output": cycle_dir / "08_summary_report" / summary_filename(),
        "reconciliation_ledger": cycle_dir / "07_allocation_ledger" / "reconciliation_ledger.csv",
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for cycle-oriented paper trading runs."""
    parser = argparse.ArgumentParser(description="Cycle-oriented paper trading runner")
    parser.add_argument(
        "--mode",
        choices=["fast-sweep", "wall-clock", "finalize-summary", "print-paths"],
        required=True,
        help="Workflow step to run",
    )
    parser.add_argument("--cycle-dir", required=True, help="Cycle directory root")
    parser.add_argument("--initial-usdc", type=float, default=30000.0, help="Initial USDC capital")
    parser.add_argument("--duration-hours", type=float, default=4.0, help="Duration in hours")
    parser.add_argument("--tick-interval-seconds", type=float, default=60.0, help="Tick interval in seconds")
    parser.add_argument("--heartbeat-every-ticks", type=int, default=5, help="Heartbeat write interval")
    parser.add_argument("--sweep-count", type=int, default=25, help="Monte Carlo path count")
    parser.add_argument("--seed", type=int, help="Optional random seed")
    parser.add_argument("--review-log", help="Optional explicit review heartbeat path")
    parser.add_argument("--reviewer", default="system-generated", help="Reviewer label for summary output")
    parser.add_argument("--objective-target", type=float, default=30000.0, help="Objective target value")
    parser.add_argument("--gross-exit-ceiling", type=float, default=37000.0, help="Gross exit ceiling")
    return parser.parse_args()


def main() -> None:
    """Entry point for canonical cycle runs."""
    args = parse_args()
    cycle_dir = Path(args.cycle_dir)
    paths = cycle_paths(cycle_dir)
    review_log_path = Path(args.review_log) if args.review_log else paths["review_heartbeat"]

    if args.mode == "print-paths":
        for key, value in paths.items():
            print(f"{key}={value}")
        return

    if args.mode == "fast-sweep":
        run_fast_monte_carlo_sweep(
            initial_usdc=args.initial_usdc,
            duration_hours=args.duration_hours,
            tick_interval_seconds=args.tick_interval_seconds,
            sweep_count=args.sweep_count,
            output_path=paths["fast_sweep_output"],
            seed=args.seed,
        )
        return

    if args.mode == "wall-clock":
        run_wall_clock_session(
            initial_usdc=args.initial_usdc,
            duration_hours=args.duration_hours,
            tick_interval_seconds=args.tick_interval_seconds,
            heartbeat_every_ticks=args.heartbeat_every_ticks,
            output_path=paths["wall_clock_report"],
            heartbeat_path=paths["wall_clock_heartbeat"],
            cycle_dir=cycle_dir,
            review_log_path=review_log_path if review_log_path.exists() else None,
            summary_output_path=paths["summary_output"],
            reviewer=args.reviewer,
            objective_target=args.objective_target,
            gross_exit_ceiling=args.gross_exit_ceiling,
            seed=args.seed,
        )
        return

    summary_path = finalize_one_page_summary(
        cycle_dir=cycle_dir,
        session_report_path=paths["wall_clock_report"],
        heartbeat_log_path=paths["wall_clock_heartbeat"],
        review_log_path=review_log_path if review_log_path.exists() else None,
        summary_output_path=paths["summary_output"],
        reviewer=args.reviewer,
        objective_target=args.objective_target,
        gross_exit_ceiling=args.gross_exit_ceiling,
    )
    print(f"summary_output={summary_path}")


if __name__ == "__main__":
    main()