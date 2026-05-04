#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""NVIDIA SAE Feature Scraper.

Acquisition order (each tried in sequence, stops on first success):

  PATH A — Headless browser (Playwright):
    Launches a real Chromium headless instance, navigates to the dashboard,
    and intercepts every network response.  When the dashboard JS starts
    DuckDB-WASM it fetches features_atlas.parquet, feature_metadata.parquet,
    and feature_examples.parquet itself.  We capture those bytes directly from
    the browser's network stack — no manual cookie capture, no guessing URLs.
    Also sniffs any per-feature CSV download endpoint pattern for Path C.
    Requires:  pip install playwright && playwright install chromium

  PATH B — Direct HTTP parquet fetch (3 requests):
    If the parquet URL can be inferred from parquet_base_url in config,
    try a direct download with httpx.  PAR1 magic-byte validation rejects
    HTML auth walls immediately.

  PATH C — Per-feature CSV sweep (rate-limited, up to 32,634 requests):
    Last resort when both above fail or when targeting a sparse ID range.
    Human-pacing multi-modal jitter + periodic heartbeat visits.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import httpx
    from tqdm.asyncio import tqdm
except ImportError:
    print("[!] Missing dependencies: pip install httpx tqdm")
    sys.exit(1)

try:
    from playwright.async_api import async_playwright, Response as PwResponse
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

try:
    import duckdb as _duckdb
    _HAS_DUCKDB = True
except ImportError:
    _HAS_DUCKDB = False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("nvidia_sae")

_PARQUET_FILES = [
    "features_atlas.parquet",
    "feature_metadata.parquet",
    "feature_examples.parquet",
]

# ── SQLite schema (shared by all ingest paths) ───────────────────────────────
_SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous  = NORMAL;

CREATE TABLE IF NOT EXISTS features (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id            TEXT UNIQUE NOT NULL,
    label                 TEXT,
    description           TEXT,
    activation_freq       REAL,
    mean_activation       REAL,
    max_activation        REAL,
    std_activation        REAL,
    total_activations     INTEGER,
    log_frequency         REAL,
    x                     REAL,
    y                     REAL,
    cluster_id            INTEGER,
    high_score_fraction   REAL,
    clinvar_fraction      REAL,
    mean_phylop           REAL,
    mean_variant_delta    REAL,
    mean_site_delta       REAL,
    mean_local_delta      REAL,
    high_score_delta      REAL,
    low_score_delta       REAL,
    gc_mean               REAL,
    gc_std                REAL,
    trinuc_entropy        REAL,
    trinuc_dominant_frac  REAL,
    gene_entropy          REAL,
    gene_n_unique         INTEGER,
    gene_dominant_frac    REAL,
    mean_variant_1bcdwt   REAL,
    mean_variant_5bcdwt   REAL,
    mean_variant_5b       REAL,
    llm_confidence        REAL,
    imported_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS proteins (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_hash TEXT UNIQUE NOT NULL,
    sequence      TEXT NOT NULL,
    length        INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS activations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id       INTEGER NOT NULL REFERENCES features(id),
    protein_id       TEXT    NOT NULL REFERENCES proteins(sequence_hash),
    example_rank     INTEGER,
    alphafold_id     TEXT,
    max_activation   REAL,
    activations_json TEXT,
    gene             TEXT,
    is_pathogenic    INTEGER,
    ref_codon        TEXT,
    alt_codon        TEXT,
    source           TEXT,
    var_pos_offset   INTEGER,
    variant_delta    REAL,
    UNIQUE(feature_id, protein_id, example_rank)
);
CREATE INDEX IF NOT EXISTS idx_features_fid  ON features(feature_id);
CREATE INDEX IF NOT EXISTS idx_proteins_hash ON proteins(sequence_hash);
CREATE INDEX IF NOT EXISTS idx_act_fid       ON activations(feature_id);
"""


# ── Parquet → SQLite inversion ───────────────────────────────────────────────

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _open_sqlite(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn


def parquet_to_sqlite(parquet_dir: Path, db_path: Path) -> int:
    """Read the three parquet files and write to SQLite.  Returns feature count."""
    if not _HAS_DUCKDB:
        logger.error("[!] duckdb not installed: pip install duckdb")
        return 0

    atlas_f    = parquet_dir / "features_atlas.parquet"
    meta_f     = parquet_dir / "feature_metadata.parquet"
    examples_f = parquet_dir / "feature_examples.parquet"

    if not atlas_f.exists() or not meta_f.exists():
        logger.error("[!] Missing required parquet files in %s", parquet_dir)
        return 0

    duck = _duckdb.connect(":memory:")

    # Log discovered column names — parquet schema may change between releases
    for fpath in (atlas_f, meta_f, examples_f):
        if fpath.exists():
            cols = duck.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{fpath}') LIMIT 0"
            ).fetchall()
            logger.info("[parquet] %-32s columns: %s",
                        fpath.name, [c[0] for c in cols])

    def _rows(fpath: Path):
        desc = duck.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{fpath}') LIMIT 0"
        ).fetchall()
        col_names = [c[0].lower() for c in desc]
        rows = duck.execute(f"SELECT * FROM read_parquet('{fpath}')").fetchall()
        return col_names, rows

    def _get(row, cols, *names):
        for n in names:
            for i, c in enumerate(cols):
                if c == n.lower():
                    return row[i]
        return None

    def _f(v) -> Optional[float]:
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    def _i(v) -> Optional[int]:
        try:
            return int(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    conn = _open_sqlite(db_path)
    cur  = conn.cursor()
    inserted = 0

    # ── features_atlas: all 30 columns ───────────────────────────────────────
    atlas_cols, atlas_rows = _rows(atlas_f)
    for row in atlas_rows:
        g = lambda *ns: _get(row, atlas_cols, *ns)   # noqa: E731
        fid = str(g("feature_id") or "")
        if not fid:
            continue
        cur.execute(
            "INSERT OR IGNORE INTO features ("
            " feature_id, label,"
            " activation_freq, mean_activation, max_activation, std_activation,"
            " total_activations, log_frequency, x, y, cluster_id,"
            " high_score_fraction, clinvar_fraction, mean_phylop,"
            " mean_variant_delta, mean_site_delta, mean_local_delta,"
            " high_score_delta, low_score_delta,"
            " gc_mean, gc_std, trinuc_entropy, trinuc_dominant_frac,"
            " gene_entropy, gene_n_unique, gene_dominant_frac,"
            " mean_variant_1bcdwt, mean_variant_5bcdwt, mean_variant_5b,"
            " llm_confidence"
            ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                fid,
                str(g("label") or ""),
                _f(g("activation_freq")),
                _f(g("mean_activation")),
                _f(g("max_activation")),
                _f(g("std_activation")),
                _i(g("total_activations")),
                _f(g("log_frequency")),
                _f(g("x")),
                _f(g("y")),
                _i(g("cluster_id")),
                _f(g("high_score_fraction")),
                _f(g("clinvar_fraction")),
                _f(g("mean_phylop")),
                _f(g("mean_variant_delta")),
                _f(g("mean_site_delta")),
                _f(g("mean_local_delta")),
                _f(g("high_score_delta")),
                _f(g("low_score_delta")),
                _f(g("gc_mean")),
                _f(g("gc_std")),
                _f(g("trinuc_entropy")),
                _f(g("trinuc_dominant_frac")),
                _f(g("gene_entropy")),
                _i(g("gene_n_unique")),
                _f(g("gene_dominant_frac")),
                _f(g("mean_variant_1bcdwt")),
                _f(g("mean_variant_5bcdwt")),
                _f(g("mean_variant_5b")),
                _f(g("llm_confidence")),
            ),
        )
        inserted += 1
    conn.commit()
    logger.info("[parquet] %d features from atlas", inserted)

    # ── feature_metadata: merge description into features ────────────────────
    if meta_f.exists():
        meta_cols, meta_rows = _rows(meta_f)
        updated = 0
        for row in meta_rows:
            g = lambda *ns: _get(row, meta_cols, *ns)   # noqa: E731
            fid  = str(g("feature_id") or "")
            desc = str(g("description") or "")
            if fid and desc:
                cur.execute(
                    "UPDATE features SET description = ? WHERE feature_id = ? AND description IS NULL",
                    (desc, fid),
                )
                updated += cur.rowcount
        conn.commit()
        logger.info("[parquet] %d descriptions merged from metadata", updated)

    # ── feature_examples: proteins dedup + all 14 activation columns ─────────
    if examples_f.exists():
        import json as _json
        ex_cols, ex_rows = _rows(examples_f)
        seen_hashes: set = set()
        act_count = 0
        for row in ex_rows:
            g = lambda *ns: _get(row, ex_cols, *ns)   # noqa: E731
            fid  = str(g("feature_id") or "")
            seq  = str(g("sequence") or "")
            if not fid or not seq:
                continue

            seq_hash = _sha256(seq)
            if seq_hash not in seen_hashes:
                cur.execute(
                    "INSERT OR IGNORE INTO proteins (sequence_hash, sequence, length)"
                    " VALUES (?, ?, ?)",
                    (seq_hash, seq, len(seq)),
                )
                seen_hashes.add(seq_hash)

            feat_row = cur.execute(
                "SELECT id FROM features WHERE feature_id = ?", (fid,)
            ).fetchone()
            if not feat_row:
                continue

            raw_acts = g("activations")
            acts_json = (
                _json.dumps(list(raw_acts)) if raw_acts is not None else None
            )

            cur.execute(
                "INSERT OR IGNORE INTO activations ("
                " feature_id, protein_id, example_rank, alphafold_id,"
                " max_activation, activations_json, gene, is_pathogenic,"
                " ref_codon, alt_codon, source, var_pos_offset, variant_delta"
                ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    feat_row[0],
                    seq_hash,
                    _i(g("example_rank")),
                    str(g("alphafold_id") or "") or None,
                    _f(g("max_activation")),
                    acts_json,
                    str(g("gene") or "") or None,
                    _i(g("is_pathogenic")),
                    str(g("ref_codon") or "") or None,
                    str(g("alt_codon") or "") or None,
                    str(g("source") or "") or None,
                    _i(g("var_pos_offset")),
                    _f(g("variant_delta")),
                ),
            )
            act_count += 1

        conn.commit()
        logger.info("[parquet] %d activations from examples", act_count)
        logger.info("[parquet] %d unique protein sequences", len(seen_hashes))

    duck.close()
    conn.close()
    return inserted


# ── Main scraper ──────────────────────────────────────────────────────────────

class NvidiaSaeScraper:

    def __init__(self, config_file: Path):
        self.config             = self._load_config(config_file)
        self.output_dir         = Path(self.config["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore          = asyncio.Semaphore(self.config["concurrency_limit"])
        self.download_count     = 0
        self.heartbeat_interval = self.config.get("heartbeat_interval", 100)
        self.max_retries        = self.config.get("max_retries", 5)
        self.base_dashboard_url = self.config.get("base_dashboard_url", "")
        self.parquet_base_url   = self.config.get(
            "parquet_base_url", self.base_dashboard_url
        ).rstrip("/")
        self.db_path            = Path(self.config.get(
            "db_path", "tools/sae_extractor/sae_features.db"
        ))
        self.parquet_dir        = self.output_dir / "parquet"
        self.parquet_dir.mkdir(parents=True, exist_ok=True)

        # Sniffed CSV endpoint discovered by headless path
        self._sniffed_csv_url_template: Optional[str] = None

    def _load_config(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            logger.error("Config not found: %s", path)
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _headers(self, extra: Optional[Dict] = None) -> Dict:
        h = self.config.get("headers", {}).copy()
        if extra:
            h.update(extra)
        return h

    # ── PATH A: Headless Playwright ───────────────────────────────────────────

    async def _try_headless(self) -> bool:
        """Drive a real headless Chromium, intercept parquet responses in-flight.

        The browser executes the dashboard JS normally — DuckDB-WASM fires its
        own fetch() calls for the parquet files.  We register a response handler
        that captures bytes for any URL ending in .parquet.

        Side-effect: also records any per-feature CSV download URL pattern in
        self._sniffed_csv_url_template for Path C fallback.
        """
        if not _HAS_PLAYWRIGHT:
            logger.info(
                "[headless] playwright not installed — skipping. "
                "Run: pip install playwright && playwright install chromium"
            )
            return False

        dashboard_url = self.base_dashboard_url
        if not dashboard_url:
            logger.info("[headless] base_dashboard_url not configured — skipping")
            return False

        captured: Dict[str, bytes] = {}
        # Events signalled when each file arrives
        events: Dict[str, asyncio.Event] = {f: asyncio.Event() for f in _PARQUET_FILES}

        async def _on_response(resp: PwResponse) -> None:
            url = resp.url
            fname = url.split("?")[0].split("/")[-1]   # strip query params

            # Capture parquet files
            if fname in events and not events[fname].is_set():
                try:
                    body = await resp.body()
                    if body[:4] == b"PAR1":
                        captured[fname] = body
                        logger.info("[headless] captured %s (%d bytes)", fname, len(body))
                        events[fname].set()
                    else:
                        logger.warning(
                            "[headless] %s response not a parquet file (first bytes: %s)",
                            fname, body[:32],
                        )
                except Exception as e:
                    logger.warning("[headless] failed to read body of %s: %s", fname, e)

            # Sniff CSV download endpoint pattern
            if (
                "/csv" in url.lower() or url.endswith(".csv")
            ) and self._sniffed_csv_url_template is None:
                # Heuristic: replace any numeric feature-ID segment with {feature_id}
                import re
                template = re.sub(r"/(\d{1,6})(/|$)", r"/{feature_id}\2", url)
                if "{feature_id}" in template:
                    logger.info("[headless] sniffed CSV endpoint: %s", template)
                    self._sniffed_csv_url_template = template

        logger.info("[headless] launching Chromium → %s", dashboard_url)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            ctx = await browser.new_context(
                user_agent=self.config.get("headers", {}).get(
                    "User-Agent",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                    " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ),
                # Inject stored cookies if provided in config
                storage_state=self.config.get("playwright_storage_state") or None,
            )
            page = await ctx.new_page()
            page.on("response", _on_response)

            try:
                await page.goto(dashboard_url, wait_until="domcontentloaded", timeout=30_000)
                logger.info("[headless] DOM loaded, waiting for parquet fetches …")

                # Wait up to 90s for all three parquet files, 45s for at least two
                wait_tasks = [asyncio.create_task(e.wait()) for e in events.values()]
                done, pending = await asyncio.wait(
                    wait_tasks, timeout=90.0, return_when=asyncio.ALL_COMPLETED
                )

                for t in pending:
                    t.cancel()

            except Exception as e:
                logger.warning("[headless] page navigation error: %s", e)
            finally:
                await browser.close()

        if len(captured) < 2:
            logger.warning(
                "[headless] only captured %d/%d parquet files — insufficient",
                len(captured), len(_PARQUET_FILES),
            )
            return False

        # Persist captured bytes
        for fname, data in captured.items():
            dest = self.parquet_dir / fname
            dest.write_bytes(data)
            logger.info("[headless] saved %s → %s", fname, dest)

        logger.info("[headless] inverting to SQLite …")
        n = parquet_to_sqlite(self.parquet_dir, self.db_path)
        if n > 0:
            logger.info("[headless] ✓ %d features written to %s", n, self.db_path)
            return True

        logger.warning("[headless] inversion returned 0 features")
        return False

    # ── PATH B: Direct HTTP parquet ───────────────────────────────────────────

    async def _try_parquet_http(self, client: httpx.AsyncClient) -> bool:
        if not self.parquet_base_url:
            return False

        logger.info("[parquet-http] trying %s", self.parquet_base_url)
        fetched: List[Path] = []

        for fname in _PARQUET_FILES:
            dest = self.parquet_dir / fname
            if dest.exists() and dest.stat().st_size > 1024:
                logger.info("[parquet-http] cached: %s", fname)
                fetched.append(dest)
                continue

            url = f"{self.parquet_base_url}/{fname}"
            try:
                resp = await client.get(
                    url,
                    headers=self._headers({"Accept": "application/octet-stream"}),
                    follow_redirects=True,
                )
                if resp.status_code == 200:
                    body = resp.content
                    if not body[:4] == b"PAR1":
                        logger.warning("[parquet-http] %s: auth wall or wrong content", fname)
                        return False
                    dest.write_bytes(body)
                    logger.info("[parquet-http] saved %s (%d bytes)", fname, len(body))
                    fetched.append(dest)
                elif resp.status_code == 404:
                    logger.info("[parquet-http] %s → 404", fname)
                    return False
                else:
                    logger.warning("[parquet-http] %s HTTP %d", fname, resp.status_code)
                    return False
            except Exception as e:
                logger.warning("[parquet-http] %s fetch failed: %s", fname, e)
                return False

        if len(fetched) < 2:
            return False

        n = parquet_to_sqlite(self.parquet_dir, self.db_path)
        if n > 0:
            logger.info("[parquet-http] ✓ %d features → %s", n, self.db_path)
            return True
        return False

    # ── PATH C: Per-feature CSV sweep ─────────────────────────────────────────

    async def _human_like_delay(self):
        base = self.config["delay_seconds"]
        r    = random.random()
        if r < 0.80:
            t = base * random.uniform(0.7, 1.3)
        elif r < 0.95:
            t = base * random.uniform(2.0, 4.0)
            logger.info("[delay] reading pause (%.1fs)", t)
        else:
            t = base * random.uniform(10.0, 20.0)
            logger.info("[delay] long break (%.1fs)", t)
        await asyncio.sleep(t)

    async def _heartbeat(self, client: httpx.AsyncClient):
        logger.info("[heartbeat] visiting dashboard root …")
        try:
            h = self._headers()
            h.pop("Referer", None)
            await client.get(self.base_dashboard_url, headers=h, follow_redirects=True)
            await asyncio.sleep(random.uniform(2, 5))
        except Exception as e:
            logger.warning("[heartbeat] failed: %s", e)

    async def _download_csv(self, client: httpx.AsyncClient, feature_id: int) -> bool:
        target = self.output_dir / f"feature_{feature_id:05d}.csv"
        if target.exists() and target.stat().st_size > 100:
            return True

        # Prefer headless-sniffed URL, then config template
        url_tpl = (
            self._sniffed_csv_url_template
            or self.config.get("base_url_template", "")
        )
        if not url_tpl or "REPLACE_WITH" in url_tpl:
            return False

        url = url_tpl.format(feature_id=feature_id)

        async with self.semaphore:
            self.download_count += 1
            if self.download_count % self.heartbeat_interval == 0:
                await self._heartbeat(client)

            for attempt in range(self.max_retries):
                await self._human_like_delay()
                try:
                    resp = await client.get(
                        url,
                        headers=self._headers({"Referer": self.base_dashboard_url}),
                        follow_redirects=True,
                    )
                    if resp.status_code == 200:
                        body = resp.text
                        if "<html" in body[:512].lower():
                            logger.warning("[csv] feature %d: auth wall", feature_id)
                            return False
                        target.write_text(body, encoding="utf-8")
                        return True
                    elif resp.status_code == 404:
                        return False
                    elif resp.status_code == 429:
                        wait = (attempt + 1) * 60
                        logger.warning("[csv] 429 — waiting %ds", wait)
                        await asyncio.sleep(wait)
                    elif resp.status_code == 403:
                        logger.error("[csv] 403 at feature %d — session expired?", feature_id)
                        return False
                    else:
                        logger.warning("[csv] feature %d: HTTP %d (attempt %d)",
                                       feature_id, resp.status_code, attempt + 1)
                except Exception as e:
                    logger.error("[csv] feature %d attempt %d: %s",
                                 feature_id, attempt + 1, e)

        return False

    async def _run_csv_path(self, client: httpx.AsyncClient):
        f_range = self.config["feature_range"]
        ids = list(range(f_range[0], f_range[1] + 1))
        random.shuffle(ids)
        logger.info("[csv] sweeping %d IDs (%d–%d)", len(ids), f_range[0], f_range[1])
        tasks   = [self._download_csv(client, fid) for fid in ids]
        results = await tqdm.gather(*tasks, desc="CSV sweep")
        logger.info("[csv] done: %d/%d ok", sum(results), len(ids))

    # ── Entry point ───────────────────────────────────────────────────────────

    async def run(self):
        # Path A: headless browser — lets the JS do the work for us
        if await self._try_headless():
            return

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Path B: direct HTTP parquet
            if await self._try_parquet_http(client):
                return
            # Path C: per-feature CSV sweep (rate-limited fallback)
            logger.info("[*] falling back to per-feature CSV sweep")
            await self._run_csv_path(client)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NVIDIA SAE Feature Scraper")
    parser.add_argument("--config",          default="4-Infrastructure/config/nvidia_sae_config.json")
    parser.add_argument("--headless-only",   action="store_true",
                        help="Playwright path only — no fallback")
    parser.add_argument("--parquet-only",    action="store_true",
                        help="Direct HTTP parquet only — no fallback")
    parser.add_argument("--csv-only",        action="store_true",
                        help="Per-feature CSV sweep only")
    parser.add_argument("--convert-parquet", metavar="DIR",
                        help="Offline: convert already-cached parquet files in DIR to SQLite")
    args = parser.parse_args()

    cfg = Path(args.config)

    if args.convert_parquet:
        config  = json.loads(cfg.read_text()) if cfg.exists() else {}
        db_path = Path(config.get("db_path", "tools/sae_extractor/sae_features.db"))
        n = parquet_to_sqlite(Path(args.convert_parquet), db_path)
        logger.info("Converted %d features → %s", n, db_path)
        sys.exit(0)

    scraper = NvidiaSaeScraper(cfg)

    if args.headless_only:
        ok = asyncio.run(scraper._try_headless())
        sys.exit(0 if ok else 1)

    if args.parquet_only:
        async def _ph():
            async with httpx.AsyncClient(timeout=120.0) as c:
                return await scraper._try_parquet_http(c)
        ok = asyncio.run(_ph())
        sys.exit(0 if ok else 1)

    if args.csv_only:
        async def _csv():
            async with httpx.AsyncClient(timeout=120.0) as c:
                await scraper._run_csv_path(c)
        try:
            asyncio.run(_csv())
        except KeyboardInterrupt:
            logger.info("[!] interrupted — progress in %s", scraper.output_dir)
        sys.exit(0)

    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        logger.info("[!] interrupted — progress in %s", scraper.output_dir)
