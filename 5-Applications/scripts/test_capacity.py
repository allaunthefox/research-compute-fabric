#!/usr/bin/env python3
import os
import hashlib
import sys

def test_drive(dev_path, logical_size_gb=29):
    print(f"[*] Testing {dev_path} for capacity fraud...")
    
    offsets_gb = [0, 1, 2, 4, 8, 16, 24, 28]
    test_size = 1024 * 1024 # 1MB test chunks
    
    hashes = {}
    
    try:
        with open(dev_path, "wb", buffering=0) as f:
            for gb in offsets_gb:
                offset = gb * 1024 * 1024 * 1024
                print(f"[>] Writing 1MB at {gb}GB offset...")
                data = os.urandom(test_size)
                hashes[gb] = hashlib.sha256(data).hexdigest()
                f.seek(offset)
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
        
        print("\n[*] Verifying data...")
        with open(dev_path, "rb", buffering=0) as f:
            for gb in offsets_gb:
                offset = gb * 1024 * 1024 * 1024
                f.seek(offset)
                data = f.read(test_size)
                actual_hash = hashlib.sha256(data).hexdigest()
                
                if actual_hash == hashes[gb]:
                    print(f"[+] {gb}GB: OK")
                else:
                    print(f"[!] {gb}GB: CORRUPT (Expected {hashes[gb][:8]}, got {actual_hash[:8]})")
                    
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_capacity.py <device>")
    else:
        test_drive(sys.argv[1])
