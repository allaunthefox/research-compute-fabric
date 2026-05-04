#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast


def sha256_hex_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def chunk_file(path: Path, chunk_size: int) -> List[Tuple[int, int, bytes]]:
    chunks: List[Tuple[int, int, bytes]] = []
    with path.open("rb") as handle:
        index = 0
        offset = 0
        while True:
            data = handle.read(chunk_size)
            if not data:
                break
            chunks.append((index, offset, data))
            index += 1
            offset += len(data)
    return chunks


def build_manifest(input_path: Path, chunk_size: int) -> Dict[str, Any]:
    file_bytes = input_path.read_bytes()
    file_hash = sha256_hex_bytes(file_bytes)

    chunks = chunk_file(input_path, chunk_size=chunk_size)
    chunk_rows: List[Dict[str, Any]] = []
    leaf_hashes: List[str] = []

    for index, offset, data in chunks:
        c_hash = sha256_hex_bytes(data)
        leaf_hashes.append(c_hash)
        chunk_rows.append(
            {
                "index": index,
                "offset_bytes": offset,
                "length_bytes": len(data),
                "sha256_hex": c_hash,
                "sha256_bytes": 32,
                "sha256_nibbles": 64,
            }
        )

    merkle_root = sha256_hex_bytes("".join(leaf_hashes).encode("ascii")) if leaf_hashes else ""

    return {
        "version": "manifest.v1",
        "path": str(input_path),
        "file_size_bytes": len(file_bytes),
        "file_size_nibbles": len(file_bytes) * 2,
        "sha256_hex": file_hash,
        "sha256_bytes": 32,
        "sha256_nibbles": 64,
        "chunk_size_bytes": chunk_size,
        "chunk_count": len(chunk_rows),
        "merkle_root_sha256": merkle_root,
        "chunks": chunk_rows,
    }


def write_chunk_store(input_path: Path, manifest: Dict[str, Any], store_dir: Path) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)
    chunks = cast_list_dict(manifest.get("chunks", []))

    with input_path.open("rb") as handle:
        for chunk in chunks:
            offset = int(chunk["offset_bytes"])
            length = int(chunk["length_bytes"])
            digest = str(chunk["sha256_hex"])
            handle.seek(offset)
            data = handle.read(length)
            out = store_dir / f"{digest}.bin"
            if not out.exists():
                out.write_bytes(data)


def cast_list_dict(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        out: List[Dict[str, Any]] = []
        for v in cast(List[Any], value):
            if isinstance(v, dict):
                out.append(cast(Dict[str, Any], v))
        return out
    return []


def verify_manifest(manifest: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
    expected_size = int(manifest.get("file_size_bytes", 0) or 0)
    expected_hash = str(manifest.get("sha256_hex", ""))

    actual_size = file_path.stat().st_size
    actual_hash = sha256_file(file_path)

    return {
        "size_match": actual_size == expected_size,
        "hash_match": actual_hash == expected_hash,
        "actual_size_bytes": actual_size,
        "actual_sha256_hex": actual_hash,
    }


def rebuild_from_store(manifest: Dict[str, Any], chunk_store: Path, out_file: Path) -> Dict[str, Any]:
    chunks = cast_list_dict(manifest.get("chunks", []))
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with out_file.open("wb") as handle:
        for chunk in sorted(chunks, key=lambda c: int(c.get("index", 0))):
            digest = str(chunk.get("sha256_hex", ""))
            source_path = chunk_store / f"{digest}.bin"
            if not source_path.exists():
                raise FileNotFoundError(f"missing chunk in store: {source_path}")

            data = source_path.read_bytes()
            expected_len = int(chunk.get("length_bytes", 0) or 0)
            if len(data) != expected_len:
                raise ValueError(f"chunk length mismatch for {digest}: got {len(data)} expected {expected_len}")

            if sha256_hex_bytes(data) != digest:
                raise ValueError(f"chunk hash mismatch for {digest}")

            handle.write(data)

    return verify_manifest(manifest, out_file)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic file manifests with nibble sizes and SHA-256 metadata, plus verify/rebuild operations.")
    sub = parser.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="Build manifest from input file")
    b.add_argument("--input", required=True, help="Input file path")
    b.add_argument("--manifest-out", required=True, help="Output manifest JSON path")
    b.add_argument("--chunk-size-bytes", type=int, default=1024 * 1024, help="Chunk size in bytes")
    b.add_argument("--chunk-store", default="", help="Optional directory to emit chunk blobs named by SHA-256")

    v = sub.add_parser("verify", help="Verify file against manifest")
    v.add_argument("--manifest", required=True, help="Manifest JSON path")
    v.add_argument("--file", required=True, help="File to verify")

    r = sub.add_parser("rebuild", help="Rebuild file from chunk store + manifest")
    r.add_argument("--manifest", required=True, help="Manifest JSON path")
    r.add_argument("--chunk-store", required=True, help="Chunk store directory")
    r.add_argument("--out-file", required=True, help="Rebuilt output file")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "build":
        in_path = Path(args.input)
        manifest = build_manifest(in_path, chunk_size=max(1, int(args.chunk_size_bytes)))

        out_path = Path(args.manifest_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        if args.chunk_store:
            write_chunk_store(in_path, manifest, Path(args.chunk_store))

        print(
            json.dumps(
                {
                    "manifest": str(out_path),
                    "file_size_bytes": manifest["file_size_bytes"],
                    "file_size_nibbles": manifest["file_size_nibbles"],
                    "sha256_hex": manifest["sha256_hex"],
                    "chunk_count": manifest["chunk_count"],
                },
                indent=2,
            )
        )
        return 0

    if args.command == "verify":
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        result = verify_manifest(manifest, Path(args.file))
        print(json.dumps(result, indent=2))
        return 0 if result["size_match"] and result["hash_match"] else 2

    if args.command == "rebuild":
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        result = rebuild_from_store(manifest, Path(args.chunk_store), Path(args.out_file))
        print(json.dumps(result, indent=2))
        return 0 if result["size_match"] and result["hash_match"] else 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
