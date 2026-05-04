# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import asyncio
from dataclasses import dataclass, field
import hashlib
import json
import os
import random
import time
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Mapping, TypeAlias, cast
from urllib.parse import quote, urlencode
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from io_harness_compat import fetch_network_resource
import xml.etree.ElementTree as ET

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidStatus

try:
    from scripts.mevbot_swarm_sim import Pool, SwarmSimulation, TruthQualifier
except ImportError:
    from mevbot_swarm_sim import Pool, SwarmSimulation, TruthQualifier

DEFAULT_ROUNDS = 100
DEFAULT_SIMULATION_SEED = 0
SWARM_STATE_VERSION = 2
LIQUIDITY_BANDS_BPS = (10.0, 25.0, 50.0)
LIQUIDITY_BAND_WEIGHTS = {
    "10bps": 0.5,
    "25bps": 0.3,
    "50bps": 0.2,
}
LIQUIDITY_IMPACT_THRESHOLD_BPS = LIQUIDITY_BANDS_BPS[-1]
ORDER_BOOK_LEVEL_LIMIT = 10
META_QUOTE_POLL_INTERVAL_S = 15.0
META_QUOTE_STALE_AFTER_S = 45.0
MACRO_CONTEXT_POLL_INTERVAL_S = 60.0
VENUE_BOOK_STALE_AFTER_S = 5.0
VENUE_FANIN_WARMUP_S = 3.0
PUBLIC_PROVIDER_TARGET_COUNT = 2
PAYMENT_GATE_MIN_OBSERVED_ROUNDS = 20
PAYMENT_GATE_MIN_LIQUIDITY_SCORE = 650_000.0
PAYMENT_GATE_MIN_EXECUTABLE_NOTIONAL_USD_50BPS = 600_000.0
PAYMENT_GATE_MIN_TRUTH_CONFIDENCE = 0.45
PAID_LIQUIDITY_WIRE_NOTE = (
    "Reserved integration point for future paid market-data acquisition. "
    "It exists so premium feeds can be added behind one policy boundary after "
    "free-path liquidity metrics show the spend is justified."
)
BINANCE_WS_URL = "wss://stream.binance.com:9443/stream"
BINANCE_STREAMS = (
    "solusdt@depth20@100ms",
    "btcusdt@depth20@100ms",
    "solbtc@depth20@100ms",
)
KRAKEN_WS_URL = "wss://ws.kraken.com/v2"
KRAKEN_PRODUCTS = {
    "SOL/USD": "SOLUSDT",
    "BTC/USD": "BTCUSDT",
    "SOL/BTC": "SOLBTC",
}
BYBIT_WS_URL = "wss://stream.bybit.com/v5/public/spot"
BYBIT_TOPICS = {
    "orderbook.50.SOLUSDT": "SOLUSDT",
    "orderbook.50.BTCUSDT": "BTCUSDT",
    "orderbook.50.SOLBTC": "SOLBTC",
}
COINGECKO_SIMPLE_PRICE_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,solana&vs_currencies=usd"
)
DEXSCREENER_SEARCH_QUERIES = {
    "SOLUSDT": "SOL/USDC",
    "BTCUSDT": "BTC/USDC",
}
YAHOO_STOCK_INDEX_SYMBOLS = ("SPY", "QQQ", "IWM", "DIA")
YAHOO_COMMODITY_SYMBOLS = ("CL=F", "NG=F", "GC=F")
GOOGLE_NEWS_WATCHLIST = {
    "south_pars": "South Pars North Dome gas field",
    "lng_supply": "LNG supply disruption",
    "opec": "OPEC production cut",
    "natural_gas": "natural gas field outage",
    "commodity_shock": "commodity market shock crude oil natural gas",
}
COMMODITY_NEWS_SHOCK_KEYWORDS = {
    "attack": 0.9,
    "strike": 0.9,
    "explosion": 1.0,
    "fire": 0.8,
    "halt": 0.8,
    "shutdown": 0.8,
    "evacuation": 0.6,
    "sanction": 0.6,
    "outage": 0.7,
    "disruption": 0.7,
    "cut": 0.5,
    "war": 0.9,
    "pipeline": 0.4,
}
MANIFOLD_SEARCH_TERMS = {
    "oil": "oil",
    "natural_gas": "natural gas",
    "lng": "lng",
    "opec": "opec",
}
POLYMARKET_KEYWORDS = (
    "oil",
    "gas",
    "lng",
    "energy",
    "iran",
    "qatar",
    "south pars",
    "north dome",
    "commodity",
)
DEFILLAMA_PROTOCOLS_URL = "https://api.llama.fi/protocols"
DEFILLAMA_CHAINS_URL = "https://api.llama.fi/v2/chains"
DEFILLAMA_STABLECOINS_URL = "https://stablecoins.llama.fi/stablecoins?includePrices=true"
DEFILLAMA_PERPS_OPEN_INTEREST_URL = "https://api.llama.fi/overview/open-interest"
DEFILLAMA_PROTOCOL_KEYWORDS = (
    "aave",
    "uniswap",
    "raydium",
    "jupiter",
    "hyperliquid",
    "gmx",
    "drift",
)
DEFILLAMA_CHAIN_WATCHLIST = ("Ethereum", "Solana", "Arbitrum", "Base", "BSC")
DEFILLAMA_STABLECOIN_WATCHLIST = ("USDT", "USDC", "DAI", "USDE", "FDUSD", "PYUSD")
ONEINCH_PRODUCT_API_BASE_URL = "https://api.1inch.dev"
ONEINCH_PRODUCT_API_KEY_ENV = "ONEINCH_API_KEY"
ONEINCH_PRODUCT_API_BASE_URL_ENV = "ONEINCH_PRODUCT_API_BASE_URL"
ONEINCH_PRODUCT_API_PROBE_PATH_ENV = "ONEINCH_PRODUCT_API_PROBE_PATH"
PREMIUM_WIRE_ENABLED_ENV = "ENABLE_PREMIUM_LIQUIDITY_WIRE"
ONEINCH_SPOT_PRICE_PROVIDER = "1inch_spot_price"
ONEINCH_SPOT_PRICE_POLL_INTERVAL_S = 1.0
ONEINCH_SPOT_PRICE_CHAIN_ID_ENV = "ONEINCH_SPOT_PRICE_CHAIN_ID"
ONEINCH_SPOT_PRICE_SOL_ADDRESS_ENV = "ONEINCH_SPOT_PRICE_SOL_ADDRESS"
ONEINCH_SPOT_PRICE_BTC_ADDRESS_ENV = "ONEINCH_SPOT_PRICE_BTC_ADDRESS"
ONEINCH_SPOT_PRICE_USDT_ADDRESS_ENV = "ONEINCH_SPOT_PRICE_USDT_ADDRESS"
ONEINCH_SPOT_PRICE_TOKENS_BY_CHAIN = {
    1: {
        "SOL": "0xD31a59c85aE9D8EdefEC411D448f90841571b89c",
        "BTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    }
}
REQUIRED_SYMBOLS = frozenset({"SOLUSDT", "BTCUSDT", "SOLBTC"})
Quote: TypeAlias = tuple[float, float]
SessionMetadata: TypeAlias = dict[str, object]


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PaymentGateObservation:
    observed_rounds: int
    active_public_providers: int
    provider_candidate_count: int
    best_liquidity_score: float
    best_executable_notional_usd_50bps: float
    final_truth_confidence: float
    failure_count: int
    failures: tuple[str, ...]


@dataclass(frozen=True)
class PaymentGateDecision:
    allow_activation: bool
    measured_shortfall: bool
    shortfall_score: float
    reasons: tuple[str, ...]
    observation: PaymentGateObservation
    policy_name: str = "free_path_liquidity_shortfall_v1"

    def to_record(self) -> dict[str, object]:
        return {
            "type": "payment_gate_decision",
            "policy_name": self.policy_name,
            "allow_activation": self.allow_activation,
            "measured_shortfall": self.measured_shortfall,
            "shortfall_score": self.shortfall_score,
            "reasons": list(self.reasons),
            "observed_rounds": self.observation.observed_rounds,
            "active_public_providers": self.observation.active_public_providers,
            "provider_candidate_count": self.observation.provider_candidate_count,
            "best_liquidity_score": self.observation.best_liquidity_score,
            "best_executable_notional_usd_50bps": self.observation.best_executable_notional_usd_50bps,
            "final_truth_confidence": self.observation.final_truth_confidence,
            "failure_count": self.observation.failure_count,
            "failures": list(self.observation.failures),
        }


@dataclass(frozen=True)
class OneInchProductAPIAdapter:
    base_url: str = field(
        default_factory=lambda: os.environ.get(
            ONEINCH_PRODUCT_API_BASE_URL_ENV,
            ONEINCH_PRODUCT_API_BASE_URL,
        ).rstrip("/")
    )
    api_key_env_var: str = ONEINCH_PRODUCT_API_KEY_ENV
    probe_path: str = field(
        default_factory=lambda: os.environ.get(ONEINCH_PRODUCT_API_PROBE_PATH_ENV, "").strip()
    )

    def api_key(self) -> str | None:
        api_key = os.environ.get(self.api_key_env_var, "").strip()
        return api_key or None

    def configured(self) -> bool:
        return self.api_key() is not None

    def ready(self) -> bool:
        return self.configured()

    def spot_price_chain_id(self) -> int:
        raw_value = os.environ.get(ONEINCH_SPOT_PRICE_CHAIN_ID_ENV, "1").strip()
        try:
            return int(raw_value)
        except ValueError as exc:
            raise RuntimeError(
                f"{ONEINCH_SPOT_PRICE_CHAIN_ID_ENV} must be an integer chain id"
            ) from exc

    def spot_price_token_addresses(self) -> dict[str, str]:
        chain_id = self.spot_price_chain_id()
        default_addresses = ONEINCH_SPOT_PRICE_TOKENS_BY_CHAIN.get(chain_id)
        if default_addresses is None:
            raise RuntimeError(
                f"unsupported 1inch spot-price chain id {chain_id}; set a supported chain or extend the token map"
            )

        return {
            "SOL": os.environ.get(
                ONEINCH_SPOT_PRICE_SOL_ADDRESS_ENV,
                default_addresses["SOL"],
            ).strip(),
            "BTC": os.environ.get(
                ONEINCH_SPOT_PRICE_BTC_ADDRESS_ENV,
                default_addresses["BTC"],
            ).strip(),
            "USDT": os.environ.get(
                ONEINCH_SPOT_PRICE_USDT_ADDRESS_ENV,
                default_addresses["USDT"],
            ).strip(),
        }

    def spot_price_path(self) -> str:
        token_addresses = self.spot_price_token_addresses()
        address_segment = ",".join(token_addresses.values())
        return f"/price/v1.1/{self.spot_price_chain_id()}/{address_segment}"

    def build_url(self, path: str, query: Mapping[str, object] | None = None) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{normalized_path}"
        if not query:
            return url
        query_pairs: list[tuple[str, str]] = []
        for key, value in query.items():
            if isinstance(value, list):
                for item in cast(list[object], value):
                    query_pairs.append((key, str(item)))
            elif isinstance(value, tuple):
                for item in cast(tuple[object, ...], value):
                    query_pairs.append((key, str(item)))
            else:
                query_pairs.append((key, str(value)))
        return f"{url}?{urlencode(query_pairs)}"

    def request_json(
        self,
        path: str,
        query: Mapping[str, object] | None = None,
        method: str = "GET",
        body: Mapping[str, object] | None = None,
    ) -> object:
        api_key = self.api_key()
        if api_key is None:
            raise RuntimeError(f"{self.api_key_env_var} is not set")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        return fetch_json(
            self.build_url(path, query),
            headers=headers,
            method=method,
            body=body,
        )

    def probe(self) -> object | None:
        if not self.probe_path:
            return None
        return self.request_json(self.probe_path)

    def status_record(
        self,
        *,
        gate_open: bool,
        wire_enabled: bool,
        adapter_ready: bool,
        probe_ok: bool | None,
        error: str | None = None,
    ) -> dict[str, object]:
        try:
            spot_price_path = self.spot_price_path() if self.configured() else None
        except RuntimeError as exc:
            spot_price_path = None
            error = str(exc) if error is None else error

        return {
            "type": "premium_adapter_status",
            "provider": "1inch_product_api",
            "base_url": self.base_url,
            "api_key_env_var": self.api_key_env_var,
            "probe_path": self.probe_path or None,
            "spot_price_path": spot_price_path,
            "wire_enabled": wire_enabled,
            "gate_open": gate_open,
            "configured": self.configured(),
            "adapter_ready": adapter_ready,
            "probe_ok": probe_ok,
            "error": error,
        }


@dataclass(frozen=True)
class PaymentGatePolicy:
    policy_name: str = "free_path_liquidity_shortfall_v1"
    min_observed_rounds: int = PAYMENT_GATE_MIN_OBSERVED_ROUNDS
    min_active_public_providers: int = PUBLIC_PROVIDER_TARGET_COUNT
    min_liquidity_score: float = PAYMENT_GATE_MIN_LIQUIDITY_SCORE
    min_executable_notional_usd_50bps: float = PAYMENT_GATE_MIN_EXECUTABLE_NOTIONAL_USD_50BPS
    min_truth_confidence: float = PAYMENT_GATE_MIN_TRUTH_CONFIDENCE

    def evaluate(self, observation: PaymentGateObservation) -> PaymentGateDecision:
        reasons: list[str] = []

        provider_shortfall = clamp_unit(
            (self.min_active_public_providers - observation.active_public_providers)
            / max(1, self.min_active_public_providers)
        )
        liquidity_shortfall = clamp_unit(
            (self.min_liquidity_score - observation.best_liquidity_score)
            / max(self.min_liquidity_score, 1e-9)
        )
        executable_shortfall = clamp_unit(
            (
                self.min_executable_notional_usd_50bps
                - observation.best_executable_notional_usd_50bps
            )
            / max(self.min_executable_notional_usd_50bps, 1e-9)
        )
        truth_shortfall = clamp_unit(
            (self.min_truth_confidence - observation.final_truth_confidence)
            / max(self.min_truth_confidence, 1e-9)
        )

        shortfall_score = clamp_unit(
            0.35 * provider_shortfall
            + 0.30 * liquidity_shortfall
            + 0.20 * executable_shortfall
            + 0.15 * truth_shortfall
        )

        if provider_shortfall > 0.0:
            reasons.append(
                f"active public providers below target: {observation.active_public_providers}/{self.min_active_public_providers}"
            )
        if liquidity_shortfall > 0.0:
            reasons.append(
                f"best liquidity score below threshold: {observation.best_liquidity_score:,.2f} < {self.min_liquidity_score:,.2f}"
            )
        if executable_shortfall > 0.0:
            reasons.append(
                "best executable notional @50bps below threshold: "
                f"{observation.best_executable_notional_usd_50bps:,.2f} < "
                f"{self.min_executable_notional_usd_50bps:,.2f}"
            )
        if truth_shortfall > 0.0:
            reasons.append(
                f"final truth confidence below threshold: {observation.final_truth_confidence:.4f} < {self.min_truth_confidence:.4f}"
            )

        has_measured_evidence = observation.observed_rounds >= self.min_observed_rounds
        if observation.active_public_providers == 0 and observation.failure_count > 0:
            has_measured_evidence = True
            if not reasons:
                reasons.append("all public providers are currently unavailable")
        if not has_measured_evidence:
            reasons.append(
                f"insufficient measurement window: {observation.observed_rounds} < {self.min_observed_rounds} rounds"
            )

        measured_shortfall = shortfall_score > 0.0 and has_measured_evidence
        allow_activation = measured_shortfall and (
            shortfall_score >= 0.25 or observation.active_public_providers == 0
        )

        return PaymentGateDecision(
            allow_activation=allow_activation,
            measured_shortfall=measured_shortfall,
            shortfall_score=shortfall_score,
            reasons=tuple(reasons),
            observation=observation,
            policy_name=self.policy_name,
        )


@dataclass(frozen=True)
class PaidLiquidityWirePlacement:
    enabled: bool = field(default_factory=lambda: env_flag(PREMIUM_WIRE_ENABLED_ENV))
    note: str = PAID_LIQUIDITY_WIRE_NOTE
    policy: PaymentGatePolicy = field(default_factory=PaymentGatePolicy)
    product_api_adapter: OneInchProductAPIAdapter = field(default_factory=OneInchProductAPIAdapter)

    async def try_activate(
        self,
        observation: PaymentGateObservation,
        recorder: "TickRecorder | None" = None,
    ) -> bool:
        decision = self.policy.evaluate(observation)
        if recorder is not None:
            recorder.record_event(decision.to_record())
        if not decision.allow_activation:
            if recorder is not None:
                recorder.record_event(
                    self.product_api_adapter.status_record(
                        gate_open=False,
                        wire_enabled=self.enabled,
                        adapter_ready=False,
                        probe_ok=None,
                    )
                )
            return False

        print("Payment gate opened by measured free-path shortfall.")
        for reason in decision.reasons:
            print(f"  - {reason}")

        adapter_ready = False
        probe_ok: bool | None = None
        adapter_error: str | None = None
        if self.enabled:
            if not self.product_api_adapter.configured():
                adapter_error = f"{self.product_api_adapter.api_key_env_var} is not set"
            else:
                adapter_ready = True
                if self.product_api_adapter.probe_path:
                    try:
                        _ = self.product_api_adapter.probe()
                    except (OSError, TimeoutError, ValueError, RuntimeError) as exc:
                        adapter_error = str(exc)
                        probe_ok = False
                        adapter_ready = False
                    else:
                        probe_ok = True

        if recorder is not None:
            recorder.record_event(
                self.product_api_adapter.status_record(
                    gate_open=True,
                    wire_enabled=self.enabled,
                    adapter_ready=adapter_ready,
                    probe_ok=probe_ok,
                    error=adapter_error,
                )
            )

        return self.enabled and adapter_ready


@dataclass(frozen=True)
class LiquiditySnapshot:
    round_index: int
    provider_name: str
    avg_spread_bps: float
    executable_notional_usd_50bps: float
    liquidity_score: float
    spreads_bps: dict[str, float]
    per_symbol_notional_usd_50bps: dict[str, float]
    band_executable_notional_usd: dict[str, float]
    band_liquidity_scores: dict[str, float]

    def to_record(self) -> dict[str, object]:
        return {
            "type": "liquidity_snapshot",
            "round": self.round_index,
            "provider": self.provider_name,
            "avg_spread_bps": self.avg_spread_bps,
            "executable_notional_usd_50bps": self.executable_notional_usd_50bps,
            "liquidity_score": self.liquidity_score,
            "spreads_bps": self.spreads_bps,
            "per_symbol_notional_usd_50bps": self.per_symbol_notional_usd_50bps,
            "band_executable_notional_usd": self.band_executable_notional_usd,
            "band_liquidity_scores": self.band_liquidity_scores,
            "impact_threshold_bps": LIQUIDITY_IMPACT_THRESHOLD_BPS,
            "depth_source": "order_book",
        }


@dataclass(frozen=True)
class TruthQualifierSnapshot:
    round_index: int
    provider_name: str
    truth_confidence: float
    noise_ratio: float
    liquidity_confidence: float
    venue_consensus: float
    reference_consensus: float
    meta_coverage: float
    average_intervenue_deviation_bps: float
    average_reference_deviation_bps: float
    active_order_book_providers: tuple[str, ...]
    active_quote_providers: tuple[str, ...]
    active_meta_quote_providers: tuple[str, ...]
    band_liquidity_scores: dict[str, float]
    macro_alignment: float
    cross_asset_stress: float
    commodity_shock_score: float
    betting_conviction: float
    news_shock_score: float
    defillama_protocol_tvl_stress: float
    defillama_stablecoin_stress: float
    defillama_perps_stress: float
    defillama_chain_liquidity_score: float

    def to_record(self) -> dict[str, object]:
        return {
            "type": "truth_qualifier_snapshot",
            "round": self.round_index,
            "provider": self.provider_name,
            "truth_confidence": self.truth_confidence,
            "noise_ratio": self.noise_ratio,
            "liquidity_confidence": self.liquidity_confidence,
            "venue_consensus": self.venue_consensus,
            "reference_consensus": self.reference_consensus,
            "meta_coverage": self.meta_coverage,
            "average_intervenue_deviation_bps": self.average_intervenue_deviation_bps,
            "average_reference_deviation_bps": self.average_reference_deviation_bps,
            "active_order_book_providers": list(self.active_order_book_providers),
            "active_quote_providers": list(self.active_quote_providers),
            "active_meta_quote_providers": list(self.active_meta_quote_providers),
            "band_liquidity_scores": self.band_liquidity_scores,
            "macro_alignment": self.macro_alignment,
            "cross_asset_stress": self.cross_asset_stress,
            "commodity_shock_score": self.commodity_shock_score,
            "betting_conviction": self.betting_conviction,
            "news_shock_score": self.news_shock_score,
            "defillama_protocol_tvl_stress": self.defillama_protocol_tvl_stress,
            "defillama_stablecoin_stress": self.defillama_stablecoin_stress,
            "defillama_perps_stress": self.defillama_perps_stress,
            "defillama_chain_liquidity_score": self.defillama_chain_liquidity_score,
        }

    def to_sim_truth_qualifier(self) -> TruthQualifier:
        return TruthQualifier(
            truth_confidence=self.truth_confidence,
            noise_ratio=self.noise_ratio,
            liquidity_confidence=self.liquidity_confidence,
            provider_agreement=self.venue_consensus,
            aggregator_agreement=max(self.reference_consensus, self.betting_conviction),
            active_sources=(
                len(self.active_order_book_providers)
                + len(self.active_quote_providers)
                + len(self.active_meta_quote_providers)
            ),
        )


@dataclass(frozen=True)
class MacroContextSnapshot:
    captured_at: str
    stock_index_returns_pct: dict[str, float]
    commodity_returns_pct: dict[str, float]
    manifold_markets: list[dict[str, object]]
    polymarket_markets: list[dict[str, object]]
    news_items: list[dict[str, object]]
    defillama_protocols: list[dict[str, object]]
    defillama_stablecoins: list[dict[str, object]]
    defillama_perps: list[dict[str, object]]
    defillama_chains: list[dict[str, object]]
    cross_asset_stress: float
    commodity_shock_score: float
    betting_conviction: float
    news_shock_score: float
    macro_alignment: float
    defillama_protocol_tvl_stress: float
    defillama_stablecoin_stress: float
    defillama_perps_stress: float
    defillama_chain_liquidity_score: float

    def to_record(self) -> dict[str, object]:
        return {
            "type": "macro_context_snapshot",
            "captured_at": self.captured_at,
            "stock_index_returns_pct": self.stock_index_returns_pct,
            "commodity_returns_pct": self.commodity_returns_pct,
            "manifold_markets": self.manifold_markets,
            "polymarket_markets": self.polymarket_markets,
            "news_items": self.news_items,
            "defillama_protocols": self.defillama_protocols,
            "defillama_stablecoins": self.defillama_stablecoins,
            "defillama_perps": self.defillama_perps,
            "defillama_chains": self.defillama_chains,
            "cross_asset_stress": self.cross_asset_stress,
            "commodity_shock_score": self.commodity_shock_score,
            "betting_conviction": self.betting_conviction,
            "news_shock_score": self.news_shock_score,
            "macro_alignment": self.macro_alignment,
            "defillama_protocol_tvl_stress": self.defillama_protocol_tvl_stress,
            "defillama_stablecoin_stress": self.defillama_stablecoin_stress,
            "defillama_perps_stress": self.defillama_perps_stress,
            "defillama_chain_liquidity_score": self.defillama_chain_liquidity_score,
        }

    def compact_dict(self) -> dict[str, object]:
        return {
            "captured_at": self.captured_at,
            "stock_index_returns_pct": self.stock_index_returns_pct,
            "commodity_returns_pct": self.commodity_returns_pct,
            "cross_asset_stress": self.cross_asset_stress,
            "commodity_shock_score": self.commodity_shock_score,
            "betting_conviction": self.betting_conviction,
            "news_shock_score": self.news_shock_score,
            "macro_alignment": self.macro_alignment,
            "defillama_protocol_tvl_stress": self.defillama_protocol_tvl_stress,
            "defillama_stablecoin_stress": self.defillama_stablecoin_stress,
            "defillama_perps_stress": self.defillama_perps_stress,
            "defillama_chain_liquidity_score": self.defillama_chain_liquidity_score,
            "top_news_titles": [
                cast(str, item.get("title", "")) for item in self.news_items[:3]
            ],
            "top_manifold_questions": [
                cast(str, item.get("question", "")) for item in self.manifold_markets[:2]
            ],
            "top_polymarket_questions": [
                cast(str, item.get("question", "")) for item in self.polymarket_markets[:2]
            ],
            "top_defillama_protocols": [
                cast(str, item.get("name", "")) for item in self.defillama_protocols[:3]
            ],
            "top_defillama_stablecoins": [
                cast(str, item.get("symbol", "")) for item in self.defillama_stablecoins[:3]
            ],
            "top_defillama_chains": [
                cast(str, item.get("name", "")) for item in self.defillama_chains[:3]
            ],
        }


class LiquidityTracker:
    def __init__(self):
        self.initial: LiquiditySnapshot | None = None
        self.best: LiquiditySnapshot | None = None
        self.final: LiquiditySnapshot | None = None
        self.initial_truth: TruthQualifierSnapshot | None = None
        self.best_truth: TruthQualifierSnapshot | None = None
        self.final_truth: TruthQualifierSnapshot | None = None

    def record_snapshot(
        self,
        snapshot: LiquiditySnapshot,
        truth_snapshot: TruthQualifierSnapshot,
        market_surface_record: Mapping[str, object],
        recorder: TickRecorder | None = None,
    ) -> None:
        if self.initial is None:
            self.initial = snapshot
            self.initial_truth = truth_snapshot
        if self.best is None or snapshot.liquidity_score > self.best.liquidity_score:
            self.best = snapshot
            self.best_truth = truth_snapshot
        self.final = snapshot
        self.final_truth = truth_snapshot

        if recorder is not None:
            recorder.record_event(market_surface_record)
            recorder.record_event(snapshot.to_record())
            recorder.record_event(truth_snapshot.to_record())

    def summary_record(self) -> dict[str, object] | None:
        if self.initial is None or self.best is None or self.final is None:
            return None

        return {
            "type": "liquidity_summary",
            "impact_threshold_bps": LIQUIDITY_IMPACT_THRESHOLD_BPS,
            "initial": summarize_snapshot(self.initial),
            "best": summarize_snapshot(self.best),
            "final": summarize_snapshot(self.final),
            "best_vs_initial_pct": percent_change(
                self.initial.liquidity_score, self.best.liquidity_score
            ),
            "final_vs_initial_pct": percent_change(
                self.initial.liquidity_score, self.final.liquidity_score
            ),
            "initial_truth": summarize_truth_snapshot(self.initial_truth),
            "best_truth": summarize_truth_snapshot(self.best_truth),
            "final_truth": summarize_truth_snapshot(self.final_truth),
        }


BookLevel = tuple[float, float]


def new_book_side() -> dict[float, float]:
    return {}


@dataclass
class OrderBook:
    bids: dict[float, float] = field(default_factory=new_book_side)
    asks: dict[float, float] = field(default_factory=new_book_side)

    def replace(self, bids: list[BookLevel], asks: list[BookLevel]) -> None:
        self.bids = {price: size for price, size in bids if price > 0.0 and size > 0.0}
        self.asks = {price: size for price, size in asks if price > 0.0 and size > 0.0}

    def apply_update(self, side: str, price: float, size: float) -> None:
        target = self.bids if side == "buy" else self.asks
        if size <= 0.0:
            target.pop(price, None)
        else:
            target[price] = size

    def has_top_of_book(self) -> bool:
        return bool(self.bids) and bool(self.asks)

    def sorted_bids(self, limit: int | None = None) -> list[BookLevel]:
        levels = sorted(self.bids.items(), key=lambda item: item[0], reverse=True)
        return levels if limit is None else levels[:limit]

    def sorted_asks(self, limit: int | None = None) -> list[BookLevel]:
        levels = sorted(self.asks.items(), key=lambda item: item[0])
        return levels if limit is None else levels[:limit]

    def top_quote(self) -> Quote | None:
        if not self.has_top_of_book():
            return None
        return self.sorted_bids(1)[0][0], self.sorted_asks(1)[0][0]


class OrderBookTracker:
    def __init__(self):
        self.books: dict[str, OrderBook] = {symbol: OrderBook() for symbol in REQUIRED_SYMBOLS}
        self.venue_books: dict[str, dict[str, OrderBook]] = {}
        self.quote_only_quotes: dict[str, dict[str, Quote]] = {}
        self.provider_updated_at: dict[str, float] = {}
        self.provider_status: dict[str, str] = {}
        self.provider_errors: dict[str, str] = {}
        self.meta_quotes: dict[str, dict[str, Quote]] = {}
        self.meta_quote_updated_at: dict[str, float] = {}
        self.macro_context: MacroContextSnapshot | None = None

    def _provider_books(self, provider_name: str) -> dict[str, OrderBook]:
        return self.venue_books.setdefault(
            provider_name,
            {symbol: OrderBook() for symbol in REQUIRED_SYMBOLS},
        )

    def _refresh_provider(self, provider_name: str) -> None:
        self.provider_updated_at[provider_name] = time.monotonic()
        self.provider_status[provider_name] = "connected"
        self.provider_errors.pop(provider_name, None)

    def set_provider_status(
        self,
        provider_name: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        self.provider_status[provider_name] = status
        if error_message:
            self.provider_errors[provider_name] = error_message
        elif status == "connected":
            self.provider_errors.pop(provider_name, None)

    def _active_provider_names_for_symbol(self, symbol: str) -> list[str]:
        now = time.monotonic()
        active: list[str] = []
        for provider_name, provider_books in self.venue_books.items():
            updated_at = self.provider_updated_at.get(provider_name, 0.0)
            if now - updated_at > VENUE_BOOK_STALE_AFTER_S:
                continue
            provider_book = provider_books.get(symbol)
            if provider_book is not None and provider_book.has_top_of_book():
                active.append(provider_name)
        return sorted(active)

    def _rebuild_consensus_book(self, symbol: str) -> None:
        bid_sizes: dict[float, float] = {}
        ask_sizes: dict[float, float] = {}
        for provider_name in self._active_provider_names_for_symbol(symbol):
            provider_book = self._provider_books(provider_name)[symbol]
            for price, size in provider_book.bids.items():
                bid_sizes[price] = bid_sizes.get(price, 0.0) + size
            for price, size in provider_book.asks.items():
                ask_sizes[price] = ask_sizes.get(price, 0.0) + size

        self.books[symbol].replace(list(bid_sizes.items()), list(ask_sizes.items()))

    def set_snapshot(
        self,
        provider_name: str,
        symbol: str,
        bids: list[BookLevel],
        asks: list[BookLevel],
    ) -> None:
        if symbol not in self.books:
            return
        self._provider_books(provider_name)[symbol].replace(bids, asks)
        self._refresh_provider(provider_name)
        self._rebuild_consensus_book(symbol)

    def apply_update(
        self,
        provider_name: str,
        symbol: str,
        side: str,
        price: float,
        size: float,
    ) -> None:
        if symbol not in self.books:
            return
        self._provider_books(provider_name)[symbol].apply_update(side, price, size)
        self._refresh_provider(provider_name)
        self._rebuild_consensus_book(symbol)

    def active_provider_quotes(self) -> dict[str, dict[str, Quote]]:
        provider_quotes: dict[str, dict[str, Quote]] = {}
        for provider_name in self.active_order_book_providers():
            quotes: dict[str, Quote] = {}
            for symbol, provider_book in self._provider_books(provider_name).items():
                top_quote = provider_book.top_quote()
                if top_quote is not None:
                    quotes[symbol] = top_quote
            if quotes:
                provider_quotes[provider_name] = quotes
        return provider_quotes

    def set_quote_snapshot(self, provider_name: str, quotes: Mapping[str, Quote]) -> None:
        filtered_quotes = {
            symbol: quote_value
            for symbol, quote_value in quotes.items()
            if symbol in REQUIRED_SYMBOLS
        }
        if not filtered_quotes:
            return
        self.quote_only_quotes[provider_name] = filtered_quotes
        self._refresh_provider(provider_name)

    def active_quote_provider_quotes(self) -> dict[str, dict[str, Quote]]:
        active: dict[str, dict[str, Quote]] = {}
        now = time.monotonic()
        for provider_name, quotes in self.quote_only_quotes.items():
            updated_at = self.provider_updated_at.get(provider_name, 0.0)
            if now - updated_at <= VENUE_BOOK_STALE_AFTER_S:
                active[provider_name] = quotes
        return active

    def active_quote_providers(self) -> list[str]:
        return sorted(self.active_quote_provider_quotes())

    def active_live_provider_quotes(self) -> dict[str, dict[str, Quote]]:
        provider_quotes = self.active_provider_quotes()
        for provider_name, quotes in self.active_quote_provider_quotes().items():
            existing_quotes = provider_quotes.setdefault(provider_name, {})
            for symbol, quote_value in quotes.items():
                existing_quotes.setdefault(symbol, quote_value)
        return provider_quotes

    def active_order_book_providers(self) -> list[str]:
        now = time.monotonic()
        active: list[str] = []
        for provider_name, provider_books in self.venue_books.items():
            updated_at = self.provider_updated_at.get(provider_name, 0.0)
            if now - updated_at > VENUE_BOOK_STALE_AFTER_S:
                continue
            if any(book.has_top_of_book() for book in provider_books.values()):
                active.append(provider_name)
        return sorted(active)

    def top_quotes(self) -> dict[str, Quote]:
        quotes: dict[str, Quote] = {}
        provider_quotes = self.active_live_provider_quotes()
        for symbol in REQUIRED_SYMBOLS:
            symbol_quotes = [
                provider_quote[symbol]
                for provider_quote in provider_quotes.values()
                if symbol in provider_quote
            ]
            if not symbol_quotes:
                continue

            bid_price = median_value([quote[0] for quote in symbol_quotes])
            ask_price = median_value([quote[1] for quote in symbol_quotes])
            if bid_price > ask_price:
                mid_price = midpoint(bid_price, ask_price)
                bid_price = mid_price
                ask_price = mid_price
            quotes[symbol] = (bid_price, ask_price)
        return quotes

    def consensus_provider_name(self) -> str:
        active_providers = sorted(self.active_live_provider_quotes())
        if not active_providers:
            return "consensus:none"
        return f"consensus[{','.join(active_providers)}]"

    def set_meta_quotes(self, provider_name: str, quotes: Mapping[str, Quote]) -> None:
        filtered_quotes = {
            symbol: quote_value
            for symbol, quote_value in quotes.items()
            if symbol in REQUIRED_SYMBOLS
        }
        if not filtered_quotes:
            return
        self.meta_quotes[provider_name] = filtered_quotes
        self.meta_quote_updated_at[provider_name] = time.monotonic()

    def active_meta_quotes(self) -> dict[str, dict[str, Quote]]:
        active: dict[str, dict[str, Quote]] = {}
        now = time.monotonic()
        for provider_name, quotes in self.meta_quotes.items():
            updated_at = self.meta_quote_updated_at.get(provider_name, 0.0)
            if now - updated_at <= META_QUOTE_STALE_AFTER_S:
                active[provider_name] = quotes
        return active

    def set_macro_context(self, snapshot: MacroContextSnapshot) -> None:
        self.macro_context = snapshot

    def current_macro_context(self) -> MacroContextSnapshot | None:
        return self.macro_context

    def snapshot_record(self, round_index: int, trigger_provider_name: str) -> dict[str, object]:
        books_payload: dict[str, object] = {}
        for symbol, book in self.books.items():
            if not book.has_top_of_book():
                continue
            books_payload[symbol] = {
                "bids": [[price, size] for price, size in book.sorted_bids(ORDER_BOOK_LEVEL_LIMIT)],
                "asks": [[price, size] for price, size in book.sorted_asks(ORDER_BOOK_LEVEL_LIMIT)],
            }

        return {
            "type": "market_surface_snapshot",
            "round": round_index,
            "provider": self.consensus_provider_name(),
            "trigger_provider": trigger_provider_name,
            "captured_at": utc_now_iso(),
            "level_limit": ORDER_BOOK_LEVEL_LIMIT,
            "books": books_payload,
            "active_order_book_providers": self.active_order_book_providers(),
            "active_quote_providers": self.active_quote_providers(),
            "venue_quotes": {
                provider: {
                    symbol: {"bid": quote_value[0], "ask": quote_value[1]}
                    for symbol, quote_value in quotes.items()
                }
                for provider, quotes in self.active_provider_quotes().items()
            },
            "quote_provider_quotes": {
                provider: {
                    symbol: {"bid": quote_value[0], "ask": quote_value[1]}
                    for symbol, quote_value in quotes.items()
                }
                for provider, quotes in self.active_quote_provider_quotes().items()
            },
            "provider_status": {
                provider: {
                    "status": self.provider_status.get(provider, "unknown"),
                    "error": self.provider_errors.get(provider),
                }
                for provider in sorted(set(self.provider_status) | set(self.provider_errors))
            },
            "meta_quotes": {
                provider: {
                    symbol: {"bid": quote_value[0], "ask": quote_value[1]}
                    for symbol, quote_value in quotes.items()
                }
                for provider, quotes in self.active_meta_quotes().items()
            },
            "macro_context": None if self.macro_context is None else self.macro_context.compact_dict(),
        }


class TickRecorder:
    def __init__(
        self,
        file_path: Path,
        rounds: int,
        session_metadata: Mapping[str, object] | None = None,
    ):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.file_path.open("w", encoding="utf-8", buffering=1)
        metadata: dict[str, object] = {
            "type": "session_meta",
            "version": 1,
            "created_at": utc_now_iso(),
            "session_id": self.file_path.stem,
            "target_rounds": rounds,
            "required_symbols": sorted(REQUIRED_SYMBOLS),
        }
        if session_metadata is not None:
            metadata.update(session_metadata)
        self._write(metadata)

    def _write(self, payload: Mapping[str, object]) -> None:
        self.handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def record_event(self, payload: Mapping[str, object]) -> None:
        self._write(payload)

    def record(self, provider_name: str, symbol: str, bid_price: float, ask_price: float) -> None:
        self._write(
            {
                "type": "tick",
                "captured_at": utc_now_iso(),
                "provider": provider_name,
                "symbol": symbol,
                "bid": bid_price,
                "ask": ask_price,
            }
        )

    def close(self) -> None:
        if not self.handle.closed:
            self.handle.close()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_swarm_state_path() -> Path:
    return Path("5-Applications/out/live_market_data") / "swarm_state.json"


def default_record_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("5-Applications/out/live_market_data") / f"session_{stamp}.jsonl"


def load_json_file(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return cast(dict[str, object], payload)


def write_json_file_atomic(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def load_swarm_state(state_path: Path | None, sim: SwarmSimulation) -> dict[str, object]:
    if state_path is None:
        return {
            "enabled": False,
            "path": None,
            "loaded": False,
            "generation": 0,
            "source_session_id": None,
            "rounds_completed": 0,
            "state_digest": None,
            "restore_summary": None,
            "learning_summary": sim.learning_summary(),
        }

    if not state_path.exists():
        return {
            "enabled": True,
            "path": str(state_path),
            "loaded": False,
            "generation": 0,
            "source_session_id": None,
            "rounds_completed": 0,
            "state_digest": None,
            "restore_summary": None,
            "learning_summary": sim.learning_summary(),
        }

    payload = load_json_file(state_path)
    simulation_state_obj = payload.get("simulation_state")
    simulation_state = (
        cast(dict[str, object], simulation_state_obj)
        if isinstance(simulation_state_obj, dict)
        else payload
    )
    restore_summary = sim.apply_learning_state(simulation_state)
    state_digest = hashlib.sha3_256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    generation_obj = payload.get("generation")
    source_session_id_obj = payload.get("source_session_id")
    rounds_completed_obj = payload.get("rounds_completed")
    learning_summary_obj = simulation_state.get("learning_summary")

    return {
        "enabled": True,
        "path": str(state_path),
        "loaded": True,
        "generation": generation_obj if isinstance(generation_obj, int) else 0,
        "source_session_id": (
            source_session_id_obj if isinstance(source_session_id_obj, str) else None
        ),
        "rounds_completed": (
            rounds_completed_obj if isinstance(rounds_completed_obj, int) else 0
        ),
        "state_digest": state_digest,
        "restore_summary": restore_summary,
        "learning_summary": (
            cast(dict[str, object], learning_summary_obj)
            if isinstance(learning_summary_obj, dict)
            else sim.learning_summary()
        ),
    }


def save_swarm_state(
    state_path: Path,
    sim: SwarmSimulation,
    session_id: str,
    previous_generation: int,
    session_liquidity_summary: Mapping[str, object] | None = None,
    session_mode: str = "live",
) -> dict[str, object]:
    generation = previous_generation + 1
    normalized_summary = (
        dict(session_liquidity_summary)
        if session_liquidity_summary is not None
        else None
    )
    objective_summary = sim.finalize_cross_session_objective(
        normalized_summary,
        session_id,
    )
    learning_summary = sim.learning_summary()
    payload: dict[str, object] = {
        "version": SWARM_STATE_VERSION,
        "saved_at": utc_now_iso(),
        "generation": generation,
        "source_session_id": session_id,
        "session_mode": session_mode,
        "rounds_completed": len(sim.execution_log),
        "learning_summary": learning_summary,
        "objective_summary": objective_summary,
        "session_liquidity_summary": normalized_summary,
        "simulation_state": sim.to_learning_state(),
    }
    write_json_file_atomic(state_path, payload)
    state_digest = hashlib.sha3_256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "type": "swarm_state_saved",
        "path": str(state_path),
        "generation": generation,
        "source_session_id": session_id,
        "session_mode": session_mode,
        "rounds_completed": len(sim.execution_log),
        "state_digest": state_digest,
        "learning_summary": learning_summary,
        "objective_summary": objective_summary,
    }


def resolve_rounds(requested_rounds: int | None, default_rounds: int) -> int:
    rounds = default_rounds if requested_rounds is None else requested_rounds
    if rounds <= 0:
        raise ValueError("round count must be positive")
    return rounds


def midpoint(bid_price: float, ask_price: float) -> float:
    return (bid_price + ask_price) / 2.0


def spread_bps(bid_price: float, ask_price: float) -> float:
    mid_price = midpoint(bid_price, ask_price)
    if mid_price <= 0.0:
        return 0.0
    return (ask_price - bid_price) / mid_price * 10_000.0


def band_key(impact_threshold_bps: float) -> str:
    return f"{int(impact_threshold_bps)}bps"


def clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def fetch_json(
    url: str,
    headers: Mapping[str, str] | None = None,
    method: str = "GET",
    body: Mapping[str, object] | None = None,
) -> object:
    request_headers = {"User-Agent": "research-stack/1.0"}
    if headers is not None:
        request_headers.update(headers)
    request_data = None if body is None else json.dumps(body).encode("utf-8")
    raw_bytes = fetch_network_resource(
        url=url,
        headers=request_headers,
        timeout=10,
        method=method,
        data=request_data
    )
    return json.loads(raw_bytes.decode("utf-8"))


def fetch_text(url: str) -> str:
    raw_bytes = fetch_network_resource(url=url, headers={"User-Agent": "research-stack/1.0"}, timeout=10)
    return raw_bytes.decode("utf-8", errors="replace")


def mean_or_zero(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median_value(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def try_fetch_json(url: str) -> object | None:
    try:
        return fetch_json(url)
    except (OSError, TimeoutError, ValueError):
        return None


def parse_oneinch_spot_price_map(payload: object) -> dict[str, float]:
    if not isinstance(payload, dict):
        return {}

    payload_dict = cast(dict[str, object], payload)
    result_obj = payload_dict.get("result")
    price_payload = cast(dict[str, object], result_obj) if isinstance(result_obj, dict) else payload_dict
    prices: dict[str, float] = {}
    for address_obj, value_obj in price_payload.items():
        if not isinstance(value_obj, (str, int, float)):
            continue
        try:
            prices[address_obj.lower()] = float(value_obj)
        except (TypeError, ValueError):
            continue
    return prices


def fetch_oneinch_spot_price_quotes(adapter: OneInchProductAPIAdapter) -> dict[str, Quote]:
    token_addresses = {
        asset: address.lower()
        for asset, address in adapter.spot_price_token_addresses().items()
    }
    payload = adapter.request_json(adapter.spot_price_path())
    price_map = parse_oneinch_spot_price_map(payload)

    sol_native = price_map.get(token_addresses["SOL"])
    btc_native = price_map.get(token_addresses["BTC"])
    usdt_native = price_map.get(token_addresses["USDT"])
    if sol_native is None or btc_native is None or usdt_native is None:
        return {}
    if sol_native <= 0.0 or btc_native <= 0.0 or usdt_native <= 0.0:
        return {}

    sol_usdt = sol_native / usdt_native
    btc_usdt = btc_native / usdt_native
    sol_btc = sol_native / btc_native
    return {
        "SOLUSDT": (sol_usdt, sol_usdt),
        "BTCUSDT": (btc_usdt, btc_usdt),
        "SOLBTC": (sol_btc, sol_btc),
    }


def numeric_value(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def pegged_usd_amount(value: object) -> float:
    if isinstance(value, dict):
        pegged_usd = cast(dict[str, object], value).get("peggedUSD")
        if isinstance(pegged_usd, (int, float)):
            return float(pegged_usd)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def fetch_yahoo_intraday_returns(symbols: tuple[str, ...]) -> dict[str, float]:
    returns: dict[str, float] = {}
    for symbol in symbols:
        payload = fetch_json(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}?interval=1m&range=1d"
        )
        if not isinstance(payload, dict):
            continue
        payload_dict = cast(dict[str, object], payload)
        chart_obj = payload_dict.get("chart")
        if not isinstance(chart_obj, dict):
            continue
        chart = cast(dict[str, object], chart_obj)
        result_obj = chart.get("result")
        if not isinstance(result_obj, list) or not result_obj:
            continue
        result_entry = cast(list[object], result_obj)[0]
        if not isinstance(result_entry, dict):
            continue
        result = cast(dict[str, object], result_entry)
        indicators_obj = result.get("indicators")
        if not isinstance(indicators_obj, dict):
            continue
        indicators = cast(dict[str, object], indicators_obj)
        quote_entries_obj = indicators.get("quote")
        if not isinstance(quote_entries_obj, list) or not quote_entries_obj:
            continue
        quote_entry = cast(list[object], quote_entries_obj)[0]
        if not isinstance(quote_entry, dict):
            continue
        close_series_obj = cast(dict[str, object], quote_entry).get("close")
        closes = (
            [
                float(value)
                for value in cast(list[object], close_series_obj)
                if isinstance(value, (int, float))
            ]
            if isinstance(close_series_obj, list)
            else []
        )
        if len(closes) >= 2 and closes[0] > 0.0:
            returns[symbol] = ((closes[-1] - closes[0]) / closes[0]) * 100.0
            continue

        meta_obj = result.get("meta")
        if not isinstance(meta_obj, dict):
            continue
        meta = cast(dict[str, object], meta_obj)
        regular_market_price_obj = meta.get("regularMarketPrice")
        chart_previous_close_obj = meta.get("chartPreviousClose", meta.get("previousClose"))
        if not isinstance(regular_market_price_obj, (int, float)):
            continue
        if not isinstance(chart_previous_close_obj, (int, float)):
            continue
        chart_previous_close = float(chart_previous_close_obj)
        if chart_previous_close <= 0.0:
            continue
        returns[symbol] = (
            (float(regular_market_price_obj) - chart_previous_close) / chart_previous_close
        ) * 100.0

    return returns


def fetch_defillama_protocol_context() -> tuple[list[dict[str, object]], float]:
    payload = try_fetch_json(DEFILLAMA_PROTOCOLS_URL)
    if not isinstance(payload, list):
        return [], 0.0

    matched: list[dict[str, object]] = []
    for protocol_obj in cast(list[object], payload):
        if not isinstance(protocol_obj, dict):
            continue
        protocol = cast(dict[str, object], protocol_obj)
        name_obj = protocol.get("name")
        tvl_obj = protocol.get("tvl")
        change_1d_obj = protocol.get("change_1d")
        if not isinstance(name_obj, str):
            continue
        if not isinstance(tvl_obj, (int, float)):
            continue
        if not any(keyword in name_obj.lower() for keyword in DEFILLAMA_PROTOCOL_KEYWORDS):
            continue

        matched.append(
            {
                "name": name_obj,
                "category": protocol.get("category", "unknown"),
                "chain": protocol.get("chain", "unknown"),
                "tvl": float(tvl_obj),
                "change_1d": float(change_1d_obj) if isinstance(change_1d_obj, (int, float)) else 0.0,
                "change_7d": (
                    float(change_7d_obj)
                    if isinstance((change_7d_obj := protocol.get("change_7d")), (int, float))
                    else 0.0
                ),
            }
        )

    matched.sort(key=lambda item: cast(float, item["tvl"]), reverse=True)
    watched = matched[:8]
    total_tvl = sum(cast(float, item["tvl"]) for item in watched)
    if total_tvl <= 0.0:
        return watched, 0.0

    weighted_change_1d = sum(
        abs(cast(float, item["change_1d"])) * cast(float, item["tvl"]) for item in watched
    ) / total_tvl
    return watched, clamp_unit(weighted_change_1d / 5.0)


def fetch_defillama_chain_liquidity_context() -> tuple[list[dict[str, object]], float]:
    payload = try_fetch_json(DEFILLAMA_CHAINS_URL)
    if not isinstance(payload, list):
        return [], 0.0

    watched: list[dict[str, object]] = []
    for chain_obj in cast(list[object], payload):
        if not isinstance(chain_obj, dict):
            continue
        chain = cast(dict[str, object], chain_obj)
        name_obj = chain.get("name")
        tvl_obj = chain.get("tvl")
        if not isinstance(name_obj, str):
            continue
        if name_obj not in DEFILLAMA_CHAIN_WATCHLIST:
            continue
        if not isinstance(tvl_obj, (int, float)):
            continue
        watched.append({"name": name_obj, "tvl": float(tvl_obj)})

    watched.sort(key=lambda item: cast(float, item["tvl"]), reverse=True)
    total_tvl = sum(cast(float, item["tvl"]) for item in watched)
    if total_tvl <= 0.0:
        return watched, 0.0

    concentration = max(cast(float, item["tvl"]) for item in watched) / total_tvl
    scale = clamp_unit(total_tvl / 100_000_000_000.0)
    liquidity_score = clamp_unit(scale * max(0.0, 1.15 - concentration))
    return watched, liquidity_score


def fetch_defillama_stablecoin_context() -> tuple[list[dict[str, object]], float]:
    payload = try_fetch_json(DEFILLAMA_STABLECOINS_URL)
    if not isinstance(payload, dict):
        return [], 0.0
    payload_dict = cast(dict[str, object], payload)

    pegged_assets_obj = payload_dict.get("peggedAssets")
    if not isinstance(pegged_assets_obj, list):
        return [], 0.0

    watched: list[dict[str, object]] = []
    max_price_deviation = 0.0
    max_watchlist_chain_flow = 0.0
    for asset_obj in cast(list[object], pegged_assets_obj):
        if not isinstance(asset_obj, dict):
            continue
        asset = cast(dict[str, object], asset_obj)
        symbol_obj = asset.get("symbol")
        price_obj = asset.get("price")
        if not isinstance(symbol_obj, str):
            continue
        if symbol_obj.upper() not in DEFILLAMA_STABLECOIN_WATCHLIST:
            continue
        price = float(price_obj) if isinstance(price_obj, (int, float)) else 1.0
        price_deviation = abs(price - 1.0)
        max_price_deviation = max(max_price_deviation, price_deviation)

        chain_circulating_obj = asset.get("chainCirculating")
        watchlist_chain_flow = 0.0
        if isinstance(chain_circulating_obj, dict):
            chain_circulating = cast(dict[str, object], chain_circulating_obj)
            for chain_name in DEFILLAMA_CHAIN_WATCHLIST:
                chain_stats_obj = chain_circulating.get(chain_name)
                if not isinstance(chain_stats_obj, dict):
                    continue
                chain_stats = cast(dict[str, object], chain_stats_obj)
                current_amount = pegged_usd_amount(chain_stats.get("current", {}))
                previous_amount = pegged_usd_amount(chain_stats.get("circulatingPrevDay", {}))
                if previous_amount <= 0.0:
                    continue
                watchlist_chain_flow = max(
                    watchlist_chain_flow,
                    abs(current_amount - previous_amount) / previous_amount,
                )

        max_watchlist_chain_flow = max(max_watchlist_chain_flow, watchlist_chain_flow)
        watched.append(
            {
                "symbol": symbol_obj.upper(),
                "name": asset.get("name", symbol_obj.upper()),
                "price": price,
                "price_deviation_pct": price_deviation * 100.0,
                "circulating_usd": pegged_usd_amount(asset.get("circulating", {})),
                "watchlist_chain_flow_pct": watchlist_chain_flow * 100.0,
            }
        )

    watched.sort(
        key=lambda item: (
            cast(float, item["price_deviation_pct"]),
            cast(float, item["watchlist_chain_flow_pct"]),
            cast(float, item["circulating_usd"]),
        ),
        reverse=True,
    )
    price_stress = clamp_unit(max_price_deviation / 0.02)
    flow_stress = clamp_unit(max_watchlist_chain_flow / 0.20)
    return watched[:8], clamp_unit(0.65 * price_stress + 0.35 * flow_stress)


def fetch_defillama_perps_context() -> tuple[list[dict[str, object]], float]:
    payload = try_fetch_json(DEFILLAMA_PERPS_OPEN_INTEREST_URL)
    if not isinstance(payload, dict):
        return [], 0.0
    payload_dict = cast(dict[str, object], payload)

    change_1d = numeric_value(payload_dict.get("change_1d")) or 0.0
    change_7d = numeric_value(payload_dict.get("change_7d")) or 0.0
    change_1m = numeric_value(payload_dict.get("change_1m")) or 0.0
    perps_rows: list[dict[str, object]] = [
        {
            "metric": "open_interest",
            "total24h": numeric_value(payload_dict.get("total24h")) or 0.0,
            "total7d": numeric_value(payload_dict.get("total7d")) or 0.0,
            "total30d": numeric_value(payload_dict.get("total30d")) or 0.0,
            "change_1d": change_1d,
            "change_7d": change_7d,
            "change_1m": change_1m,
        }
    ]
    perps_stress = clamp_unit(
        0.40 * clamp_unit(abs(change_1d) / 5.0)
        + 0.35 * clamp_unit(abs(change_7d) / 10.0)
        + 0.25 * clamp_unit(abs(change_1m) / 20.0)
    )
    return perps_rows, perps_stress


def score_news_item(title: str, topic: str) -> float:
    lowered = f"{topic} {title}".lower()
    score = 0.1
    for keyword, weight in COMMODITY_NEWS_SHOCK_KEYWORDS.items():
        if keyword in lowered:
            score = max(score, weight)
    if "south pars" in lowered or "north dome" in lowered:
        score = max(score, 1.0)
    return clamp_unit(score)


def fetch_google_news_watchlist() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for topic, query_text in GOOGLE_NEWS_WATCHLIST.items():
        xml_payload = fetch_text(
            f"https://news.google.com/rss/search?q={quote(query_text)}"
        )
        root = ET.fromstring(xml_payload)
        for item in root.findall(".//item")[:3]:
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            source = item.findtext("source") or ""
            items.append(
                {
                    "topic": topic,
                    "title": title,
                    "link": link,
                    "source": source,
                    "shock_score": score_news_item(title, query_text),
                }
            )

    items.sort(key=lambda item: cast(float, item["shock_score"]), reverse=True)
    return items[:10]


def fetch_manifold_bet_history_signal(contract_id: str) -> tuple[int, float]:
    payload = fetch_json(
        f"https://api.manifold.markets/v0/bets?contractId={quote(contract_id)}&limit=25"
    )
    if not isinstance(payload, list):
        return 0, 0.0

    total_change = 0.0
    count = 0
    for bet_obj in cast(list[object], payload):
        if not isinstance(bet_obj, dict):
            continue
        bet = cast(dict[str, object], bet_obj)
        prob_before_obj = bet.get("probBefore")
        prob_after_obj = bet.get("probAfter")
        if not isinstance(prob_before_obj, (int, float)):
            continue
        if not isinstance(prob_after_obj, (int, float)):
            continue
        total_change += abs(float(prob_after_obj) - float(prob_before_obj))
        count += 1

    if count == 0:
        return 0, 0.0
    return count, clamp_unit((total_change / count) * 8.0)


def fetch_manifold_betting_context() -> list[dict[str, object]]:
    markets: list[dict[str, object]] = []
    for topic, search_term in MANIFOLD_SEARCH_TERMS.items():
        payload = fetch_json(
            "https://api.manifold.markets/v0/search-markets"
            f"?term={quote(search_term)}&sort=liquidity&filter=open&contractType=BINARY&limit=3"
        )
        if not isinstance(payload, list):
            continue

        for market_obj in cast(list[object], payload)[:2]:
            if not isinstance(market_obj, dict):
                continue
            market = cast(dict[str, object], market_obj)
            contract_id = market.get("id")
            probability_obj = market.get("probability")
            volume_24h_obj = market.get("volume24Hours", 0.0)
            question_obj = market.get("question")
            if not isinstance(contract_id, str):
                continue
            if not isinstance(probability_obj, (int, float)):
                continue
            if not isinstance(question_obj, str):
                continue
            bet_count, history_signal = fetch_manifold_bet_history_signal(contract_id)
            probability = float(probability_obj)
            conviction = abs(probability - 0.5) * 2.0
            markets.append(
                {
                    "source": "manifold",
                    "topic": topic,
                    "question": question_obj,
                    "probability": probability,
                    "conviction": conviction,
                    "bet_count": bet_count,
                    "history_signal": history_signal,
                    "volume24h": float(volume_24h_obj)
                    if isinstance(volume_24h_obj, (int, float))
                    else 0.0,
                }
            )

    markets.sort(
        key=lambda market: (
            cast(float, market["conviction"]) + cast(float, market["history_signal"]),
            cast(float, market["volume24h"]),
        ),
        reverse=True,
    )
    return markets[:6]


def parse_polymarket_probability(market: dict[str, object]) -> float | None:
    last_trade_price_obj = market.get("lastTradePrice")
    if isinstance(last_trade_price_obj, (int, float)):
        return float(last_trade_price_obj)
    if isinstance(last_trade_price_obj, str):
        try:
            return float(last_trade_price_obj)
        except ValueError:
            return None

    outcome_prices_obj = market.get("outcomePrices")
    if isinstance(outcome_prices_obj, list) and outcome_prices_obj:
        first_price = cast(list[object], outcome_prices_obj)[0]
        if isinstance(first_price, (int, float)):
            return float(first_price)
        if isinstance(first_price, str):
            try:
                return float(first_price)
            except ValueError:
                return None
    return None


def fetch_polymarket_betting_context() -> list[dict[str, object]]:
    payload = fetch_json("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100")
    if not isinstance(payload, list):
        return []

    markets: list[dict[str, object]] = []
    for market_obj in cast(list[object], payload):
        if not isinstance(market_obj, dict):
            continue
        market = cast(dict[str, object], market_obj)
        question_obj = market.get("question")
        if not isinstance(question_obj, str):
            continue
        lowered_question = question_obj.lower()
        if not any(keyword in lowered_question for keyword in POLYMARKET_KEYWORDS):
            continue

        probability = parse_polymarket_probability(market)
        if probability is None:
            continue

        liquidity_obj = market.get("liquidityNum", market.get("liquidity", 0.0))
        one_day_change_obj = market.get("oneDayPriceChange", 0.0)
        conviction = abs(probability - 0.5) * 2.0
        price_change = float(one_day_change_obj) if isinstance(one_day_change_obj, (int, float)) else 0.0
        markets.append(
            {
                "source": "polymarket",
                "question": question_obj,
                "probability": probability,
                "conviction": conviction,
                "one_day_price_change": price_change,
                "liquidity": float(liquidity_obj)
                if isinstance(liquidity_obj, (int, float))
                else 0.0,
            }
        )

    markets.sort(
        key=lambda market: (
            cast(float, market["conviction"]) + abs(cast(float, market["one_day_price_change"])),
            cast(float, market["liquidity"]),
        ),
        reverse=True,
    )
    return markets[:6]


def build_macro_context_snapshot() -> MacroContextSnapshot:
    stock_index_returns = fetch_yahoo_intraday_returns(YAHOO_STOCK_INDEX_SYMBOLS)
    commodity_returns = fetch_yahoo_intraday_returns(YAHOO_COMMODITY_SYMBOLS)
    manifold_markets = fetch_manifold_betting_context()
    polymarket_markets = fetch_polymarket_betting_context()
    news_items = fetch_google_news_watchlist()
    defillama_protocols, defillama_protocol_tvl_stress = fetch_defillama_protocol_context()
    defillama_chains, defillama_chain_liquidity_score = fetch_defillama_chain_liquidity_context()
    defillama_stablecoins, defillama_stablecoin_stress = fetch_defillama_stablecoin_context()
    defillama_perps, defillama_perps_stress = fetch_defillama_perps_context()

    stock_stress = clamp_unit(abs(mean_or_zero(list(stock_index_returns.values()))) / 1.5)
    commodity_shock_score = clamp_unit(
        max((abs(value) for value in commodity_returns.values()), default=0.0) / 3.0
    )
    manifold_signal = mean_or_zero(
        [cast(float, market["conviction"]) + 0.5 * cast(float, market["history_signal"]) for market in manifold_markets]
    )
    polymarket_signal = mean_or_zero(
        [cast(float, market["conviction"]) + min(0.5, abs(cast(float, market["one_day_price_change"]))) for market in polymarket_markets]
    )
    betting_conviction = clamp_unit(0.5 * manifold_signal + 0.5 * polymarket_signal)
    news_shock_score = clamp_unit(
        mean_or_zero([cast(float, item["shock_score"]) for item in news_items[:5]])
    )
    cross_asset_stress = clamp_unit(
        0.60 * stock_stress
        + 0.20 * defillama_perps_stress
        + 0.20 * defillama_stablecoin_stress
    )

    signal_values = [
        cross_asset_stress,
        commodity_shock_score,
        betting_conviction,
        news_shock_score,
        defillama_protocol_tvl_stress,
        defillama_stablecoin_stress,
        defillama_perps_stress,
        defillama_chain_liquidity_score,
    ]
    macro_alignment = clamp_unit(
        mean_or_zero(signal_values) * (1.0 - 0.5 * (max(signal_values) - min(signal_values)))
    )

    return MacroContextSnapshot(
        captured_at=utc_now_iso(),
        stock_index_returns_pct=stock_index_returns,
        commodity_returns_pct=commodity_returns,
        manifold_markets=manifold_markets,
        polymarket_markets=polymarket_markets,
        news_items=news_items,
        defillama_protocols=defillama_protocols,
        defillama_stablecoins=defillama_stablecoins,
        defillama_perps=defillama_perps,
        defillama_chains=defillama_chains,
        cross_asset_stress=cross_asset_stress,
        commodity_shock_score=commodity_shock_score,
        betting_conviction=betting_conviction,
        news_shock_score=news_shock_score,
        macro_alignment=macro_alignment,
        defillama_protocol_tvl_stress=defillama_protocol_tvl_stress,
        defillama_stablecoin_stress=defillama_stablecoin_stress,
        defillama_perps_stress=defillama_perps_stress,
        defillama_chain_liquidity_score=defillama_chain_liquidity_score,
    )


async def poll_macro_context_sources(
    order_books: "OrderBookTracker",
    recorder: TickRecorder | None,
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        try:
            snapshot = await asyncio.to_thread(build_macro_context_snapshot)
        except (OSError, TimeoutError, ValueError, ET.ParseError) as exc:
            print(f"macro context poll failed: {exc}")
        else:
            order_books.set_macro_context(snapshot)
            if recorder is not None:
                recorder.record_event(snapshot.to_record())

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=MACRO_CONTEXT_POLL_INTERVAL_S)
        except TimeoutError:
            continue


def select_dexscreener_price_usd(payload: object, base_symbol: str) -> float | None:
    if not isinstance(payload, dict):
        return None
    payload_dict = cast(dict[str, object], payload)

    pairs_obj = payload_dict.get("pairs")
    if not isinstance(pairs_obj, list):
        return None

    best_price: float | None = None
    best_liquidity_usd = -1.0
    for pair_obj in cast(list[object], pairs_obj):
        if not isinstance(pair_obj, dict):
            continue
        pair = cast(dict[str, object], pair_obj)

        base_obj = pair.get("baseToken")
        quote_obj = pair.get("quoteToken")
        if not isinstance(base_obj, dict) or not isinstance(quote_obj, dict):
            continue

        base_token = cast(dict[str, object], base_obj)
        quote_token = cast(dict[str, object], quote_obj)
        base_symbol_obj = base_token.get("symbol")
        quote_symbol_obj = quote_token.get("symbol")
        if base_symbol_obj != base_symbol:
            continue
        if quote_symbol_obj not in {"USD", "USDC", "USDT"}:
            continue

        price_usd_obj = pair.get("priceUsd")
        liquidity_obj = pair.get("liquidity")
        if not isinstance(price_usd_obj, (str, int, float)):
            continue
        if not isinstance(liquidity_obj, dict):
            continue

        liquidity = cast(dict[str, object], liquidity_obj)
        liquidity_usd_obj = liquidity.get("usd")
        if not isinstance(liquidity_usd_obj, (str, int, float)):
            continue

        try:
            price_usd = float(price_usd_obj)
            liquidity_usd = float(liquidity_usd_obj)
        except (TypeError, ValueError):
            continue

        if liquidity_usd > best_liquidity_usd:
            best_liquidity_usd = liquidity_usd
            best_price = price_usd

    return best_price


def fetch_coingecko_meta_quotes() -> dict[str, Quote]:
    payload = fetch_json(COINGECKO_SIMPLE_PRICE_URL)
    if not isinstance(payload, dict):
        return {}
    payload_dict = cast(dict[str, object], payload)

    bitcoin_obj = payload_dict.get("bitcoin")
    solana_obj = payload_dict.get("solana")
    if not isinstance(bitcoin_obj, dict) or not isinstance(solana_obj, dict):
        return {}

    bitcoin = cast(dict[str, object], bitcoin_obj)
    solana = cast(dict[str, object], solana_obj)
    btc_usd_obj = bitcoin.get("usd")
    sol_usd_obj = solana.get("usd")
    if not isinstance(btc_usd_obj, (int, float)):
        return {}
    if not isinstance(sol_usd_obj, (int, float)):
        return {}

    btc_usd = float(btc_usd_obj)
    sol_usd = float(sol_usd_obj)
    if btc_usd <= 0.0 or sol_usd <= 0.0:
        return {}

    sol_btc = sol_usd / btc_usd
    return {
        "SOLUSDT": (sol_usd, sol_usd),
        "BTCUSDT": (btc_usd, btc_usd),
        "SOLBTC": (sol_btc, sol_btc),
    }


def fetch_dexscreener_meta_quotes() -> dict[str, Quote]:
    quotes_usd: dict[str, float] = {}
    for symbol, search_query in DEXSCREENER_SEARCH_QUERIES.items():
        payload = fetch_json(
            f"https://api.dexscreener.com/latest/dex/search?q={quote(search_query)}"
        )
        base_symbol = "SOL" if symbol == "SOLUSDT" else "BTC"
        price_usd = select_dexscreener_price_usd(payload, base_symbol)
        if price_usd is not None:
            quotes_usd[symbol] = price_usd

    sol_usd = quotes_usd.get("SOLUSDT")
    btc_usd = quotes_usd.get("BTCUSDT")
    if sol_usd is None or btc_usd is None or btc_usd <= 0.0:
        return {}

    sol_btc = sol_usd / btc_usd
    return {
        "SOLUSDT": (sol_usd, sol_usd),
        "BTCUSDT": (btc_usd, btc_usd),
        "SOLBTC": (sol_btc, sol_btc),
    }


async def poll_meta_quote_sources(
    order_books: "OrderBookTracker",
    recorder: TickRecorder | None,
    stop_event: asyncio.Event,
) -> None:
    sources = {
        "coingecko": fetch_coingecko_meta_quotes,
        "dexscreener": fetch_dexscreener_meta_quotes,
    }

    while not stop_event.is_set():
        for provider_name, fetcher in sources.items():
            try:
                quotes = await asyncio.to_thread(fetcher)
            except (OSError, TimeoutError, ValueError) as exc:
                print(f"{provider_name} meta quote poll failed: {exc}")
                continue

            if not quotes:
                continue

            order_books.set_meta_quotes(provider_name, quotes)
            if recorder is not None:
                recorder.record_event(
                    {
                        "type": "meta_quote_snapshot",
                        "provider": provider_name,
                        "captured_at": utc_now_iso(),
                        "quotes": {
                            symbol: {"bid": quote_value[0], "ask": quote_value[1]}
                            for symbol, quote_value in quotes.items()
                        },
                    }
                )

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=META_QUOTE_POLL_INTERVAL_S)
        except TimeoutError:
            continue


async def consume_1inch_spot_price_quotes(
    event_queue: asyncio.Queue[dict[str, object]],
    stop_event: asyncio.Event,
) -> None:
    adapter = OneInchProductAPIAdapter()
    provider_name = ONEINCH_SPOT_PRICE_PROVIDER
    print("Connecting to gated 1inch spot-price quote poller...")

    while not stop_event.is_set():
        quotes = await asyncio.to_thread(fetch_oneinch_spot_price_quotes, adapter)
        if quotes:
            await event_queue.put(
                {
                    "type": "quote",
                    "provider": provider_name,
                    "quotes": quotes,
                }
            )
            await event_queue.put(
                {
                    "type": "provider_status",
                    "provider": provider_name,
                    "status": "connected",
                }
            )

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=ONEINCH_SPOT_PRICE_POLL_INTERVAL_S)
        except TimeoutError:
            continue


async def maybe_start_premium_quote_provider(
    current_round: int,
    liquidity_tracker: LiquidityTracker,
    order_books: OrderBookTracker,
    provider_failures: Mapping[str, str],
    provider_candidate_count: int,
    wire_placement: PaidLiquidityWirePlacement,
    recorder: TickRecorder | None,
    venue_event_queue: asyncio.Queue[dict[str, object]],
    venue_stop: asyncio.Event,
) -> asyncio.Task[None] | None:
    adapter_ready = await wire_placement.try_activate(
        build_live_payment_gate_observation(
            current_round,
            liquidity_tracker,
            order_books,
            tuple(provider_failures.values()),
            provider_candidate_count,
        ),
        recorder,
    )
    if not adapter_ready:
        return None

    print("Starting gated premium 1inch spot-price provider.")
    return asyncio.create_task(
        run_provider_stream(
            ONEINCH_SPOT_PRICE_PROVIDER,
            consume_1inch_spot_price_quotes,
            venue_event_queue,
            venue_stop,
        )
    )


def parse_price_size_levels(raw_levels: object, expected_len: int = 2) -> list[BookLevel]:
    if not isinstance(raw_levels, list):
        return []

    levels: list[BookLevel] = []
    for raw_level_obj in cast(list[object], raw_levels):
        if not isinstance(raw_level_obj, list):
            continue

        raw_level = cast(list[object], raw_level_obj)
        if len(raw_level) < expected_len:
            continue

        price_obj = raw_level[0]
        size_obj = raw_level[1]
        if not isinstance(price_obj, (str, int, float)):
            continue
        if not isinstance(size_obj, (str, int, float)):
            continue

        try:
            price = float(price_obj)
            size = float(size_obj)
        except (TypeError, ValueError):
            continue

        levels.append((price, size))

    return levels


def quote_notional_to_usd(symbol: str, quote_notional: float, latest_quotes: Mapping[str, Quote]) -> float:
    if symbol in {"SOLUSDT", "BTCUSDT"}:
        return quote_notional
    if symbol == "SOLBTC":
        btc_mid = midpoint(*latest_quotes["BTCUSDT"])
        return quote_notional * btc_mid
    raise ValueError(f"Unsupported symbol for USD conversion: {symbol}")


def two_sided_notional_within_band_usd(
    symbol: str,
    order_book: OrderBook,
    latest_quotes: Mapping[str, Quote],
    impact_threshold_bps: float,
) -> float:
    bid_price, ask_price = latest_quotes[symbol]
    mid_price = midpoint(bid_price, ask_price)
    threshold_multiplier = impact_threshold_bps / 10_000.0
    min_bid_price = mid_price * (1.0 - threshold_multiplier)
    max_ask_price = mid_price * (1.0 + threshold_multiplier)

    bid_quote_notional = 0.0
    for price, size in order_book.sorted_bids(ORDER_BOOK_LEVEL_LIMIT):
        if price < min_bid_price:
            break
        bid_quote_notional += price * size

    ask_quote_notional = 0.0
    for price, size in order_book.sorted_asks(ORDER_BOOK_LEVEL_LIMIT):
        if price > max_ask_price:
            break
        ask_quote_notional += price * size

    bid_notional_usd = quote_notional_to_usd(symbol, bid_quote_notional, latest_quotes)
    ask_notional_usd = quote_notional_to_usd(symbol, ask_quote_notional, latest_quotes)
    return min(bid_notional_usd, ask_notional_usd)


def build_liquidity_snapshot(
    round_index: int,
    provider_name: str,
    latest_quotes: Mapping[str, Quote],
    order_books: OrderBookTracker,
) -> LiquiditySnapshot:
    spreads_bps = {
        symbol: spread_bps(bid_price, ask_price)
        for symbol, (bid_price, ask_price) in latest_quotes.items()
        if symbol in REQUIRED_SYMBOLS
    }
    avg_spread = sum(spreads_bps.values()) / max(1, len(spreads_bps))

    band_executable_notional_usd: dict[str, float] = {}
    band_liquidity_scores: dict[str, float] = {}
    per_symbol_notional_usd: dict[str, float] = {}
    for impact_threshold_bps in LIQUIDITY_BANDS_BPS:
        current_band_per_symbol = {
            symbol: two_sided_notional_within_band_usd(
                symbol,
                order_books.books[symbol],
                latest_quotes,
                impact_threshold_bps,
            )
            for symbol in REQUIRED_SYMBOLS
        }
        band_name = band_key(impact_threshold_bps)
        band_notional = sum(current_band_per_symbol.values())
        band_executable_notional_usd[band_name] = band_notional
        band_liquidity_scores[band_name] = band_notional / max(avg_spread, 1e-9)
        if impact_threshold_bps == LIQUIDITY_IMPACT_THRESHOLD_BPS:
            per_symbol_notional_usd = current_band_per_symbol

    executable_notional_usd = band_executable_notional_usd[band_key(LIQUIDITY_IMPACT_THRESHOLD_BPS)]
    liquidity_score = sum(
        weight * band_liquidity_scores.get(band_name, 0.0)
        for band_name, weight in LIQUIDITY_BAND_WEIGHTS.items()
    )

    return LiquiditySnapshot(
        round_index=round_index,
        provider_name=provider_name,
        avg_spread_bps=avg_spread,
        executable_notional_usd_50bps=executable_notional_usd,
        liquidity_score=liquidity_score,
        spreads_bps=spreads_bps,
        per_symbol_notional_usd_50bps=per_symbol_notional_usd,
        band_executable_notional_usd=band_executable_notional_usd,
        band_liquidity_scores=band_liquidity_scores,
    )


def build_truth_qualifier_snapshot(
    round_index: int,
    provider_name: str,
    latest_quotes: Mapping[str, Quote],
    order_books: OrderBookTracker,
    liquidity_snapshot: LiquiditySnapshot,
) -> TruthQualifierSnapshot:
    active_live_provider_quotes = order_books.active_live_provider_quotes()
    active_order_book_providers = tuple(order_books.active_order_book_providers())
    active_quote_providers = tuple(order_books.active_quote_providers())
    active_meta_quotes = order_books.active_meta_quotes()
    intervenue_deviations_bps: list[float] = []
    reference_deviations_bps: list[float] = []

    for symbol, current_quote in latest_quotes.items():
        current_mid = midpoint(*current_quote)
        if current_mid <= 0.0:
            continue

        provider_mids = [
            midpoint(*quotes[symbol])
            for quotes in active_live_provider_quotes.values()
            if symbol in quotes and midpoint(*quotes[symbol]) > 0.0
        ]
        if len(provider_mids) >= 2:
            provider_mid_consensus = median_value(provider_mids)
            intervenue_deviations_bps.extend(
                abs(provider_mid - provider_mid_consensus)
                / max(provider_mid_consensus, 1e-9)
                * 10_000.0
                for provider_mid in provider_mids
            )

        reference_mids = [
            midpoint(*quotes[symbol])
            for quotes in active_meta_quotes.values()
            if symbol in quotes and midpoint(*quotes[symbol]) > 0.0
        ]
        if not reference_mids:
            continue

        reference_mid = sum(reference_mids) / len(reference_mids)
        reference_deviations_bps.append(
            abs(current_mid - reference_mid) / max(reference_mid, 1e-9) * 10_000.0
        )

    average_reference_deviation_bps = (
        sum(reference_deviations_bps) / len(reference_deviations_bps)
        if reference_deviations_bps
        else 25.0
    )
    if len(active_live_provider_quotes) >= 2 and intervenue_deviations_bps:
        average_intervenue_deviation_bps = sum(intervenue_deviations_bps) / len(
            intervenue_deviations_bps
        )
        venue_consensus = clamp_unit(1.0 - average_intervenue_deviation_bps / 20.0)
    elif len(active_live_provider_quotes) == 1:
        average_intervenue_deviation_bps = 25.0
        venue_consensus = 0.35
    else:
        average_intervenue_deviation_bps = 50.0
        venue_consensus = 0.0
    reference_consensus = clamp_unit(1.0 - average_reference_deviation_bps / 50.0)
    meta_coverage = len(active_meta_quotes) / 2.0
    venue_coverage = clamp_unit(len(active_order_book_providers) / PUBLIC_PROVIDER_TARGET_COUNT)
    score_10 = liquidity_snapshot.band_liquidity_scores.get("10bps", 0.0)
    score_25 = liquidity_snapshot.band_liquidity_scores.get("25bps", 0.0)
    score_50 = liquidity_snapshot.band_liquidity_scores.get("50bps", 0.0)
    if score_50 <= 0.0:
        liquidity_confidence = 0.0
    else:
        liquidity_confidence = clamp_unit(
            0.6 * min(1.0, score_10 / score_50) + 0.4 * min(1.0, score_25 / score_50)
        )

    macro_context = order_books.current_macro_context()
    if macro_context is None:
        macro_alignment = 0.0
        cross_asset_stress = 0.0
        commodity_shock_score = 0.0
        betting_conviction = 0.0
        news_shock_score = 0.0
        defillama_protocol_tvl_stress = 0.0
        defillama_stablecoin_stress = 0.0
        defillama_perps_stress = 0.0
        defillama_chain_liquidity_score = 0.0
    else:
        macro_alignment = macro_context.macro_alignment
        cross_asset_stress = macro_context.cross_asset_stress
        commodity_shock_score = macro_context.commodity_shock_score
        betting_conviction = macro_context.betting_conviction
        news_shock_score = macro_context.news_shock_score
        defillama_protocol_tvl_stress = macro_context.defillama_protocol_tvl_stress
        defillama_stablecoin_stress = macro_context.defillama_stablecoin_stress
        defillama_perps_stress = macro_context.defillama_perps_stress
        defillama_chain_liquidity_score = macro_context.defillama_chain_liquidity_score

    macro_signal = clamp_unit(
        0.22 * macro_alignment
        + 0.10 * cross_asset_stress
        + 0.13 * commodity_shock_score
        + 0.12 * betting_conviction
        + 0.08 * news_shock_score
        + 0.12 * defillama_protocol_tvl_stress
        + 0.10 * defillama_stablecoin_stress
        + 0.08 * defillama_perps_stress
        + 0.05 * defillama_chain_liquidity_score
    )
    truth_confidence = clamp_unit(
        0.30 * venue_consensus
        + 0.20 * reference_consensus
        + 0.20 * liquidity_confidence
        + 0.10 * meta_coverage
        + 0.10 * venue_coverage
        + 0.10 * macro_signal
    )
    noise_ratio = clamp_unit(
        1.0
        - truth_confidence
        + 0.10 * (1.0 - venue_consensus)
        + 0.05 * (1.0 - reference_consensus)
        + 0.05 * (1.0 - macro_alignment)
    )

    return TruthQualifierSnapshot(
        round_index=round_index,
        provider_name=provider_name,
        truth_confidence=truth_confidence,
        noise_ratio=noise_ratio,
        liquidity_confidence=liquidity_confidence,
        venue_consensus=venue_consensus,
        reference_consensus=reference_consensus,
        meta_coverage=meta_coverage,
        average_intervenue_deviation_bps=average_intervenue_deviation_bps,
        average_reference_deviation_bps=average_reference_deviation_bps,
        active_order_book_providers=active_order_book_providers,
        active_quote_providers=active_quote_providers,
        active_meta_quote_providers=tuple(sorted(active_meta_quotes)),
        band_liquidity_scores=liquidity_snapshot.band_liquidity_scores,
        macro_alignment=macro_alignment,
        cross_asset_stress=cross_asset_stress,
        commodity_shock_score=commodity_shock_score,
        betting_conviction=betting_conviction,
        news_shock_score=news_shock_score,
        defillama_protocol_tvl_stress=defillama_protocol_tvl_stress,
        defillama_stablecoin_stress=defillama_stablecoin_stress,
        defillama_perps_stress=defillama_perps_stress,
        defillama_chain_liquidity_score=defillama_chain_liquidity_score,
    )


def summarize_snapshot(snapshot: LiquiditySnapshot) -> dict[str, object]:
    return {
        "round": snapshot.round_index,
        "provider": snapshot.provider_name,
        "avg_spread_bps": snapshot.avg_spread_bps,
        "executable_notional_usd_50bps": snapshot.executable_notional_usd_50bps,
        "liquidity_score": snapshot.liquidity_score,
        "per_symbol_notional_usd_50bps": snapshot.per_symbol_notional_usd_50bps,
        "band_executable_notional_usd": snapshot.band_executable_notional_usd,
        "band_liquidity_scores": snapshot.band_liquidity_scores,
    }


def summarize_truth_snapshot(snapshot: TruthQualifierSnapshot | None) -> dict[str, object] | None:
    if snapshot is None:
        return None

    return {
        "round": snapshot.round_index,
        "provider": snapshot.provider_name,
        "truth_confidence": snapshot.truth_confidence,
        "noise_ratio": snapshot.noise_ratio,
        "liquidity_confidence": snapshot.liquidity_confidence,
        "venue_consensus": snapshot.venue_consensus,
        "reference_consensus": snapshot.reference_consensus,
        "meta_coverage": snapshot.meta_coverage,
        "average_intervenue_deviation_bps": snapshot.average_intervenue_deviation_bps,
        "average_reference_deviation_bps": snapshot.average_reference_deviation_bps,
        "active_order_book_providers": list(snapshot.active_order_book_providers),
        "active_quote_providers": list(snapshot.active_quote_providers),
        "active_meta_quote_providers": list(snapshot.active_meta_quote_providers),
        "macro_alignment": snapshot.macro_alignment,
        "cross_asset_stress": snapshot.cross_asset_stress,
        "commodity_shock_score": snapshot.commodity_shock_score,
        "betting_conviction": snapshot.betting_conviction,
        "news_shock_score": snapshot.news_shock_score,
        "defillama_protocol_tvl_stress": snapshot.defillama_protocol_tvl_stress,
        "defillama_stablecoin_stress": snapshot.defillama_stablecoin_stress,
        "defillama_perps_stress": snapshot.defillama_perps_stress,
        "defillama_chain_liquidity_score": snapshot.defillama_chain_liquidity_score,
    }


def percent_change(baseline: float, value: float) -> float:
    if baseline <= 0.0:
        return 0.0
    return ((value - baseline) / baseline) * 100.0


def print_liquidity_summary_record(summary: dict[str, object] | None) -> None:
    if summary is None:
        print("\nNo liquidity summary available.")
        return

    initial = cast(dict[str, object], summary["initial"])
    best = cast(dict[str, object], summary["best"])
    final = cast(dict[str, object], summary["final"])
    best_vs_initial = cast(float, summary["best_vs_initial_pct"])
    final_vs_initial = cast(float, summary["final_vs_initial_pct"])
    final_truth = cast(dict[str, object] | None, summary.get("final_truth"))

    def _format_band_scores(snapshot: dict[str, object]) -> str:
        band_scores_obj = snapshot.get("band_liquidity_scores", {})
        if not isinstance(band_scores_obj, dict):
            return "Bands=n/a"
        band_scores = cast(dict[str, object], band_scores_obj)
        return (
            f"Bands 10/25/50={float(cast(float, band_scores.get('10bps', 0.0))):,.2f}/"
            f"{float(cast(float, band_scores.get('25bps', 0.0))):,.2f}/"
            f"{float(cast(float, band_scores.get('50bps', 0.0))):,.2f}"
        )

    print("\n" + "=" * 80)
    print("LIQUIDITY PROBE")
    print("=" * 80)
    print(
        "Wire note: paid feed integration is intentionally disabled until the free path "
        "shows measurable liquidity improvement."
    )
    print(
        f"Initial  | Round {cast(int, initial['round']) + 1:03d} | "
        f"Spread={cast(float, initial['avg_spread_bps']):8.4f} bps | "
        f"Exec@50bps=${cast(float, initial['executable_notional_usd_50bps']):12,.2f} | "
        f"Score={cast(float, initial['liquidity_score']):12,.2f}"
    )
    print(f"          {_format_band_scores(initial)}")
    print(
        f"Best     | Round {cast(int, best['round']) + 1:03d} | "
        f"Spread={cast(float, best['avg_spread_bps']):8.4f} bps | "
        f"Exec@50bps=${cast(float, best['executable_notional_usd_50bps']):12,.2f} | "
        f"Score={cast(float, best['liquidity_score']):12,.2f} | "
        f"Delta={best_vs_initial:+7.2f}%"
    )
    print(f"          {_format_band_scores(best)}")
    print(
        f"Final    | Round {cast(int, final['round']) + 1:03d} | "
        f"Spread={cast(float, final['avg_spread_bps']):8.4f} bps | "
        f"Exec@50bps=${cast(float, final['executable_notional_usd_50bps']):12,.2f} | "
        f"Score={cast(float, final['liquidity_score']):12,.2f} | "
        f"Delta={final_vs_initial:+7.2f}%"
    )
    print(f"          {_format_band_scores(final)}")
    if final_truth is not None:
        print(
            "Truth    | "
            f"Confidence={cast(float, final_truth.get('truth_confidence', 0.0)):.4f} | "
            f"Noise={cast(float, final_truth.get('noise_ratio', 0.0)):.4f} | "
            f"LiquidityConf={cast(float, final_truth.get('liquidity_confidence', 0.0)):.4f} | "
            f"VenueConsensus={cast(float, final_truth.get('venue_consensus', 0.0)):.4f} | "
            f"RefConsensus={cast(float, final_truth.get('reference_consensus', 0.0)):.4f} | "
            f"Macro={cast(float, final_truth.get('macro_alignment', 0.0)):.4f} | "
            f"CommodityShock={cast(float, final_truth.get('commodity_shock_score', 0.0)):.4f} | "
            f"Betting={cast(float, final_truth.get('betting_conviction', 0.0)):.4f} | "
            f"News={cast(float, final_truth.get('news_shock_score', 0.0)):.4f} | "
            f"LlamaStable={cast(float, final_truth.get('defillama_stablecoin_stress', 0.0)):.4f} | "
            f"LlamaPerps={cast(float, final_truth.get('defillama_perps_stress', 0.0)):.4f} | "
            f"LlamaChain={cast(float, final_truth.get('defillama_chain_liquidity_score', 0.0)):.4f}"
        )


def print_liquidity_summary(tracker: LiquidityTracker) -> None:
    print_liquidity_summary_record(tracker.summary_record())


def print_session_comparison(
    baseline_path: Path,
    baseline_metadata: SessionMetadata,
    baseline_summary: dict[str, object],
    candidate_path: Path,
    candidate_metadata: SessionMetadata,
    candidate_summary: dict[str, object],
) -> None:
    baseline_best = cast(dict[str, object], baseline_summary["best"])
    candidate_best = cast(dict[str, object], candidate_summary["best"])
    baseline_final = cast(dict[str, object], baseline_summary["final"])
    candidate_final = cast(dict[str, object], candidate_summary["final"])
    baseline_final_truth = cast(dict[str, object] | None, baseline_summary.get("final_truth"))
    candidate_final_truth = cast(dict[str, object] | None, candidate_summary.get("final_truth"))

    best_score_delta = percent_change(
        cast(float, baseline_best["liquidity_score"]),
        cast(float, candidate_best["liquidity_score"]),
    )
    final_score_delta = percent_change(
        cast(float, baseline_final["liquidity_score"]),
        cast(float, candidate_final["liquidity_score"]),
    )
    best_notional_delta = percent_change(
        cast(float, baseline_best["executable_notional_usd_50bps"]),
        cast(float, candidate_best["executable_notional_usd_50bps"]),
    )
    best_spread_delta = percent_change(
        cast(float, baseline_best["avg_spread_bps"]),
        cast(float, candidate_best["avg_spread_bps"]),
    )

    baseline_session = baseline_metadata.get("session_id", baseline_path.stem)
    candidate_session = candidate_metadata.get("session_id", candidate_path.stem)
    baseline_warm = bool(baseline_metadata.get("swarm_state_loaded", False))
    candidate_warm = bool(candidate_metadata.get("swarm_state_loaded", False))

    print("\n" + "=" * 80)
    print("LIQUIDITY SESSION COMPARISON")
    print("=" * 80)
    print(f"Baseline : {baseline_session} ({baseline_path})")
    print(f"Candidate: {candidate_session} ({candidate_path})")
    if baseline_warm or candidate_warm:
        print(
            "Warm start          : "
            f"baseline loaded={baseline_warm} "
            f"(gen {baseline_metadata.get('swarm_state_generation_in', 0)}), "
            f"candidate loaded={candidate_warm} "
            f"(gen {candidate_metadata.get('swarm_state_generation_in', 0)})"
        )
    print(
        f"Best score delta     : {best_score_delta:+7.2f}% "
        f"({cast(float, baseline_best['liquidity_score']):,.2f} -> "
        f"{cast(float, candidate_best['liquidity_score']):,.2f})"
    )
    print(
        f"Final score delta    : {final_score_delta:+7.2f}% "
        f"({cast(float, baseline_final['liquidity_score']):,.2f} -> "
        f"{cast(float, candidate_final['liquidity_score']):,.2f})"
    )
    print(
        f"Best exec@50bps delta: {best_notional_delta:+7.2f}% "
        f"(${cast(float, baseline_best['executable_notional_usd_50bps']):,.2f} -> "
        f"${cast(float, candidate_best['executable_notional_usd_50bps']):,.2f})"
    )
    print(
        f"Best spread delta    : {best_spread_delta:+7.2f}% "
        f"({cast(float, baseline_best['avg_spread_bps']):.4f} bps -> "
        f"{cast(float, candidate_best['avg_spread_bps']):.4f} bps; negative is tighter)"
    )

    truth_gate_open = True
    if baseline_final_truth is not None and candidate_final_truth is not None:
        truth_confidence_delta = percent_change(
            cast(float, baseline_final_truth["truth_confidence"]),
            cast(float, candidate_final_truth["truth_confidence"]),
        )
        print(
            f"Truth confidence delta: {truth_confidence_delta:+7.2f}% "
            f"({cast(float, baseline_final_truth['truth_confidence']):.4f} -> "
            f"{cast(float, candidate_final_truth['truth_confidence']):.4f})"
        )
        truth_gate_open = cast(float, candidate_final_truth["truth_confidence"]) >= (
            cast(float, baseline_final_truth["truth_confidence"]) * 0.9
        )

    improved = cast(float, candidate_best["liquidity_score"]) > cast(
        float, baseline_best["liquidity_score"]
    )
    verdict = "IMPROVED" if improved and truth_gate_open else "NO IMPROVEMENT DETECTED"
    print(f"Verdict  : {verdict}")


def derive_mode_session_key_hex(simulation_seed: int) -> str:
    material = f"live-market-data:{simulation_seed}".encode("utf-8")
    return hashlib.sha3_256(material).hexdigest()


def build_simulation(rounds: int, simulation_seed: int) -> SwarmSimulation:
    previous_key = os.getenv("WAVEPROBE_MODE_SESSION_KEY")
    os.environ["WAVEPROBE_MODE_SESSION_KEY"] = derive_mode_session_key_hex(simulation_seed)
    random.seed(simulation_seed)

    try:
        return SwarmSimulation(num_bots=50, num_rounds=rounds)
    finally:
        if previous_key is None:
            os.environ.pop("WAVEPROBE_MODE_SESSION_KEY", None)
        else:
            os.environ["WAVEPROBE_MODE_SESSION_KEY"] = previous_key


def update_pool_from_binance(pool: Pool, bid_price: float, ask_price: float) -> None:
    """
    Updates the AMM Pool reserve ratios to match the live Binance orderbook midpoint.
    We maintain the existing pool depth (k) but shift the reserves to force the price 
    P = reserve_b / reserve_a to equal the live mid_price.
    """
    if bid_price <= 0.0 or ask_price <= 0.0:
        return

    mid_price = (bid_price + ask_price) / 2.0

    # Constant product: k = reserve_a * reserve_b
    k = pool.reserve_a * pool.reserve_b
    if k <= 0.0:
        return

    # Required calculation to set P = mid_price:
    # P = pool.reserve_b / pool.reserve_a
    # k = pool.reserve_a * (pool.reserve_a * P)  => pool.reserve_a = sqrt(k/P)

    new_reserve_a = (k / mid_price) ** 0.5
    new_reserve_b = new_reserve_a * mid_price

    pool.reserve_a = new_reserve_a
    pool.reserve_b = new_reserve_b


def decode_json_message(message: str | bytes) -> dict[str, object] | None:
    if isinstance(message, bytes):
        try:
            message = message.decode("utf-8")
        except UnicodeDecodeError:
            return None

    try:
        payload_obj = json.loads(message)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload_obj, dict):
        return None
    return cast(dict[str, object], payload_obj)


def iter_session_records(session_path: Path) -> Iterator[dict[str, object]]:
    with session_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue

            payload = decode_json_message(line)
            if payload is None:
                raise ValueError(f"Invalid JSON in session file {session_path} at line {line_number}")

            yield payload


def read_replay_metadata(replay_path: Path) -> SessionMetadata:
    for payload in iter_session_records(replay_path):
        if payload.get("type") == "session_meta":
            return payload
        break

    return {}


def iter_replay_ticks(replay_path: Path) -> Iterator[tuple[str, str, float, float]]:
    for line_number, payload in enumerate(iter_session_records(replay_path), 1):
        record_type = payload.get("type")
        if record_type == "session_meta":
            continue
        if record_type != "tick":
            continue

        provider_obj = payload.get("provider")
        symbol_obj = payload.get("symbol")
        bid_obj = payload.get("bid")
        ask_obj = payload.get("ask")

        if not isinstance(provider_obj, str):
            raise ValueError(f"Replay tick at line {line_number} is missing a valid provider")
        if not isinstance(symbol_obj, str):
            raise ValueError(f"Replay tick at line {line_number} is missing a valid symbol")
        if not isinstance(bid_obj, (str, int, float)):
            raise ValueError(f"Replay tick at line {line_number} is missing a valid bid")
        if not isinstance(ask_obj, (str, int, float)):
            raise ValueError(f"Replay tick at line {line_number} is missing a valid ask")

        yield provider_obj, symbol_obj, float(bid_obj), float(ask_obj)


def read_recorded_liquidity_summary(session_path: Path) -> tuple[SessionMetadata, dict[str, object]]:
    metadata: SessionMetadata = {}
    summary: dict[str, object] | None = None
    snapshots: list[dict[str, object]] = []

    for payload in iter_session_records(session_path):
        record_type = payload.get("type")
        if record_type == "session_meta" and not metadata:
            metadata = payload
        elif record_type == "liquidity_summary":
            summary = payload
        elif record_type == "liquidity_snapshot":
            snapshots.append(payload)

    if summary is not None:
        return metadata, summary

    if not snapshots:
        raise ValueError(f"No liquidity records found in session file {session_path}")

    initial = snapshots[0]
    best = max(snapshots, key=lambda payload: cast(float, payload["liquidity_score"]))
    final = snapshots[-1]
    derived_summary: dict[str, object] = {
        "type": "liquidity_summary",
        "impact_threshold_bps": LIQUIDITY_IMPACT_THRESHOLD_BPS,
        "initial": summarize_snapshot_record(initial),
        "best": summarize_snapshot_record(best),
        "final": summarize_snapshot_record(final),
        "best_vs_initial_pct": percent_change(
            cast(float, initial["liquidity_score"]), cast(float, best["liquidity_score"])
        ),
        "final_vs_initial_pct": percent_change(
            cast(float, initial["liquidity_score"]), cast(float, final["liquidity_score"])
        ),
    }
    return metadata, derived_summary


def summarize_snapshot_record(snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "round": snapshot["round"],
        "provider": snapshot["provider"],
        "avg_spread_bps": snapshot["avg_spread_bps"],
        "executable_notional_usd_50bps": snapshot["executable_notional_usd_50bps"],
        "liquidity_score": snapshot["liquidity_score"],
        "per_symbol_notional_usd_50bps": snapshot.get("per_symbol_notional_usd_50bps", {}),
        "band_executable_notional_usd": snapshot.get("band_executable_notional_usd", {}),
        "band_liquidity_scores": snapshot.get("band_liquidity_scores", {}),
    }


def read_recorded_truth_qualifiers(replay_path: Path) -> dict[int, TruthQualifier]:
    truth_by_round: dict[int, TruthQualifier] = {}
    for payload in iter_session_records(replay_path):
        if payload.get("type") != "truth_qualifier_snapshot":
            continue

        round_obj = payload.get("round")
        truth_confidence_obj = payload.get("truth_confidence")
        noise_ratio_obj = payload.get("noise_ratio")
        liquidity_confidence_obj = payload.get("liquidity_confidence")
        venue_consensus_obj = payload.get("venue_consensus", payload.get("reference_consensus", 0.0))
        reference_consensus_obj = payload.get("reference_consensus")
        if not isinstance(round_obj, int):
            continue
        if not isinstance(truth_confidence_obj, (int, float)):
            continue
        if not isinstance(noise_ratio_obj, (int, float)):
            continue
        if not isinstance(liquidity_confidence_obj, (int, float)):
            continue
        if not isinstance(reference_consensus_obj, (int, float)):
            continue
        if not isinstance(venue_consensus_obj, (int, float)):
            continue
        betting_conviction_obj = payload.get("betting_conviction", 0.0)

        active_order_book_providers_obj = payload.get("active_order_book_providers", [])
        active_quote_providers_obj = payload.get("active_quote_providers", [])
        active_sources_obj = payload.get("active_meta_quote_providers", [])
        active_meta_sources = (
            len(cast(list[object], active_sources_obj)) if isinstance(active_sources_obj, list) else 0
        )
        active_order_book_sources = (
            len(cast(list[object], active_order_book_providers_obj))
            if isinstance(active_order_book_providers_obj, list)
            else 0
        )
        active_quote_sources = (
            len(cast(list[object], active_quote_providers_obj))
            if isinstance(active_quote_providers_obj, list)
            else 0
        )
        truth_by_round[round_obj] = TruthQualifier(
            truth_confidence=float(truth_confidence_obj),
            noise_ratio=float(noise_ratio_obj),
            liquidity_confidence=float(liquidity_confidence_obj),
            provider_agreement=float(venue_consensus_obj),
            aggregator_agreement=max(
                float(reference_consensus_obj),
                float(betting_conviction_obj)
                if isinstance(betting_conviction_obj, (int, float))
                else 0.0,
            ),
            active_sources=active_order_book_sources + active_quote_sources + active_meta_sources,
        )

    return truth_by_round


def extract_binance_order_book(message: str | bytes) -> tuple[str, list[BookLevel], list[BookLevel]] | None:
    payload = decode_json_message(message)
    if payload is None:
        return None

    raw_data = payload["data"] if "data" in payload else payload
    if not isinstance(raw_data, dict):
        return None
    data = cast(dict[str, object], raw_data)

    symbol_obj = data.get("s")
    if not isinstance(symbol_obj, str):
        stream_name = payload.get("stream")
        if isinstance(stream_name, str):
            symbol_obj = stream_name.split("@", maxsplit=1)[0].upper()
    if not isinstance(symbol_obj, str):
        return None

    bids = parse_price_size_levels(data.get("bids", []))
    asks = parse_price_size_levels(data.get("asks", []))
    if not bids or not asks:
        return None

    return symbol_obj, bids, asks


def parse_kraken_levels(raw_levels: object) -> list[BookLevel]:
    if not isinstance(raw_levels, list):
        return []

    levels: list[BookLevel] = []
    for raw_level_obj in cast(list[object], raw_levels):
        if not isinstance(raw_level_obj, dict):
            continue

        raw_level = cast(dict[str, object], raw_level_obj)
        price_obj = raw_level.get("price")
        qty_obj = raw_level.get("qty")
        if not isinstance(price_obj, (str, int, float)):
            continue
        if not isinstance(qty_obj, (str, int, float)):
            continue

        try:
            levels.append((float(price_obj), float(qty_obj)))
        except (TypeError, ValueError):
            continue

    return levels


def extract_kraken_order_book_event(message: str | bytes) -> dict[str, object] | None:
    payload = decode_json_message(message)
    if payload is None:
        return None

    if payload.get("channel") != "book":
        return None

    message_type = payload.get("type")
    if message_type not in {"snapshot", "update"}:
        return None

    raw_data = payload.get("data")
    if not isinstance(raw_data, list) or not raw_data:
        return None

    data_entries = cast(list[object], raw_data)
    data_entry_obj = data_entries[0]
    if not isinstance(data_entry_obj, dict):
        return None
    data_entry = cast(dict[str, object], data_entry_obj)

    product_id = data_entry.get("symbol")
    if not isinstance(product_id, str):
        return None
    symbol = KRAKEN_PRODUCTS.get(product_id)
    if symbol is None:
        return None

    bids = parse_kraken_levels(data_entry.get("bids", []))
    asks = parse_kraken_levels(data_entry.get("asks", []))
    return {"type": cast(str, message_type), "symbol": symbol, "bids": bids, "asks": asks}


def extract_bybit_order_book_event(message: str | bytes) -> dict[str, object] | None:
    payload = decode_json_message(message)
    if payload is None:
        return None

    topic_obj = payload.get("topic")
    message_type = payload.get("type")
    if not isinstance(topic_obj, str):
        return None
    if message_type not in {"snapshot", "delta"}:
        return None

    symbol = BYBIT_TOPICS.get(topic_obj)
    if symbol is None:
        return None

    raw_data = payload.get("data")
    if not isinstance(raw_data, dict):
        return None
    data = cast(dict[str, object], raw_data)
    bids = parse_price_size_levels(data.get("b", []))
    asks = parse_price_size_levels(data.get("a", []))
    return {"type": cast(str, message_type), "symbol": symbol, "bids": bids, "asks": asks}


def apply_latest_quotes(sim: SwarmSimulation, latest_quotes: Mapping[str, Quote]) -> None:
    solusdt_bid, solusdt_ask = latest_quotes["SOLUSDT"]
    update_pool_from_binance(sim.pools[0], solusdt_bid, solusdt_ask)

    btcusdt_bid, btcusdt_ask = latest_quotes["BTCUSDT"]
    update_pool_from_binance(sim.pools[1], 1.0 / btcusdt_ask, 1.0 / btcusdt_bid)

    solbtc_bid, solbtc_ask = latest_quotes["SOLBTC"]
    update_pool_from_binance(sim.pools[2], solbtc_bid, solbtc_ask)


def process_quote(
    sim: SwarmSimulation,
    latest_quotes: dict[str, Quote],
    current_round: int,
    provider_name: str,
    symbol: str,
    bid_price: float,
    ask_price: float,
    recorder: TickRecorder | None = None,
    liquidity_tracker: LiquidityTracker | None = None,
    order_books: OrderBookTracker | None = None,
    truth_by_round: Mapping[int, TruthQualifier] | None = None,
) -> int:
    if symbol not in REQUIRED_SYMBOLS:
        return current_round

    if recorder is not None:
        recorder.record(provider_name, symbol, bid_price, ask_price)

    latest_quotes[symbol] = (bid_price, ask_price)
    if not REQUIRED_SYMBOLS.issubset(latest_quotes):
        return current_round

    liquidity_snapshot: LiquiditySnapshot | None = None
    truth_snapshot: TruthQualifierSnapshot | None = None
    if order_books is not None:
        consensus_provider_name = order_books.consensus_provider_name()
        liquidity_snapshot = build_liquidity_snapshot(
            current_round,
            consensus_provider_name,
            latest_quotes,
            order_books,
        )
        truth_snapshot = build_truth_qualifier_snapshot(
            current_round,
            consensus_provider_name,
            latest_quotes,
            order_books,
            liquidity_snapshot,
        )
        sim.set_market_truth(truth_snapshot.to_sim_truth_qualifier())
    elif truth_by_round is not None:
        sim.set_market_truth(truth_by_round.get(current_round, TruthQualifier()))

    apply_latest_quotes(sim, latest_quotes)
    sim.run_round(current_round)

    if (
        liquidity_tracker is not None
        and order_books is not None
        and liquidity_snapshot is not None
        and truth_snapshot is not None
    ):
        liquidity_tracker.record_snapshot(
            liquidity_snapshot,
            truth_snapshot,
            order_books.snapshot_record(current_round, provider_name),
            recorder,
        )

    if current_round == 0 or (current_round + 1) % 10 == 0:
        print(
            f"[{time.strftime('%H:%M:%S')}] "
            f"Round {current_round + 1:03d} | "
            f"Source {provider_name} | "
            f"Tick {symbol} | Swarm processed."
        )

    return current_round + 1


async def consume_binance_stream(
    event_queue: asyncio.Queue[dict[str, object]],
    stop_event: asyncio.Event,
) -> None:
    url = f"{BINANCE_WS_URL}?streams={'/'.join(BINANCE_STREAMS)}"
    print("Connecting to Binance public stream...")

    async with connect(url, ping_interval=20, ping_timeout=20) as websocket:
        await event_queue.put(
            {"type": "provider_status", "provider": "binance", "status": "connected"}
        )
        while not stop_event.is_set():
            message = await websocket.recv()
            depth_update = extract_binance_order_book(message)
            if depth_update is None:
                continue

            symbol, bids, asks = depth_update
            await event_queue.put(
                {
                    "type": "book",
                    "provider": "binance",
                    "symbol": symbol,
                    "event": "snapshot",
                    "bids": bids,
                    "asks": asks,
                }
            )


async def consume_kraken_stream(
    event_queue: asyncio.Queue[dict[str, object]],
    stop_event: asyncio.Event,
) -> None:
    print("Connecting to Kraken public book stream...")

    async with connect(KRAKEN_WS_URL, ping_interval=20, ping_timeout=20) as websocket:
        await websocket.send(
            json.dumps(
                {
                    "method": "subscribe",
                    "params": {
                        "channel": "book",
                        "symbol": list(KRAKEN_PRODUCTS),
                        "depth": ORDER_BOOK_LEVEL_LIMIT,
                    },
                }
            )
        )
        await event_queue.put(
            {"type": "provider_status", "provider": "kraken", "status": "connected"}
        )

        while not stop_event.is_set():
            message = await websocket.recv()
            event = extract_kraken_order_book_event(message)
            if event is None:
                continue

            symbol = cast(str, event["symbol"])
            event_type = cast(str, event["type"])
            await event_queue.put(
                {
                    "type": "book",
                    "provider": "kraken",
                    "symbol": symbol,
                    "event": event_type,
                    "bids": cast(list[BookLevel], event["bids"]),
                    "asks": cast(list[BookLevel], event["asks"]),
                }
            )


async def consume_bybit_stream(
    event_queue: asyncio.Queue[dict[str, object]],
    stop_event: asyncio.Event,
) -> None:
    print("Connecting to Bybit public order-book stream...")

    async with connect(BYBIT_WS_URL, ping_interval=20, ping_timeout=20) as websocket:
        await websocket.send(
            json.dumps({"op": "subscribe", "args": list(BYBIT_TOPICS)})
        )
        await event_queue.put(
            {"type": "provider_status", "provider": "bybit", "status": "connected"}
        )

        while not stop_event.is_set():
            message = await websocket.recv()
            event = extract_bybit_order_book_event(message)
            if event is None:
                continue

            symbol = cast(str, event["symbol"])
            event_type = cast(str, event["type"])
            await event_queue.put(
                {
                    "type": "book",
                    "provider": "bybit",
                    "symbol": symbol,
                    "event": event_type,
                    "bids": cast(list[BookLevel], event["bids"]),
                    "asks": cast(list[BookLevel], event["asks"]),
                }
            )


def provider_failure_is_hard(exc: Exception) -> bool:
    message = str(exc)
    lowered = message.lower()
    return any(status_code in message for status_code in ("401", "403", "451")) or any(
        token in lowered
        for token in (
            "unsupported 1inch spot-price chain",
            "must be an integer chain id",
            "is not set",
        )
    )


async def run_provider_stream(
    provider_name: str,
    consumer: Callable[[asyncio.Queue[dict[str, object]], asyncio.Event], Awaitable[None]],
    event_queue: asyncio.Queue[dict[str, object]],
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        try:
            await consumer(event_queue, stop_event)
        except (ConnectionClosed, InvalidStatus, OSError, TimeoutError, RuntimeError) as exc:
            await event_queue.put(
                {
                    "type": "provider_status",
                    "provider": provider_name,
                    "status": "unavailable",
                    "error": str(exc),
                }
            )
            if provider_failure_is_hard(exc) or stop_event.is_set():
                return
            await asyncio.sleep(1.0)
        else:
            if not stop_event.is_set():
                await event_queue.put(
                    {
                        "type": "provider_status",
                        "provider": provider_name,
                        "status": "disconnected",
                        "error": "stream ended",
                    }
                )
            return


def build_live_payment_gate_observation(
    current_round: int,
    liquidity_tracker: LiquidityTracker,
    order_books: OrderBookTracker,
    provider_failures: tuple[str, ...],
    provider_candidate_count: int,
) -> PaymentGateObservation:
    best_snapshot = liquidity_tracker.best
    final_truth = liquidity_tracker.final_truth
    return PaymentGateObservation(
        observed_rounds=current_round,
        active_public_providers=len(order_books.active_order_book_providers()),
        provider_candidate_count=provider_candidate_count,
        best_liquidity_score=0.0 if best_snapshot is None else best_snapshot.liquidity_score,
        best_executable_notional_usd_50bps=(
            0.0
            if best_snapshot is None
            else best_snapshot.executable_notional_usd_50bps
        ),
        final_truth_confidence=(0.0 if final_truth is None else final_truth.truth_confidence),
        failure_count=len(provider_failures),
        failures=provider_failures,
    )


async def stream_live_market_data(
    rounds: int,
    record_path: Path,
    swarm_state_path: Path | None,
) -> None:
    """
    Plugs live market data into the MEV Swarm Simulation.
    Each incoming tick triggers a round of swarm competition over the new state.
    """
    simulation_seed = random.SystemRandom().getrandbits(64)
    sim = build_simulation(rounds, simulation_seed)
    swarm_state_context = load_swarm_state(swarm_state_path, sim)
    print("Swarm Initialized. Waiting for live market ticks...")
    print(f"Persisting ticks to {record_path}")
    print(f"Simulation seed: {simulation_seed}")
    if swarm_state_path is not None:
        if cast(bool, swarm_state_context["loaded"]):
            print(
                "Hydrated swarm state from "
                f"{swarm_state_context['path']} "
                f"(generation {cast(int, swarm_state_context['generation'])}, "
                f"source session {swarm_state_context['source_session_id'] or 'unknown'})"
            )
        else:
            print(
                f"No persisted swarm state found at {swarm_state_context['path']}; starting cold."
            )
    print(
        "Warming up venue fan-in before round 1 to let multiple public providers populate the surface..."
    )

    current_round = 0
    latest_quotes: dict[str, Quote] = {}
    provider_specs = (
        ("binance", consume_binance_stream),
        ("kraken", consume_kraken_stream),
        ("bybit", consume_bybit_stream),
    )
    wire_placement = PaidLiquidityWirePlacement()
    liquidity_tracker = LiquidityTracker()
    order_books = OrderBookTracker()
    meta_quote_stop = asyncio.Event()
    venue_stop = asyncio.Event()
    venue_event_queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()
    recorder = TickRecorder(
        record_path,
        rounds,
        session_metadata={
            "simulation_seed": simulation_seed,
            "paid_liquidity_wire_reserved": True,
            "paid_liquidity_wire_note": wire_placement.note,
            "payment_gate_policy": wire_placement.policy.policy_name,
            "premium_adapter_provider": "1inch_product_api",
            "premium_adapter_enabled": wire_placement.enabled,
            "premium_adapter_api_key_env_var": wire_placement.product_api_adapter.api_key_env_var,
            "premium_adapter_probe_path": wire_placement.product_api_adapter.probe_path or None,
            "premium_quote_provider": ONEINCH_SPOT_PRICE_PROVIDER,
            "liquidity_probe_model": "weighted_order_book_depth_bands_10_25_50bps",
            "order_book_level_limit": ORDER_BOOK_LEVEL_LIMIT,
            "order_book_provider_candidates": ["binance", "kraken", "bybit"],
            "public_provider_target_count": PUBLIC_PROVIDER_TARGET_COUNT,
            "meta_quote_providers": ["coingecko", "dexscreener"],
            "macro_context_providers": [
                "yahoo_chart",
                "google_news_rss",
                "manifold",
                "polymarket",
                "defillama",
            ],
            "macro_context_watchlist": sorted(GOOGLE_NEWS_WATCHLIST),
            "defillama_protocol_watchlist": list(DEFILLAMA_PROTOCOL_KEYWORDS),
            "defillama_chain_watchlist": list(DEFILLAMA_CHAIN_WATCHLIST),
            "defillama_stablecoin_watchlist": list(DEFILLAMA_STABLECOIN_WATCHLIST),
            "swarm_state_file": cast(str | None, swarm_state_context["path"]),
            "swarm_state_enabled": cast(bool, swarm_state_context["enabled"]),
            "swarm_state_loaded": cast(bool, swarm_state_context["loaded"]),
            "swarm_state_generation_in": cast(int, swarm_state_context["generation"]),
            "swarm_state_parent_session_id": cast(
                str | None, swarm_state_context["source_session_id"]
            ),
            "swarm_state_rounds_completed_in": cast(
                int, swarm_state_context["rounds_completed"]
            ),
            "swarm_state_digest_in": cast(str | None, swarm_state_context["state_digest"]),
            "swarm_state_learning_summary_in": cast(
                dict[str, object], swarm_state_context["learning_summary"]
            ),
        },
    )
    if swarm_state_path is not None:
        recorder.record_event(
            {
                "type": "swarm_state_status",
                "phase": "loaded" if cast(bool, swarm_state_context["loaded"]) else "cold_start",
                "path": cast(str | None, swarm_state_context["path"]),
                "generation": cast(int, swarm_state_context["generation"]),
                "source_session_id": cast(
                    str | None, swarm_state_context["source_session_id"]
                ),
                "rounds_completed": cast(int, swarm_state_context["rounds_completed"]),
                "state_digest": cast(str | None, swarm_state_context["state_digest"]),
                "restore_summary": cast(
                    dict[str, object] | None, swarm_state_context["restore_summary"]
                ),
                "learning_summary": cast(
                    dict[str, object], swarm_state_context["learning_summary"]
                ),
            }
        )
    meta_quote_task = asyncio.create_task(poll_meta_quote_sources(order_books, recorder, meta_quote_stop))
    macro_context_stop = asyncio.Event()
    try:
        initial_macro_context = await asyncio.to_thread(build_macro_context_snapshot)
    except (OSError, TimeoutError, ValueError, ET.ParseError) as exc:
        print(f"initial macro context poll failed: {exc}")
    else:
        order_books.set_macro_context(initial_macro_context)
        recorder.record_event(initial_macro_context.to_record())
    macro_context_task = asyncio.create_task(
        poll_macro_context_sources(order_books, recorder, macro_context_stop)
    )
    public_provider_tasks = [
        asyncio.create_task(
            run_provider_stream(provider_name, consumer, venue_event_queue, venue_stop)
        )
        for provider_name, consumer in provider_specs
    ]
    provider_tasks = list(public_provider_tasks)
    provider_failures: dict[str, str] = {}
    premium_provider_requested = False
    next_gate_evaluation_round = wire_placement.policy.min_observed_rounds
    warmup_deadline = time.monotonic() + VENUE_FANIN_WARMUP_S
    liquidity_summary: dict[str, object] | None = None

    try:
        while current_round < sim.num_rounds:
            try:
                event = await asyncio.wait_for(venue_event_queue.get(), timeout=1.0)
            except TimeoutError as exc:
                if not order_books.active_order_book_providers() and all(
                    task.done() for task in public_provider_tasks
                ):
                    raise RuntimeError(
                        "No public market data providers are reachable from this environment."
                    ) from exc
                continue

            event_type_obj = event.get("type")
            if event_type_obj == "provider_status":
                provider_name_obj = event.get("provider")
                status_obj = event.get("status")
                error_obj = event.get("error")
                if not isinstance(provider_name_obj, str):
                    continue
                if not isinstance(status_obj, str):
                    continue

                error_message = error_obj if isinstance(error_obj, str) else None
                order_books.set_provider_status(provider_name_obj, status_obj, error_message)
                if status_obj == "connected":
                    provider_failures.pop(provider_name_obj, None)
                elif error_message is not None:
                    failure_record = f"{provider_name_obj}: {error_message}"
                    provider_failures[provider_name_obj] = failure_record
                    print(f"{provider_name_obj} unavailable: {error_message}")
                continue

            if event_type_obj == "quote":
                provider_name_obj = event.get("provider")
                quotes_obj = event.get("quotes")
                if not isinstance(provider_name_obj, str):
                    continue
                if not isinstance(quotes_obj, dict):
                    continue

                parsed_quotes: dict[str, Quote] = {}
                for symbol_obj, quote_obj in cast(dict[object, object], quotes_obj).items():
                    if not isinstance(symbol_obj, str):
                        continue
                    if not isinstance(quote_obj, (tuple, list)):
                        continue
                    quote_sequence = cast(tuple[object, ...] | list[object], quote_obj)
                    quote_pair = list(quote_sequence)
                    if len(quote_pair) != 2:
                        continue
                    bid_obj = quote_pair[0]
                    ask_obj = quote_pair[1]
                    if not isinstance(bid_obj, (int, float)):
                        continue
                    if not isinstance(ask_obj, (int, float)):
                        continue
                    parsed_quotes[symbol_obj] = (float(bid_obj), float(ask_obj))

                if not parsed_quotes:
                    continue

                order_books.set_quote_snapshot(provider_name_obj, parsed_quotes)
                latest_quotes.clear()
                latest_quotes.update(order_books.top_quotes())
                recorder.record_event(
                    {
                        "type": "provider_quote_snapshot",
                        "provider": provider_name_obj,
                        "captured_at": utc_now_iso(),
                        "quotes": {
                            symbol: {"bid": quote[0], "ask": quote[1]}
                            for symbol, quote in parsed_quotes.items()
                        },
                    }
                )
                continue

            if event_type_obj != "book":
                continue

            provider_name_obj = event.get("provider")
            symbol_obj = event.get("symbol")
            book_event_type_obj = event.get("event")
            bids_obj = event.get("bids")
            asks_obj = event.get("asks")
            if not isinstance(provider_name_obj, str):
                continue
            if not isinstance(symbol_obj, str):
                continue
            if not isinstance(book_event_type_obj, str):
                continue
            if not isinstance(bids_obj, list):
                continue
            if not isinstance(asks_obj, list):
                continue

            provider_name = provider_name_obj
            symbol = symbol_obj
            bids = cast(list[BookLevel], bids_obj)
            asks = cast(list[BookLevel], asks_obj)
            if book_event_type_obj == "snapshot":
                order_books.set_snapshot(provider_name, symbol, bids, asks)
            else:
                for price, size in bids:
                    order_books.apply_update(provider_name, symbol, "buy", price, size)
                for price, size in asks:
                    order_books.apply_update(provider_name, symbol, "sell", price, size)

            latest_quotes.clear()
            latest_quotes.update(order_books.top_quotes())

            top_quote = latest_quotes.get(symbol)
            if top_quote is None:
                continue

            if (
                current_round == 0
                and time.monotonic() < warmup_deadline
                and len(order_books.active_order_book_providers()) < PUBLIC_PROVIDER_TARGET_COUNT
            ):
                continue

            bid_price, ask_price = top_quote
            current_round = process_quote(
                sim,
                latest_quotes,
                current_round,
                provider_name,
                symbol,
                bid_price,
                ask_price,
                recorder,
                liquidity_tracker,
                order_books,
            )

            if (
                not premium_provider_requested
                and current_round >= next_gate_evaluation_round
            ):
                premium_provider_task = await maybe_start_premium_quote_provider(
                    current_round,
                    liquidity_tracker,
                    order_books,
                    provider_failures,
                    len(provider_specs),
                    wire_placement,
                    recorder,
                    venue_event_queue,
                    venue_stop,
                )
                next_gate_evaluation_round += 10
                if premium_provider_task is not None:
                    provider_tasks.append(premium_provider_task)
                    premium_provider_requested = True

        liquidity_summary = liquidity_tracker.summary_record()
        if liquidity_summary is not None:
            recorder.record_event(liquidity_summary)

        # Print the final stats after the live session completes.
        sim.print_final_stats()
        print_liquidity_summary(liquidity_tracker)
    finally:
        meta_quote_stop.set()
        macro_context_stop.set()
        venue_stop.set()
        meta_quote_task.cancel()
        macro_context_task.cancel()
        for task in provider_tasks:
            task.cancel()
        try:
            await meta_quote_task
        except asyncio.CancelledError:
            pass
        try:
            await macro_context_task
        except asyncio.CancelledError:
            pass
        for task in provider_tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        if swarm_state_path is not None:
            try:
                swarm_state_record = save_swarm_state(
                    swarm_state_path,
                    sim,
                    record_path.stem,
                    cast(int, swarm_state_context["generation"]),
                    liquidity_summary,
                    "live",
                )
            except (OSError, ValueError, TypeError) as exc:
                print(f"swarm state save failed: {exc}")
            else:
                recorder.record_event(swarm_state_record)
        recorder.close()


async def replay_market_data(
    replay_path: Path,
    rounds: int | None,
    replay_delay_ms: float,
    swarm_state_path: Path | None,
) -> None:
    metadata = read_replay_metadata(replay_path)
    metadata_rounds = metadata.get("target_rounds")
    default_rounds = metadata_rounds if isinstance(metadata_rounds, int) else DEFAULT_ROUNDS

    simulation_seed_obj = metadata.get("simulation_seed")
    if isinstance(simulation_seed_obj, int):
        simulation_seed = simulation_seed_obj
    else:
        simulation_seed = DEFAULT_SIMULATION_SEED
        print(
            "Replay file is missing simulation_seed metadata; "
            "using deterministic default seed 0."
        )

    sim = build_simulation(resolve_rounds(rounds, default_rounds), simulation_seed)
    swarm_state_context = load_swarm_state(swarm_state_path, sim)
    print(f"Replaying ticks from {replay_path}")
    print(f"Simulation seed: {simulation_seed}")
    if swarm_state_path is not None:
        if cast(bool, swarm_state_context["loaded"]):
            print(
                "Hydrated swarm state from "
                f"{swarm_state_context['path']} "
                f"(generation {cast(int, swarm_state_context['generation'])}, "
                f"source session {swarm_state_context['source_session_id'] or 'unknown'})"
            )
        else:
            print(
                f"No persisted swarm state found at {swarm_state_context['path']}; starting cold."
            )

    session_id = metadata.get("session_id")
    if isinstance(session_id, str):
        print(f"Session ID: {session_id}")

    current_round = 0
    latest_quotes: dict[str, Quote] = {}
    liquidity_tracker = LiquidityTracker()
    replay_delay_s = replay_delay_ms / 1000.0
    truth_by_round = read_recorded_truth_qualifiers(replay_path)

    for provider_name, symbol, bid_price, ask_price in iter_replay_ticks(replay_path):
        current_round = process_quote(
            sim,
            latest_quotes,
            current_round,
            provider_name,
            symbol,
            bid_price,
            ask_price,
            liquidity_tracker=liquidity_tracker,
            truth_by_round=truth_by_round,
        )

        if current_round >= sim.num_rounds:
            break
        if replay_delay_s > 0.0:
            await asyncio.sleep(replay_delay_s)

    if current_round < sim.num_rounds:
        print(f"Replay exhausted after {current_round} rounds (target was {sim.num_rounds}).")

    sim.print_final_stats()
    replay_metadata, replay_summary = read_recorded_liquidity_summary(replay_path)
    _ = replay_metadata
    if swarm_state_path is not None:
        replay_session_id = (
            f"replay_{session_id}" if isinstance(session_id, str) else f"replay_{replay_path.stem}"
        )
        try:
            swarm_state_record = save_swarm_state(
                swarm_state_path,
                sim,
                replay_session_id,
                cast(int, swarm_state_context["generation"]),
                replay_summary,
                "replay",
            )
        except (OSError, ValueError, TypeError) as exc:
            print(f"swarm state save failed: {exc}")
        else:
            print(
                "Saved replay-updated swarm state to "
                f"{swarm_state_record['path']} "
                f"(generation {swarm_state_record['generation']})"
            )
    print_liquidity_summary_record(replay_summary)


def compare_recorded_sessions(baseline_path: Path, candidate_path: Path) -> None:
    baseline_metadata, baseline_summary = read_recorded_liquidity_summary(baseline_path)
    candidate_metadata, candidate_summary = read_recorded_liquidity_summary(candidate_path)
    print_session_comparison(
        baseline_path,
        baseline_metadata,
        baseline_summary,
        candidate_path,
        candidate_metadata,
        candidate_summary,
    )


def build_recorded_payment_gate_observation(session_path: Path) -> PaymentGateObservation:
    metadata, summary = read_recorded_liquidity_summary(session_path)
    best = cast(dict[str, object], summary["best"])
    final = cast(dict[str, object], summary["final"])
    final_truth = cast(dict[str, object] | None, summary.get("final_truth"))

    final_round_obj = final.get("round")
    observed_rounds = final_round_obj + 1 if isinstance(final_round_obj, int) else 0

    provider_candidates_obj = metadata.get("order_book_provider_candidates", [])
    provider_candidate_count = (
        len(cast(list[object], provider_candidates_obj))
        if isinstance(provider_candidates_obj, list)
        else 0
    )

    max_active_public_providers = 0
    provider_status: dict[str, tuple[str, str | None]] = {}
    for payload in iter_session_records(session_path):
        if payload.get("type") != "market_surface_snapshot":
            continue

        active_providers_obj = payload.get("active_order_book_providers", [])
        if isinstance(active_providers_obj, list):
            max_active_public_providers = max(
                max_active_public_providers,
                len(cast(list[object], active_providers_obj)),
            )

        provider_status_obj = payload.get("provider_status", {})
        if not isinstance(provider_status_obj, dict):
            continue
        for provider_name_obj, details_obj in cast(
            dict[object, object], provider_status_obj
        ).items():
            if not isinstance(provider_name_obj, str):
                continue
            if not isinstance(details_obj, dict):
                continue
            details = cast(dict[str, object], details_obj)
            status_obj = details.get("status")
            error_obj = details.get("error")
            provider_status[provider_name_obj] = (
                status_obj if isinstance(status_obj, str) else "unknown",
                error_obj if isinstance(error_obj, str) else None,
            )

    failures = tuple(
        sorted(
            f"{provider_name}: {error_message}"
            for provider_name, (status, error_message) in provider_status.items()
            if status != "connected" and error_message is not None
        )
    )

    return PaymentGateObservation(
        observed_rounds=observed_rounds,
        active_public_providers=max_active_public_providers,
        provider_candidate_count=provider_candidate_count,
        best_liquidity_score=float(cast(float, best.get("liquidity_score", 0.0))),
        best_executable_notional_usd_50bps=float(
            cast(float, best.get("executable_notional_usd_50bps", 0.0))
        ),
        final_truth_confidence=(
            0.0 if final_truth is None else float(cast(float, final_truth.get("truth_confidence", 0.0)))
        ),
        failure_count=len(failures),
        failures=failures,
    )


def evaluate_payment_gate_for_session(session_path: Path) -> None:
    observation = build_recorded_payment_gate_observation(session_path)
    wire_placement = PaidLiquidityWirePlacement()
    decision = wire_placement.policy.evaluate(observation)

    print("\n" + "=" * 80)
    print("PAYMENT GATE POLICY")
    print("=" * 80)
    print(f"Session: {session_path}")
    print(f"Policy : {decision.policy_name}")
    print(
        f"Observed rounds={observation.observed_rounds} | "
        f"Active public providers={observation.active_public_providers}/{observation.provider_candidate_count}"
    )
    print(
        f"Best liquidity score={observation.best_liquidity_score:,.2f} | "
        f"Best exec@50bps=${observation.best_executable_notional_usd_50bps:,.2f} | "
        f"Final truth={observation.final_truth_confidence:.4f}"
    )
    print(
        f"Measured shortfall={decision.measured_shortfall} | "
        f"Shortfall score={decision.shortfall_score:.4f} | "
        f"Allow premium activation={decision.allow_activation}"
    )
    print(
        f"1inch adapter configured={wire_placement.product_api_adapter.configured()} | "
        f"Wire enabled={wire_placement.enabled} | "
        f"Probe path={wire_placement.product_api_adapter.probe_path or 'unset'}"
    )
    if decision.reasons:
        print("Reasons:")
        for reason in decision.reasons:
            print(f"- {reason}")
    if observation.failures:
        print("Provider failures:")
        for failure in observation.failures:
            print(f"- {failure}")


def analyze_recorded_coincidences(session_path: Path, limit: int) -> None:
    metadata = read_replay_metadata(session_path)
    rounds: dict[int, dict[str, object]] = {}
    best_liquidity_score = 0.0

    for payload in iter_session_records(session_path):
        record_type = payload.get("type")
        round_obj = payload.get("round")
        if not isinstance(round_obj, int):
            continue

        round_bucket = rounds.setdefault(round_obj, {})
        if record_type == "liquidity_snapshot":
            round_bucket["liquidity"] = payload
            liquidity_score_obj = payload.get("liquidity_score")
            if isinstance(liquidity_score_obj, (int, float)):
                best_liquidity_score = max(best_liquidity_score, float(liquidity_score_obj))
        elif record_type == "truth_qualifier_snapshot":
            round_bucket["truth"] = payload
        elif record_type == "market_surface_snapshot":
            round_bucket["surface"] = payload

    if not rounds:
        print(f"No round snapshots found in {session_path}.")
        return

    scored_rounds: list[dict[str, object]] = []
    for round_index, round_bucket in rounds.items():
        liquidity_obj = round_bucket.get("liquidity")
        truth_obj = round_bucket.get("truth")
        surface_obj = round_bucket.get("surface")
        if not isinstance(liquidity_obj, dict) or not isinstance(truth_obj, dict):
            continue

        liquidity = cast(dict[str, object], liquidity_obj)
        truth = cast(dict[str, object], truth_obj)
        macro_context_obj = (
            cast(dict[str, object], surface_obj).get("macro_context")
            if isinstance(surface_obj, dict)
            else None
        )
        macro_context = (
            cast(dict[str, object], macro_context_obj) if isinstance(macro_context_obj, dict) else {}
        )

        liquidity_score = float(cast(float, liquidity.get("liquidity_score", 0.0)))
        liquidity_strength = (
            clamp_unit(liquidity_score / best_liquidity_score) if best_liquidity_score > 0.0 else 0.0
        )
        truth_confidence = float(cast(float, truth.get("truth_confidence", 0.0)))
        macro_alignment = float(
            cast(float, macro_context.get("macro_alignment", truth.get("macro_alignment", 0.0)))
        )
        cross_asset_stress = float(
            cast(
                float,
                macro_context.get("cross_asset_stress", truth.get("cross_asset_stress", 0.0)),
            )
        )
        commodity_shock_score = float(
            cast(
                float,
                macro_context.get(
                    "commodity_shock_score",
                    truth.get("commodity_shock_score", 0.0),
                ),
            )
        )
        betting_conviction = float(
            cast(
                float,
                macro_context.get("betting_conviction", truth.get("betting_conviction", 0.0)),
            )
        )
        news_shock_score = float(
            cast(float, macro_context.get("news_shock_score", truth.get("news_shock_score", 0.0)))
        )

        coincidence_score = clamp_unit(
            0.35 * truth_confidence
            + 0.20 * liquidity_strength
            + 0.15 * macro_alignment
            + 0.10 * cross_asset_stress
            + 0.10 * commodity_shock_score
            + 0.05 * betting_conviction
            + 0.05 * news_shock_score
        )

        top_news_titles_obj = macro_context.get("top_news_titles", [])
        top_news_titles = (
            [str(title) for title in cast(list[object], top_news_titles_obj)[:2]]
            if isinstance(top_news_titles_obj, list)
            else []
        )

        scored_rounds.append(
            {
                "round": round_index,
                "provider": str(truth.get("provider", liquidity.get("provider", "unknown"))),
                "coincidence_score": coincidence_score,
                "liquidity_score": liquidity_score,
                "truth_confidence": truth_confidence,
                "avg_spread_bps": float(cast(float, liquidity.get("avg_spread_bps", 0.0))),
                "macro_alignment": macro_alignment,
                "cross_asset_stress": cross_asset_stress,
                "commodity_shock_score": commodity_shock_score,
                "betting_conviction": betting_conviction,
                "news_shock_score": news_shock_score,
                "top_news_titles": top_news_titles,
            }
        )

    if not scored_rounds:
        print(f"No coincidence-ready snapshots found in {session_path}.")
        return

    scored_rounds.sort(
        key=lambda row: cast(float, row["coincidence_score"]),
        reverse=True,
    )

    session_id = metadata.get("session_id")
    print("\n" + "=" * 80)
    print("COINCIDENCE ANALYSIS")
    print("=" * 80)
    print(f"Session: {session_path}")
    if isinstance(session_id, str):
        print(f"Session ID: {session_id}")
    print(f"Top coincident rounds: {min(limit, len(scored_rounds))}")

    for row in scored_rounds[:limit]:
        print(
            f"Round {cast(int, row['round']) + 1:03d} | "
            f"Source {cast(str, row['provider'])} | "
            f"Coincidence={cast(float, row['coincidence_score']):.4f} | "
            f"Truth={cast(float, row['truth_confidence']):.4f} | "
            f"Liquidity={cast(float, row['liquidity_score']):,.2f} | "
            f"Spread={cast(float, row['avg_spread_bps']):.4f}bps | "
            f"Macro={cast(float, row['macro_alignment']):.4f} | "
            f"CommodityShock={cast(float, row['commodity_shock_score']):.4f} | "
            f"Betting={cast(float, row['betting_conviction']):.4f} | "
            f"News={cast(float, row['news_shock_score']):.4f}"
        )
        top_news_titles = cast(list[str], row["top_news_titles"])
        if top_news_titles:
            print(f"          Headlines: {' | '.join(top_news_titles)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture and replay public market ticks for the MEV swarm simulation."
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Number of swarm rounds to execute. Defaults to 100 live rounds or the replay file target.",
    )
    parser.add_argument(
        "--record-file",
        type=Path,
        default=None,
        help="JSONL path for persisting live ticks. Defaults to a timestamped file under 5-Applications/out/live_market_data/.",
    )
    parser.add_argument(
        "--replay-file",
        type=Path,
        default=None,
        help="Replay a previously recorded JSONL tick session instead of connecting to live providers.",
    )
    parser.add_argument(
        "--replay-delay-ms",
        type=float,
        default=0.0,
        help="Optional delay between replayed ticks in milliseconds.",
    )
    parser.add_argument(
        "--compare-files",
        nargs=2,
        type=Path,
        default=None,
        metavar=("BASELINE", "CANDIDATE"),
        help="Compare two recorded session files and report whether liquidity improved.",
    )
    parser.add_argument(
        "--coincidence-file",
        type=Path,
        default=None,
        help="Inspect one recorded session and report the rounds where liquidity, truth, and macro signals coincided most strongly.",
    )
    parser.add_argument(
        "--coincidence-limit",
        type=int,
        default=5,
        help="Maximum number of coincident rounds to print with --coincidence-file.",
    )
    parser.add_argument(
        "--payment-gate-file",
        type=Path,
        default=None,
        help="Evaluate the premium-feed payment gate against one recorded session file.",
    )
    parser.add_argument(
        "--swarm-state-file",
        type=Path,
        default=None,
        help=(
            "JSON path for persisted swarm learning state. During live runs and replays, the file "
            "is loaded before round 1 when present and rewritten at shutdown with updated bot, "
            "pool, and cross-session objective state."
        ),
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if args.compare_files is not None:
        compare_recorded_sessions(args.compare_files[0], args.compare_files[1])
        return
    if args.coincidence_limit <= 0:
        raise ValueError("--coincidence-limit must be positive")
    if args.coincidence_file is not None:
        analyze_recorded_coincidences(args.coincidence_file, args.coincidence_limit)
        return
    if args.payment_gate_file is not None:
        evaluate_payment_gate_for_session(args.payment_gate_file)
        return

    if args.replay_file is not None and args.record_file is not None:
        raise ValueError("--record-file cannot be combined with --replay-file")
    if args.replay_delay_ms < 0.0:
        raise ValueError("--replay-delay-ms must be non-negative")

    if args.replay_file is not None:
        await replay_market_data(
            args.replay_file,
            args.rounds,
            args.replay_delay_ms,
            args.swarm_state_file,
        )
        return

    await stream_live_market_data(
        rounds=resolve_rounds(args.rounds, DEFAULT_ROUNDS),
        record_path=args.record_file or default_record_path(),
        swarm_state_path=args.swarm_state_file,
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested... exiting.")
