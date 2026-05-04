# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, cast


SOURCE_ENDPOINTS: Dict[str, List[str]] = {
    "federalreserve": [
        "https://www.federalreserve.gov/feeds/press_all.xml",
    ],
    "ecb": [
        "https://www.ecb.europa.eu/rss/press.html",
        "https://www.ecb.europa.eu/rss/blog.html",
    ],
    "bankofengland": [
        "https://www.bankofengland.co.uk/rss/news",
    ],
    "sec": [
        "https://www.sec.gov/news/pressreleases.rss",
        "https://www.sec.gov/rss/news/press.xml",
        "https://www.sec.gov/news/press-release",
    ],
    "cftc": [
        "https://www.cftc.gov/PressRoom/PressReleases/rss",
        "https://www.cftc.gov/About/PressRoom/PressReleases/rss.xml",
        "https://www.cftc.gov/PressRoom/PressReleases",
    ],
}

HAWKISH_TERMS = {
    "hike",
    "tighten",
    "inflation",
    "enforcement",
    "sanction",
    "penalty",
    "restriction",
    "hawkish",
    "cease",
    "fraud",
    "charges",
    "lawsuit",
}

DOVISH_TERMS = {
    "cut",
    "easing",
    "stimulus",
    "support",
    "approval",
    "clarity",
    "framework",
    "guidance",
    "liquidity",
    "pause",
}


def http_get_text(url: str, timeout: float = 25.0) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "policy-event-collector/2.0 (+research stack)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html;q=0.8, */*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse_datetime(value: str) -> Optional[datetime]:
    s = value.strip()
    if not s:
        return None

    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def load_previous_reliability(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return cast(Dict[str, Any], payload) if isinstance(payload, dict) else {}


def ema_alpha_for_elapsed_hours(elapsed_hours: float, ema_days: float) -> float:
    # Daily EMA baseline alpha using span N: alpha = 2/(N+1), scaled for elapsed time.
    n = max(1.0, ema_days)
    alpha_day = 2.0 / (n + 1.0)
    days = max(0.0, elapsed_hours / 24.0)
    return 1.0 - ((1.0 - alpha_day) ** days)


def rolling_ema(new_value: float, prev_value: Optional[float], alpha: float) -> float:
    if prev_value is None:
        return new_value
    a = max(0.0, min(1.0, alpha))
    return (a * new_value) + ((1.0 - a) * prev_value)


def apply_relative_drift_cap(
    prev_value: Optional[float],
    proposed_value: float,
    elapsed_hours: float,
    max_drift_up_per_day: float,
    max_drift_down_per_day: float,
) -> Tuple[float, bool, float, float]:
    """Asymmetric relative drift cap.

    Returns (bounded_value, was_capped, applied_cap_up, applied_cap_down).
    Upward moves are capped by max_drift_up_per_day; downward moves by
    max_drift_down_per_day (both expressed as decimal fractions per day).
    """
    if prev_value is None or prev_value <= 0.0:
        return proposed_value, False, 0.0, 0.0

    elapsed_days = max(0.0, elapsed_hours / 24.0)
    cap_up = max(0.0, max_drift_up_per_day) * elapsed_days
    cap_down = max(0.0, max_drift_down_per_day) * elapsed_days

    lower = prev_value * (1.0 - cap_down) if cap_down > 0.0 else 0.0
    upper = prev_value * (1.0 + cap_up) if cap_up > 0.0 else float("inf")
    bounded = min(upper, max(lower, proposed_value))
    was_capped = bounded != proposed_value
    return bounded, was_capped, cap_up, cap_down


def infer_event_signal(title: str, summary: str) -> Tuple[str, float, float, List[str]]:
    text = f"{title} {summary}".lower()
    tokens = set(re.findall(r"[a-zA-Z]{3,}", text))

    hawk = sorted([t for t in tokens if t in HAWKISH_TERMS])
    dove = sorted([t for t in tokens if t in DOVISH_TERMS])

    if hawk and not dove:
        impact = min(1.0, 0.45 + (0.10 * len(hawk)))
        return "hawkish_or_enforcement", impact, min(1.0, 0.55 + 0.05 * len(hawk)), hawk

    if dove and not hawk:
        impact = -min(1.0, 0.40 + (0.10 * len(dove)))
        return "dovish_or_supportive", impact, min(1.0, 0.55 + 0.05 * len(dove)), dove

    overlap = sorted(set(hawk + dove))
    if overlap:
        return "mixed_policy_signal", 0.0, 0.45, overlap

    return "neutral_policy_signal", 0.0, 0.35, []


def text_or_none(node: Optional[ET.Element]) -> str:
    if node is None or node.text is None:
        return ""
    return clean_text(node.text)


def find_first_text(node: ET.Element, tags: Iterable[str]) -> str:
    for t in tags:
        child = node.find(t)
        txt = text_or_none(child)
        if txt:
            return txt
    return ""


def make_record(source: str, title: str, summary: str, link: str, dt: datetime, collector_url: str, parser: str) -> Dict[str, Any]:
    event_type, impact, confidence, keywords = infer_event_signal(title, summary)
    evid_input = f"{source}|{title}|{link}|{dt.isoformat()}"
    evidence_id = "EV-" + hashlib.sha256(evid_input.encode("utf-8")).hexdigest()[:16].upper()

    return {
        "version": "v1.0",
        "record_id": f"POLICY-{source}-{evidence_id}",
        "timestamp_utc": dt.replace(microsecond=0).isoformat(),
        "source": source,
        "title": title,
        "url": link,
        "event_type": event_type,
        "impact": round(impact, 8),
        "confidence": round(confidence, 8),
        "keywords": keywords,
        "evidence_id": evidence_id,
        "metadata": {
            "collector": "collect_policy_event_records.py",
            "feed_url": collector_url,
            "parser": parser,
        },
    }


def collect_from_xml(source: str, url: str, xml_text: str, cutoff: datetime, max_items: int) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_text)

    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{*}entry")

    out: List[Dict[str, Any]] = []
    for item in items[: max(1, max_items * 4)]:
        title = find_first_text(item, ["title", "{*}title"])
        summary = find_first_text(item, ["description", "summary", "{*}summary", "{*}content"])
        link = find_first_text(item, ["link", "{*}link"])

        if not link:
            link_elem = item.find("{*}link")
            if link_elem is not None:
                link = str(link_elem.attrib.get("href", "")).strip()

        pub = find_first_text(item, ["pubDate", "published", "updated", "{*}published", "{*}updated"])
        dt = parse_datetime(pub)
        if dt is None:
            continue
        if dt < cutoff:
            continue

        out.append(make_record(source, title, summary, link, dt, collector_url=url, parser="xml"))

    out.sort(key=lambda r: str(r.get("timestamp_utc", "")), reverse=True)
    return out[:max_items]


def infer_page_patterns(source: str) -> Sequence[str]:
    if source == "sec":
        return [r"/news/press-release/\d{4}-\d+", r"/newsroom/press-releases"]
    if source == "cftc":
        return [r"/PressRoom/PressReleases/\d+", r"/PressRoom/PressReleases"]
    return []


def collect_from_html_page(source: str, url: str, html_text: str, now_utc: datetime, cutoff: datetime, max_items: int) -> List[Dict[str, Any]]:
    patterns = infer_page_patterns(source)
    if not patterns:
        return []

    hrefs = re.findall(r"href=[\"']([^\"']+)[\"']", html_text, flags=re.IGNORECASE)
    candidates: List[str] = []
    for href in hrefs:
        for pat in patterns:
            if re.search(pat, href):
                candidates.append(href)
                break

    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for href in candidates:
        full_link = urllib.parse.urljoin(url, href)
        if full_link in seen:
            continue
        seen.add(full_link)

        # Page fallbacks typically do not expose precise per-item pubdates in a parse-stable format.
        # Use collection timestamp with reduced confidence via neutral summary text.
        dt = now_utc
        if dt < cutoff:
            continue

        tail = full_link.rstrip("/").split("/")[-1].replace("-", " ")
        title = clean_text(tail).title() or f"{source.upper()} policy update"
        summary = "fallback-page-parser"

        rec = make_record(source, title, summary, full_link, dt, collector_url=url, parser="html-fallback")
        rec["confidence"] = round(float(rec["confidence"]) * 0.6, 8)
        out.append(rec)
        if len(out) >= max_items:
            break

    return out


def collect_source(source: str, endpoints: Sequence[str], cutoff: datetime, max_per_source: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]], Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    now = datetime.now(tz=UTC)
    endpoint_attempts = 0
    endpoint_fetch_successes = 0

    for url in endpoints:
        endpoint_attempts += 1
        try:
            text = http_get_text(url)
            endpoint_fetch_successes += 1
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append({"source": source, "url": url, "stage": "fetch", "error": str(exc)})
            continue

        xml_rows: List[Dict[str, Any]] = []
        try:
            xml_rows = collect_from_xml(source, url, text, cutoff=cutoff, max_items=max_per_source)
        except ET.ParseError:
            xml_rows = []

        if xml_rows:
            collected.extend(xml_rows)

        if len(collected) < max_per_source:
            html_rows = collect_from_html_page(source, url, text, now_utc=now, cutoff=cutoff, max_items=max_per_source - len(collected))
            collected.extend(html_rows)

        # stop early when we have enough records from fallback/alternate endpoints
        if len(collected) >= max_per_source:
            break

    collected.sort(key=lambda r: str(r.get("timestamp_utc", "")), reverse=True)
    trimmed = collected[:max_per_source]

    parser_hist: Dict[str, int] = {}
    for row in trimmed:
        meta_raw = row.get("metadata", {})
        meta = cast(Dict[str, Any], meta_raw) if isinstance(meta_raw, dict) else {}
        parser_name = str(meta.get("parser", "unknown"))
        parser_hist[parser_name] = parser_hist.get(parser_name, 0) + 1

    xml_count = parser_hist.get("xml", 0)
    fallback_count = parser_hist.get("html-fallback", 0)
    parsed_total = xml_count + fallback_count

    endpoint_stability = (endpoint_fetch_successes / endpoint_attempts) if endpoint_attempts > 0 else 0.0
    parser_quality = (xml_count / parsed_total) if parsed_total > 0 else 0.0
    coverage = min(1.0, len(trimmed) / max(1, max_per_source))
    reliability_score = max(0.1, min(1.0, (0.15 + 0.55 * endpoint_stability + 0.20 * parser_quality + 0.10 * coverage)))

    source_metrics: Dict[str, Any] = {
        "source": source,
        "endpoint_attempts": endpoint_attempts,
        "endpoint_fetch_successes": endpoint_fetch_successes,
        "endpoint_stability": round(endpoint_stability, 8),
        "xml_rows": xml_count,
        "fallback_rows": fallback_count,
        "parser_quality": round(parser_quality, 8),
        "coverage": round(coverage, 8),
        "rows_collected": len(trimmed),
        "reliability_score": round(reliability_score, 8),
        "recommended_weight_multiplier": round(0.5 + 0.8 * reliability_score, 8),
    }

    return trimmed, errors, source_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect policy/news event records from central-bank and regulator feeds with resilient endpoint fallback parsers.")
    parser.add_argument("--hours-back", type=int, default=168, help="How far back to include events.")
    parser.add_argument("--max-per-feed", type=int, default=60, help="Maximum events per source after filtering.")
    parser.add_argument("--ema-days", type=float, default=7.0, help="Rolling EMA span in days for source reliability memory.")
    parser.add_argument("--ema-drift-cap-up-per-day", type=float, default=0.05, help="Max relative upward EMA multiplier drift per day (e.g. 0.05 = +5%%/day). Trust upgrades are capped here.")
    parser.add_argument("--ema-drift-cap-down-per-day", type=float, default=0.02, help="Max relative downward EMA multiplier drift per day (e.g. 0.02 = -2%%/day). Trust downgrades are capped here.")
    parser.add_argument("--out", default="5-Applications/out/micro_cap_sim/policy_events.jsonl", help="Output JSONL path")
    parser.add_argument("--reliability-out", default="5-Applications/out/micro_cap_sim/policy_source_reliability.json", help="Output JSON path for per-source reliability metrics.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = datetime.now(tz=UTC)
    cutoff = now - timedelta(hours=max(1, int(args.hours_back)))

    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    source_reliability: Dict[str, Dict[str, Any]] = {}

    reliability_out_path = Path(args.reliability_out)
    previous_reliability = load_previous_reliability(reliability_out_path)
    prev_sources_raw = previous_reliability.get("sources", {})
    prev_sources = cast(Dict[str, Any], prev_sources_raw) if isinstance(prev_sources_raw, dict) else {}

    prev_generated_raw = str(previous_reliability.get("generated_utc", ""))
    prev_generated_dt = parse_datetime(prev_generated_raw)
    elapsed_hours = ((now - prev_generated_dt).total_seconds() / 3600.0) if prev_generated_dt is not None else 24.0
    elapsed_days = max(0.0, elapsed_hours / 24.0)
    ema_alpha = ema_alpha_for_elapsed_hours(elapsed_hours=elapsed_hours, ema_days=max(1.0, float(args.ema_days)))

    for source, endpoints in SOURCE_ENDPOINTS.items():
        rows, errs, metrics = collect_source(source=source, endpoints=endpoints, cutoff=cutoff, max_per_source=max(1, int(args.max_per_feed)))
        records.extend(rows)
        errors.extend(errs)

        prev_raw = prev_sources.get(source, {})
        prev = cast(Dict[str, Any], prev_raw) if isinstance(prev_raw, dict) else {}
        prev_ema_reliability = float(prev.get("ema_reliability_score", prev.get("reliability_score", 0.0)) or 0.0)
        prev_ema_multiplier = float(prev.get("ema_recommended_weight_multiplier", prev.get("recommended_weight_multiplier", 1.0)) or 1.0)

        cur_reliability = float(metrics.get("reliability_score", 0.0) or 0.0)
        cur_multiplier = float(metrics.get("recommended_weight_multiplier", 1.0) or 1.0)

        ema_reliability = rolling_ema(cur_reliability, prev_ema_reliability, alpha=ema_alpha)
        ema_multiplier_raw = rolling_ema(cur_multiplier, prev_ema_multiplier, alpha=ema_alpha)
        ema_multiplier_capped, drift_was_capped, applied_cap_up, applied_cap_down = apply_relative_drift_cap(
            prev_value=prev_ema_multiplier,
            proposed_value=ema_multiplier_raw,
            elapsed_hours=elapsed_hours,
            max_drift_up_per_day=max(0.0, float(args.ema_drift_cap_up_per_day)),
            max_drift_down_per_day=max(0.0, float(args.ema_drift_cap_down_per_day)),
        )

        obs_prev = int(prev.get("observations", 0) or 0)
        metrics["ema_days"] = max(1.0, float(args.ema_days))
        metrics["ema_drift_cap_up_per_day"] = max(0.0, float(args.ema_drift_cap_up_per_day))
        metrics["ema_drift_cap_down_per_day"] = max(0.0, float(args.ema_drift_cap_down_per_day))
        metrics["elapsed_days"] = round(elapsed_days, 8)
        metrics["ema_alpha"] = round(ema_alpha, 8)
        metrics["ema_reliability_score"] = round(ema_reliability, 8)
        metrics["ema_recommended_weight_multiplier_raw"] = round(ema_multiplier_raw, 8)
        metrics["ema_recommended_weight_multiplier"] = round(ema_multiplier_capped, 8)
        metrics["ema_drift_cap_up_applied"] = round(applied_cap_up, 8)
        metrics["ema_drift_cap_down_applied"] = round(applied_cap_down, 8)
        metrics["ema_drift_was_capped"] = drift_was_capped
        metrics["observations"] = obs_prev + 1

        source_reliability[source] = metrics

    dedup: Dict[str, Dict[str, Any]] = {}
    for row in records:
        eid = str(row.get("evidence_id", ""))
        if eid:
            dedup[eid] = row

    final_rows = list(dedup.values())
    final_rows.sort(key=lambda r: str(r.get("timestamp_utc", "")), reverse=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in final_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    by_type: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    parser_hist: Dict[str, int] = {}
    for row in final_rows:
        t = str(row.get("event_type", "unknown"))
        by_type[t] = by_type.get(t, 0) + 1

        source = str(row.get("source", "unknown"))
        by_source[source] = by_source.get(source, 0) + 1

        meta_raw = row.get("metadata", {})
        meta = cast(Dict[str, Any], meta_raw) if isinstance(meta_raw, dict) else {}
        parser_name = str(meta.get("parser", "unknown"))
        parser_hist[parser_name] = parser_hist.get(parser_name, 0) + 1

    reliability_out_path.parent.mkdir(parents=True, exist_ok=True)
    reliability_payload: Dict[str, Any] = {
        "version": "v1.0",
        "generated_utc": now.replace(microsecond=0).isoformat(),
        "hours_back": int(args.hours_back),
        "max_per_feed": int(args.max_per_feed),
        "ema_days": max(1.0, float(args.ema_days)),
        "ema_drift_cap_up_per_day": max(0.0, float(args.ema_drift_cap_up_per_day)),
        "ema_drift_cap_down_per_day": max(0.0, float(args.ema_drift_cap_down_per_day)),
        "ema_alpha": round(ema_alpha, 8),
        "elapsed_hours_since_last": round(elapsed_hours, 8),
        "elapsed_days_since_last": round(elapsed_days, 8),
        "sources": source_reliability,
        "errors": errors,
    }
    reliability_out_path.write_text(json.dumps(reliability_payload, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "rows_written": len(final_rows),
                "by_source": by_source,
                "by_event_type": by_type,
                "parser_hist": parser_hist,
                "errors": errors,
                "out": str(out_path),
                "reliability_out": str(reliability_out_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
