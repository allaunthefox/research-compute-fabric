# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import os
import sys
import asyncio
from typing import Dict, Any
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

try:
    from scripts.tsm_harness_compat import TSMKernel
except ImportError:
    from tsm_harness_compat import TSMKernel

try:
    from scripts.market_action_policy import MarketActionPolicy
except ImportError:
    from market_action_policy import MarketActionPolicy

class CoinbaseClient:
    def __init__(self, policy: MarketActionPolicy | None = None):
        self.kernel = TSMKernel()
        self.policy = policy or MarketActionPolicy.from_env(prefix="ZEC_ACTION")

    async def get_zec_price_snapshot(self) -> Dict[str, Any]:
        """Fetch current ZEC-USD price and derive a local risk-aware action policy."""
        # Opcode 0xA3: FETCH_ZEC_PRICE_SURFACE (legacy payloads may still include alpha_target)
        result = await self.kernel.execute_async([("0xA3", [])])
        data = result[0]
        market = float(data.get("market", 0.0) or 0.0)
        snapshot = self.policy.snapshot(market)
        snapshot["source"] = data.get("source", "tsm_0xA3")
        if "alpha_target" in data:
            snapshot["legacy_alpha_target"] = data.get("alpha_target")

        if market > 0:
            print(
                "[ACTION-POLICY] "
                f"Market: ${market:.2f} | "
                f"Entry ref ({snapshot['entry_improvement_pct']:.2f}% better): "
                f"${snapshot['entry_reference_price']:.2f} | "
                f"Loss alert ({snapshot['max_loss_pct']:.2f}% down): "
                f"${snapshot['loss_alert_price']:.2f}"
            )
        return snapshot

    async def get_zec_price(self) -> float:
        """Fetch current ZEC-USD market price via TSM 0xA3."""
        snapshot = await self.get_zec_price_snapshot()
        market = float(snapshot.get("market_price", 0.0) or 0.0)
        return market

    async def place_market_buy(self, amount_usd: float) -> Dict[str, Any]:
        """Place a market buy order for ZEC using USD via TSM 0xA2."""
        path = "/orders"
        payload = {
            "client_order_id": f"ZEC-BUY-{int(asyncio.get_event_loop().time())}",
            "product_id": "ZEC-USD",
            "side": "BUY",
            "order_configuration": {
                "market_market_ioc": {
                    "quote_size": str(amount_usd)
                }
            }
        }
        # Opcode 0xA2: EXECUTE_COINBASE_POST
        result = await self.kernel.execute_async([("0xA2", [path, payload])])
        return result[0]

    async def withdraw_zec(self, amount: float, address: str) -> Dict[str, Any]:
        """Withdraw ZEC to a specific address via TSM 0xA2."""
        path = "/withdrawals/crypto"
        payload = {
            "amount": str(amount),
            "currency": "ZEC",
            "crypto_address": address
        }
        # Opcode 0xA2: EXECUTE_COINBASE_POST
        result = await self.kernel.execute_async([("0xA2", [path, payload])])
        return result[0]
