#!/usr/bin/env python3
"""
hep_data_puller.py — Pull high-energy physics data from multiple providers

Usage:
    python3 hep_data_puller.py --provider all --output ./hep_data/
    python3 hep_data_puller.py --provider inspire --output ./hep_data/
"""

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import pandas as pd


@dataclass
class PullResult:
    provider: str
    records_pulled: int
    destination: str
    success: bool
    error: Optional[str]
    timestamp: float


class HepDataPuller:
    """Pull data from HEP providers."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[PullResult] = []

    # -------------------------------------------------------------------------
    # CERN Open Data
    # -------------------------------------------------------------------------

    def pull_cern_opendata(self, experiments: List[str] = None) -> PullResult:
        """
        Pull from CERN Open Data Portal.
        API: https://opendata.cern.org/api/records
        """
        if not HAS_REQUESTS:
            return PullResult(
                provider="cern_opendata",
                records_pulled=0,
                destination=str(self.output_dir / "cern"),
                success=False,
                error="requests library not installed",
                timestamp=time.time()
            )

        experiments = experiments or ["LHCb", "ATLAS", "CMS", "ALICE"]
        total_records = 0
        errors = []

        for exp in experiments:
            try:
                url = f"https://opendata.cern.org/api/records"
                params = {
                    "q": f"collaboration:{exp}",
                    "size": 100,
                    "page": 1
                }

                all_records = []
                for page in range(5):  # Max 500 records per experiment
                    params["page"] = page + 1
                    resp = requests.get(url, params=params, timeout=30)
                    if resp.status_code != 200:
                        errors.append(f"{exp}: HTTP {resp.status_code}")
                        break

                    data = resp.json()
                    items = data.get("items", data.get("results", []))
                    if not items:
                        break

                    all_records.extend(items)

                # Save to parquet
                if all_records:
                    df = pd.DataFrame(all_records)
                    path = self.output_dir / "cern" / f"{exp.lower()}.parquet"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    df.to_parquet(path)
                    total_records += len(all_records)

            except Exception as e:
                errors.append(f"{exp}: {str(e)}")

        return PullResult(
            provider="cern_opendata",
            records_pulled=total_records,
            destination=str(self.output_dir / "cern"),
            success=total_records > 0,
            error="; ".join(errors) if errors else None,
            timestamp=time.time()
        )

    # -------------------------------------------------------------------------
    # INSPIRE HEP
    # -------------------------------------------------------------------------

    def pull_inspire(self, queries: List[str] = None) -> PullResult:
        """
        Pull literature metadata from INSPIRE HEP.
        API: https://inspirehep.net/api/literature
        """
        if not HAS_REQUESTS:
            return PullResult(
                provider="inspire",
                records_pulled=0,
                destination=str(self.output_dir / "inspire"),
                success=False,
                error="requests library not installed",
                timestamp=time.time()
            )

        queries = queries or [
            "LHCb",
            "B-meson",
            "penguin decay",
            "rare decay",
            "CP violation"
        ]

        total_records = 0
        errors = []

        for query in queries:
            try:
                url = "https://inspirehep.net/api/literature"
                params = {
                    "q": query,
                    "size": 100,
                    "fields": ["titles", "abstract", "authors", "collaborations", "experiments"]
                }

                resp = requests.get(url, params=params, timeout=30)
                if resp.status_code != 200:
                    errors.append(f"{query}: HTTP {resp.status_code}")
                    continue

                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                if not hits:
                    continue

                # Save to parquet
                df = pd.DataFrame(hits)
                safe_name = query.lower().replace(" ", "_").replace("-", "_")
                path = self.output_dir / "inspire" / f"{safe_name}.parquet"
                path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(path)
                total_records += len(hits)

                time.sleep(0.5)  # Rate limit

            except Exception as e:
                errors.append(f"{query}: {str(e)}")

        return PullResult(
            provider="inspire",
            records_pulled=total_records,
            destination=str(self.output_dir / "inspire"),
            success=total_records > 0,
            error="; ".join(errors) if errors else None,
            timestamp=time.time()
        )

    # -------------------------------------------------------------------------
    # HepData (we already have this)
    # -------------------------------------------------------------------------

    def pull_hepdata(self, source_path: str = "/tmp/hepdata-parquet") -> PullResult:
        """
        Use existing HepData parquet files.
        """
        source = Path(source_path)
        dest = self.output_dir / "hepdata"

        if not source.exists():
            return PullResult(
                provider="hepdata",
                records_pulled=0,
                destination=str(dest),
                success=False,
                error=f"Source path not found: {source_path}",
                timestamp=time.time()
            )

        dest.mkdir(parents=True, exist_ok=True)

        # Copy existing parquet files
        import shutil
        parquet_files = list(source.glob("*.parquet"))

        for pf in parquet_files:
            shutil.copy2(pf, dest / pf.name)

        total = sum(1 for _ in dest.glob("*.parquet"))

        return PullResult(
            provider="hepdata",
            records_pulled=total,
            destination=str(dest),
            success=True,
            error=None,
            timestamp=time.time()
        )

    # -------------------------------------------------------------------------
    # Fermilab
    # -------------------------------------------------------------------------

    def pull_fermilab(self) -> PullResult:
        """
        Fermilab data - requires specific API knowledge.
        """
        return PullResult(
            provider="fermilab",
            records_pulled=0,
            destination=str(self.output_dir / "fermilab"),
            success=False,
            error="Fermilab requires authenticated access. Visit https:// fermilab.gov/data for API details.",
            timestamp=time.time()
        )

    # -------------------------------------------------------------------------
    # Run all
    # -------------------------------------------------------------------------

    def pull_all(self, providers: List[str] = None) -> List[PullResult]:
        """
        Pull from all specified providers.
        """
        providers = providers or ["hepdata", "inspire", "cern_opendata"]

        for provider in providers:
            print(f"Pulling from {provider}...")

            if provider == "hepdata":
                result = self.pull_hepdata()
            elif provider == "inspire":
                result = self.pull_inspire()
            elif provider == "cern_opendata":
                result = self.pull_cern_opendata()
            elif provider == "fermilab":
                result = self.pull_fermilab()
            else:
                result = PullResult(
                    provider=provider,
                    records_pulled=0,
                    destination=str(self.output_dir / provider),
                    success=False,
                    error="Unknown provider",
                    timestamp=time.time()
                )

            self.results.append(result)
            icon = "✓" if result.success else "✗"
            print(f"  {icon} {provider}: {result.records_pulled} records")

        return self.results

    def save_results(self, path: Path):
        """Save pull results to JSON."""
        with open(path, "w") as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Pull HEP data from multiple providers")
    parser.add_argument("--provider", default="all", help="Provider(s) to pull: all, hepdata, inspire, cern, fermilab")
    parser.add_argument("--output", default="/tmp/hep_combined", help="Output directory")
    parser.add_argument("--source-hepdata", default="/tmp/hepdata-parquet", help="Source path for existing HepData")

    args = parser.parse_args()

    print("=" * 70)
    print("HEP DATA PULLER")
    print("=" * 70)
    print()

    output_dir = Path(args.output)
    puller = HepDataPuller(output_dir)

    if args.provider == "all":
        providers = ["hepdata", "inspire", "cern_opendata"]
    elif args.provider == "cern":
        providers = ["cern_opendata"]
    else:
        providers = [args.provider]

    results = puller.pull_all(providers)
    puller.save_results(output_dir / "pull_results.json")

    print()
    print("SUMMARY:")
    print("-" * 70)
    total = sum(r.records_pulled for r in results)
    for r in results:
        icon = "✓" if r.success else "✗"
        print(f"  {icon} {r.provider}: {r.records_pulled} records → {r.destination}")
    print()
    print(f"Total records: {total}")
    print(f"Results saved to: {output_dir / 'pull_results.json'}")


if __name__ == "__main__":
    main()