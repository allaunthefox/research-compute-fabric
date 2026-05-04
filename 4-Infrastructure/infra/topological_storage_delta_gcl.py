#!/usr/bin/env python3
"""
Topological Storage Delta GCL Integration

Integrates Delta GCL compression with topological storage manifests.
Compresses metadata before storing to Google Drive topological storage.

Features:
- Delta GCL compression for topological manifests
- Previous state tracking for delta encoding
- Integration with Rclone for storage operations
- Compression statistics tracking

Per AGENTS.md: This is a shim layer - logic in Lean, only JSON marshaling here.
"""

import sys
from pathlib import Path
# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import hashlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from infra.delta_gcl_compression_service import DeltaGCLCompressionService, CompressionResult


@dataclass
class TopologicalManifest:
    """Topological storage manifest."""
    manifest_id: str
    version: int
    timestamp: float
    topology_type: str  # "manifold", "connectome", "resource", etc.
    data: Dict[str, Any]
    compression_metadata: Optional[Dict[str, Any]] = None


@dataclass
class StoredManifest:
    """Manifest stored in topological storage with compression."""
    manifest_id: str
    version: int
    compressed_data: str  # Delta GCL compressed
    original_size: int
    compressed_size: int
    stored_at: float
    storage_path: str


class TopologicalStorageDeltaGCL:
    """
    Delta GCL compression for topological storage manifests.
    
    Compresses manifests before storing to Google Drive topological storage.
    Maintains previous state for delta encoding.
    """
    
    def __init__(self, storage_path: str = "gdrive:topological_storage/manifests"):
        self.storage_path = storage_path
        self.compression_service = DeltaGCLCompressionService()
        self.previous_manifests: Dict[str, TopologicalManifest] = {}
        self.stored_manifests: Dict[str, StoredManifest] = {}
    
    def compress_manifest(self, manifest: TopologicalManifest) -> CompressionResult:
        """Compress manifest using Delta GCL."""
        # Convert to PTOS format for compression
        ptos_manifest = {
            "layer": manifest.topology_type,
            "domain": "TOPOLOGICAL",
            "tier": "STORAGE",
            "condition": "ACTIVE",
            "metadata": manifest.data
        }
        
        # Check if we have previous version for delta encoding
        previous = None
        use_delta = False
        if manifest.manifest_id in self.previous_manifests:
            previous = self.previous_manifests[manifest.manifest_id]
            use_delta = True
        
        # Compress
        result = self.compression_service.compress_manifest(
            ptos_manifest,
            f"topo_{manifest.manifest_id}",
            use_delta=use_delta
        )
        
        # Update previous manifest
        self.previous_manifests[manifest.manifest_id] = manifest
        
        return result
    
    def store_manifest(self, manifest: TopologicalManifest, 
                      storage_path: Optional[str] = None) -> StoredManifest:
        """
        Store manifest to topological storage with Delta GCL compression.
        
        In production, this would call Rclone to upload to Google Drive.
        For now, simulates storage.
        """
        # Compress manifest
        compression_result = self.compress_manifest(manifest)
        
        # Calculate sizes
        original_size = len(json.dumps(manifest.data))
        compressed_size = len(compression_result.delta_gcl)
        
        # Determine storage path
        path = storage_path or self.storage_path
        full_path = f"{path}/{manifest.manifest_id}_v{manifest.version}.delta_gcl"
        
        # Create stored manifest record
        stored = StoredManifest(
            manifest_id=manifest.manifest_id,
            version=manifest.version,
            compressed_data=compression_result.delta_gcl,
            original_size=original_size,
            compressed_size=compressed_size,
            stored_at=datetime.now().timestamp(),
            storage_path=full_path
        )
        
        # Store in local cache (in production: upload via Rclone)
        self.stored_manifests[manifest.manifest_id] = stored
        
        # Add compression metadata to manifest
        manifest.compression_metadata = {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "reduction": original_size - compressed_size,
            "reduction_percent": compression_result.stats["reduction_percent"],
            "compression_method": "delta_gcl",
            "use_delta": compression_result.stats["use_delta"]
        }
        
        return stored
    
    def retrieve_manifest(self, manifest_id: str) -> Optional[TopologicalManifest]:
        """
        Retrieve manifest from topological storage.
        
        In production, this would call Rclone to download from Google Drive.
        For now, retrieves from local cache.
        """
        if manifest_id not in self.stored_manifests:
            return None
        
        stored = self.stored_manifests[manifest_id]
        
        # In production: decompress using Delta GCL
        # For now: return placeholder indicating compression
        return TopologicalManifest(
            manifest_id=stored.manifest_id,
            version=stored.version,
            timestamp=stored.stored_at,
            topology_type="retrieved",
            data={"compressed": True, "path": stored.storage_path},
            compression_metadata={
                "original_size": stored.original_size,
                "compressed_size": stored.compressed_size,
                "reduction": stored.original_size - stored.compressed_size
            }
        )
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get aggregate compression statistics."""
        if not self.stored_manifests:
            return {"total_manifests": 0}
        
        total_original = sum(m.original_size for m in self.stored_manifests.values())
        total_compressed = sum(m.compressed_size for m in self.stored_manifests.values())
        total_reduction = total_original - total_compressed
        avg_reduction = total_reduction / len(self.stored_manifests) if self.stored_manifests else 0
        
        return {
            "total_manifests": len(self.stored_manifests),
            "total_original_size": total_original,
            "total_compressed_size": total_compressed,
            "total_reduction": total_reduction,
            "average_reduction_percent": (avg_reduction / total_original * 100) if total_original > 0 else 0
        }
    
    def list_manifests(self) -> List[str]:
        """List all stored manifest IDs."""
        return list(self.stored_manifests.keys())


# Singleton instance
_storage_instance: Optional[TopologicalStorageDeltaGCL] = None


def get_topological_storage() -> TopologicalStorageDeltaGCL:
    """Get singleton topological storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = TopologicalStorageDeltaGCL()
    return _storage_instance


def store_topological_manifest(manifest: TopologicalManifest) -> StoredManifest:
    """Convenience function to store manifest."""
    storage = get_topological_storage()
    return storage.store_manifest(manifest)


if __name__ == "__main__":
    # Test topological storage with Delta GCL
    print("=" * 70)
    print("TOPOLOGICAL STORAGE DELTA GCL INTEGRATION")
    print("=" * 70)
    
    storage = TopologicalStorageDeltaGCL()
    
    # Create test manifest
    manifest1 = TopologicalManifest(
        manifest_id="manifold_001",
        version=1,
        timestamp=datetime.now().timestamp(),
        topology_type="manifold",
        data={
            "vertices": 1000,
            "edges": 2500,
            "dimension": 14,
            "embedding": "high_dim"
        }
    )
    
    print("\n[1] Storing first manifest (full encoding)...")
    stored1 = storage.store_manifest(manifest1)
    print(f"  Manifest ID: {stored1.manifest_id}")
    print(f"  Storage Path: {stored1.storage_path}")
    print(f"  Compression: {stored1.original_size} → {stored1.compressed_size} bytes")
    print(f"  Reduction: {stored1.original_size - stored1.compressed_size} bytes")
    
    # Create second version (delta encoding)
    manifest2 = TopologicalManifest(
        manifest_id="manifold_001",
        version=2,
        timestamp=datetime.now().timestamp(),
        topology_type="manifold",
        data={
            "vertices": 1005,  # Small change
            "edges": 2510,
            "dimension": 14,
            "embedding": "high_dim"
        }
    )
    
    print("\n[2] Storing second manifest (delta encoding)...")
    stored2 = storage.store_manifest(manifest2)
    print(f"  Manifest ID: {stored2.manifest_id}")
    print(f"  Version: {stored2.version}")
    print(f"  Compression: {stored2.original_size} → {stored2.compressed_size} bytes")
    print(f"  Reduction: {stored2.original_size - stored2.compressed_size} bytes")
    
    # Get aggregate stats
    print("\n[3] Aggregate compression statistics...")
    stats = storage.get_compression_stats()
    print(f"  Total Manifests: {stats['total_manifests']}")
    print(f"  Total Original: {stats['total_original_size']} bytes")
    print(f"  Total Compressed: {stats['total_compressed_size']} bytes")
    print(f"  Total Reduction: {stats['total_reduction']} bytes")
    print(f"  Avg Reduction: {stats['average_reduction_percent']:.2f}%")
    
    print("\n" + "=" * 70)
    print("TOPOLOGICAL STORAGE DELTA GCL OPERATIONAL")
    print("=" * 70)
