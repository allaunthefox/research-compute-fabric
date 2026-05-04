# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
from pathlib import Path
import json
from datasets import load_dataset
from huggingface_hub import HfApi
import geopandas as gpd

OUTPUT_DIR = Path("data_baselines/geospatial").absolute()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG = Path("data_baselines/geospatial_ingest.log")


def normalize_crs(df, target_epsg=4326):
    if hasattr(df, "to_crs"):
        return df.to_crs(epsg=target_epsg)
    return df


def convert_geo(table, out_path):
    if hasattr(table, "to_pandas"):
        df = table.to_pandas()
    else:
        df = table

    if "geometry" in df.columns:
        gdf = gpd.GeoDataFrame(df, geometry="geometry")
        gdf = normalize_crs(gdf)
        gdf.to_file(out_path, driver="GeoJSON")
        return True
    return False


def ingest_dataset(dataset_id):
    print(f"[INGEST] {dataset_id}")
    ds = load_dataset(dataset_id)
    meta = []
    for split, table in ds.items():
        out_dir = OUTPUT_DIR / dataset_id.replace("/", "__")
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_split = split.replace("/", "_")
        target_parquet = out_dir / f"{safe_split}.parquet"
        try:
            table.to_parquet(target_parquet, index=False)
        except Exception as e:
            print(f"  cannot parquet {dataset_id}/{split}: {e}")
            continue

        geojs = out_dir / f"{safe_split}.geojson"
        try:
            convert_geo(table, geojs)
        except Exception as e:
            print(f"  geo conversion fail {dataset_id}/{split}: {e}")

        meta.append({"dataset": dataset_id, "split": split, "path": str(target_parquet), "geojson": str(geojs) if geojs.exists() else None})

    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"dataset": dataset_id, "meta": meta}) + "\n")


if __name__ == "__main__":
    api = HfApi()
    # geospatial + datasets library=datasets trending set
    datasets = []
    results = api.list_datasets(filter="geospatial", sort="trending_score", limit=200)
    for r in results:
        if r.id not in datasets:
            datasets.append(r.id)

    print(f"Found {len(datasets)} datasets")
    for dsid in datasets:
        try:
            ingest_dataset(dsid)
        except Exception as e:
            print(f"FAILED {dsid}: {e}")
