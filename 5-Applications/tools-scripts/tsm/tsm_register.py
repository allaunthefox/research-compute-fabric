#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Logic-Signal Substrate Hyperledger Register for Graph OS
Finds all documents with logic_signal_substrate content, extracts manifest/metadata/SHA256,
and adds them to the Graph OS hyperledger using ledger_commit opcode.

Usage:
    python 5-Applications/scripts/logic_signal_substrate_hyperledger_register.py
"""

import hashlib
import json
import time
import zlib
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# Import TSM Kernel for ledger operations
try:
    from logic_signal_substrate_mcp_harness import TSMKernel, TermType
except ImportError:
    print("[!] logic_signal_substrate_mcp_harness not found, using embedded TSMKernel")
    
    # Embedded minimal TSMKernel for ledger operations
    class TermType:
        PERMANENT = "permanent"
        LEASE = "lease"
        TICKS = "ticks"
    
    class TSMKernel:
        def __init__(self):
            self.manifold = {}
            self.ledger = []
        
        def absorb_bh(self, data: str, metadata: Dict[str, Any] = None) -> str:
            if metadata is None:
                metadata = {}
            compressed = zlib.compress(data.encode('utf-8'), level=9)
            blob = base64.urlsafe_b64encode(compressed).decode('ascii')
            manifest = {
                'original_size': len(data),
                'compressed_size': len(compressed),
                'entropy_ratio': len(compressed) / len(data) if data else 0,
                'metadata': metadata,
                'timestamp': time.time()
            }
            hash_input = f"{blob}{json.dumps(manifest, sort_keys=True)}".encode('utf-8')
            hash_id = hashlib.sha256(hash_input).hexdigest()
            self.manifold[hash_id] = {
                'blob': blob,
                'manifest': manifest,
                'hash': hash_id,
                'created_at': time.time(),
                'term': TermType.LEASE
            }
            return hash_id
        
        def ledger_commit(self, state_id: str, term: str = TermType.PERMANENT) -> str:
            if state_id not in self.manifold:
                return f"State {state_id} not found"
            self.manifold[state_id]['term'] = term
            self.ledger.append({
                'state_id': state_id,
                'term': term,
                'committed_at': time.time(),
                'manifest': self.manifold[state_id]['manifest']
            })
            return f"Committed {state_id} with term {term}"


@dataclass
class TsmDocument:
    """Represents a Logic-Signal Substrate document with manifest, metadata, and SHA256"""
    file_path: str
    filename: str
    sha256: str
    manifest: Dict[str, Any]
    metadata: Dict[str, Any]
    logic_signal_substrate_content: str
    manifold_id: Optional[str] = None
    ledger_term: str = TermType.PERMANENT


class TsmRegister:
    """
    Registers Logic-Signal Substrate documents into the Graph OS Hyperledger
    
    Process:
    1. Scan for all files containing 'logic_signal_substrate' content
    2. Extract manifest, metadata, and compute SHA256
    3. Absorb into TSM manifold
    4. Commit to hyperledger with PERMANENT term
    """
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.kernel = TSMKernel()
        self.logic_signal_substrate_documents: List[TsmDocument] = []
        self.hyperledger_entries: List[Dict] = []
        
    def calculate_sha256(self, data: bytes) -> str:
        """Calculate SHA256 hash of data"""
        return hashlib.sha256(data).hexdigest()
    
    def extract_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Extract metadata from file content"""
        metadata = {
            'file_path': str(file_path),
            'filename': file_path.name,
            'size_bytes': len(content.encode('utf-8')),
            'line_count': content.count('\n') + 1,
            'detected_at': datetime.utcnow().isoformat() + 'Z',
            'logic_signal_substrate_markers': []
        }
        
        # Detect Logic-Signal Substrate-specific markers
        if '```logic_signal_substrate' in content:
            metadata['logic_signal_substrate_markers'].append('logic_signal_substrate_code_block')
        if 'logic_signal_substrate_version' in content:
            metadata['logic_signal_substrate_markers'].append('logic_signal_substrate_version_header')
        if '@MoE' in content:
            metadata['logic_signal_substrate_markers'].append('moe_directive')
        if 'TSMKernel' in content or 'logic_signal_substrate_kernel' in content:
            metadata['logic_signal_substrate_markers'].append('tsm_kernel_reference')
        if 'ledger_commit' in content:
            metadata['logic_signal_substrate_markers'].append('ledger_opcode')
        if 'manifold_id' in content:
            metadata['logic_signal_substrate_markers'].append('manifold_reference')
        
        # Extract logic_signal_substrate_version if present
        import re
        version_match = re.search(r'"logic_signal_substrate_version":\s*"([^"]+)"', content)
        if version_match:
            metadata['logic_signal_substrate_version'] = version_match.group(1)
        
        # Extract manifold_id if present
        manifold_match = re.search(r'"manifold_id":\s*"([^"]+)"', content)
        if manifold_match:
            metadata['existing_manifold_id'] = manifold_match.group(1)
        
        return metadata
    
    def create_manifest(self, file_path: Path, sha256: str, metadata: Dict) -> Dict[str, Any]:
        """Create a manifest for the Logic-Signal Substrate document"""
        return {
            'schema': 'logic_signal_substrate-hyperledger/v1',
            'document_id': sha256[:16],
            'content_hash': sha256,
            'source_path': str(file_path.relative_to(self.root_path)),
            'registration_timestamp': datetime.utcnow().isoformat() + 'Z',
            'ledger_type': 'Graph OS_HYPERLEDGER',
            'metadata_summary': {
                'size_bytes': metadata.get('size_bytes', 0),
                'line_count': metadata.get('line_count', 0),
                'logic_signal_substrate_markers': metadata.get('logic_signal_substrate_markers', []),
                'logic_signal_substrate_version': metadata.get('logic_signal_substrate_version', 'unknown')
            }
        }
    
    def scan_for_logic_signal_substrate_documents(self) -> List[Path]:
        """Scan the repository for files containing Logic-Signal Substrate content"""
        logic_signal_substrate_files = []
        
        # Patterns to search for
        logic_signal_substrate_patterns = [
            '```logic_signal_substrate',
            'logic_signal_substrate_version',
            'logic_signal_substrate_kernel',
            'logic_signal_substrate_mode',
            '@MoE',
            'TSMKernel',
            'manifold_id',
            'ledger_commit',
            '.logic_signal_substrate',
            'logic_signal_substrate-'
        ]
        
        print(f"[*] Scanning {self.root_path} for Logic-Signal Substrate documents...")
        
        # Search for files with logic_signal_substrate in name or content
        for ext in ['*.py', '*.json', '*.md', '*.logic_signal_substrate', '*.txt', '*.tex', '*.scad', '*.cu', '*.cpp']:
            for file_path in self.root_path.rglob(ext):
                if file_path.is_file():
                    try:
                        # Skip binary files and large files
                        if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                            continue
                        
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        
                        # Check if file contains Logic-Signal Substrate markers
                        has_logic_signal_substrate = any(pattern in content for pattern in logic_signal_substrate_patterns)
                        has_logic_signal_substrate_in_name = 'logic_signal_substrate' in file_path.name.lower()
                        
                        if has_logic_signal_substrate or has_logic_signal_substrate_in_name:
                            logic_signal_substrate_files.append(file_path)
                            
                    except Exception as e:
                        print(f"  [!] Error reading {file_path}: {e}")
        
        print(f"  Found {len(logic_signal_substrate_files)} Logic-Signal Substrate documents")
        return logic_signal_substrate_files
    
    def process_document(self, file_path: Path) -> Optional[TsmDocument]:
        """Process a single Logic-Signal Substrate document"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            content_bytes = content.encode('utf-8')
            
            # Calculate SHA256
            sha256 = self.calculate_sha256(content_bytes)
            
            # Extract metadata
            metadata = self.extract_metadata(file_path, content)
            
            # Create manifest
            manifest = self.create_manifest(file_path, sha256, metadata)
            
            # Create Logic-Signal Substrate document record
            doc = TsmDocument(
                file_path=str(file_path),
                filename=file_path.name,
                sha256=sha256,
                manifest=manifest,
                metadata=metadata,
                logic_signal_substrate_content=content[:10000]  # Truncate for storage
            )
            
            return doc
            
        except Exception as e:
            print(f"  [!] Error processing {file_path}: {e}")
            return None
    
    def register_to_hyperledger(self, doc: TsmDocument) -> Dict[str, Any]:
        """Register a Logic-Signal Substrate document to the Graph OS hyperledger"""
        
        # Step 1: Absorb into TSM manifold
        manifold_data = json.dumps({
            'manifest': doc.manifest,
            'metadata': doc.metadata,
            'sha256': doc.sha256,
            'filename': doc.filename
        })
        
        manifold_id = self.kernel.absorb_bh(
            manifold_data,
            metadata={
                'type': 'logic_signal_substrate_document',
                'filename': doc.filename,
                'sha256': doc.sha256
            }
        )
        
        doc.manifold_id = manifold_id
        
        # Step 2: Commit to hyperledger with PERMANENT term
        commit_result = self.kernel.ledger_commit(manifold_id, TermType.PERMANENT)
        
        # Create hyperledger entry
        entry = {
            'manifold_id': manifold_id,
            'document_id': doc.manifest['document_id'],
            'content_hash': doc.sha256,
            'filename': doc.filename,
            'file_path': doc.file_path,
            'ledger_term': TermType.PERMANENT,
            'commit_result': commit_result,
            'registered_at': datetime.utcnow().isoformat() + 'Z',
            'manifest': doc.manifest,
            'metadata': doc.metadata
        }
        
        self.hyperledger_entries.append(entry)
        return entry
    
    def run(self) -> Dict[str, Any]:
        """Execute the full Logic-Signal Substrate hyperledger registration process"""
        
        print("\n" + "=" * 70)
        print("  Logic-Signal Substrate HYPERLEDGER REGISTER FOR Graph OS")
        print("  Extracting manifest/metadata/SHA256 and committing to ledger")
        print("=" * 70 + "\n")
        
        # Phase 1: Scan for Logic-Signal Substrate documents
        print("[PHASE 1] SCANNING FOR Logic-Signal Substrate DOCUMENTS")
        logic_signal_substrate_files = self.scan_for_logic_signal_substrate_documents()
        print()
        
        # Phase 2: Process documents
        print("[PHASE 2] PROCESSING DOCUMENTS (extracting manifest/metadata/SHA256)")
        for i, file_path in enumerate(logic_signal_substrate_files):
            doc = self.process_document(file_path)
            if doc:
                self.logic_signal_substrate_documents.append(doc)
                print(f"  [{i+1}/{len(logic_signal_substrate_files)}] {file_path.name}")
                print(f"      SHA256: {doc.sha256[:16]}...")
                print(f"      Markers: {', '.join(doc.metadata.get('logic_signal_substrate_markers', []))}")
        print(f"\n  Processed {len(self.logic_signal_substrate_documents)} documents")
        print()
        
        # Phase 3: Register to hyperledger
        print("[PHASE 3] REGISTERING TO Graph OS HYPERLEDGER (ledger_commit)")
        for i, doc in enumerate(self.logic_signal_substrate_documents):
            entry = self.register_to_hyperledger(doc)
            print(f"  [{i+1}/{len(self.logic_signal_substrate_documents)}] {doc.filename}")
            print(f"      Manifold ID: {entry['manifold_id'][:16]}...")
            print(f"      Ledger Term: {entry['ledger_term']}")
            print(f"      Status: {entry['commit_result']}")
        print()
        
        # Phase 4: Summary
        print("[PHASE 4] REGISTRATION SUMMARY")
        print(f"  Total Logic-Signal Substrate documents found: {len(logic_signal_substrate_files)}")
        print(f"  Documents processed: {len(self.logic_signal_substrate_documents)}")
        print(f"  Hyperledger entries: {len(self.hyperledger_entries)}")
        print(f"  TSM manifold size: {len(self.kernel.manifold)}")
        print(f"  Ledger commits: {len(self.kernel.ledger)}")
        print()
        
        # Generate summary report
        summary = {
            'registration_timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_documents_found': len(logic_signal_substrate_files),
            'total_documents_processed': len(self.logic_signal_substrate_documents),
            'total_ledger_entries': len(self.hyperledger_entries),
            'manifold_size': len(self.kernel.manifold),
            'ledger_commits': len(self.kernel.ledger),
            'entries': self.hyperledger_entries
        }
        
        # Save summary to file
        output_path = ROOT / "out" / "logic_signal_substrate_hyperledger_registration.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"[✓] Summary saved to: {output_path}")
        print("\n" + "=" * 70)
        print("  Logic-Signal Substrate HYPERLEDGER REGISTRATION COMPLETE")
        print("=" * 70 + "\n")
        
        return summary


def main():
    """Main entry point"""
    register = TsmRegister(ROOT)
    summary = register.run()
    
    # Print detailed entries for verification
    print("\n[HYPERLEDGER ENTRIES]")
    for entry in summary['entries'][:5]:  # Show first 5
        print(f"\n  Document: {entry['filename']}")
        print(f"    Manifold ID: {entry['manifold_id']}")
        print(f"    Content Hash: {entry['content_hash']}")
        print(f"    Ledger Term: {entry['ledger_term']}")
    
    if len(summary['entries']) > 5:
        print(f"\n  ... and {len(summary['entries']) - 5} more entries")
    
    return summary


if __name__ == "__main__":
    main()
