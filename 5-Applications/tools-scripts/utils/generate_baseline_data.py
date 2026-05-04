import os
import hashlib

def expand_primer(source_path, target_path, target_size_mb=100):
    """
    Expands the primer file to target_size_mb using a deterministic 
    expansion scheme based on SHA256 hashing.
    """
    if not os.path.exists(source_path):
        print(f"Error: Source primer not found at {source_path}")
        # If missing, we'll create a synthetic root
        chunk = b"Sovereign-Root-Axiom-2026-04-13"
    else:
        with open(source_path, "rb") as f:
            chunk = f.read()

    print(f"Expanding primer to {target_size_mb}MB...")
    target_bytes = target_size_mb * 1024 * 1024
    
    with open(target_path, "wb") as f:
        written = 0
        while written < target_bytes:
            # Hash-linked expansion to ensure non-repetitive but deterministic data
            chunk = hashlib.sha256(chunk).digest()
            to_write = min(len(chunk), target_bytes - written)
            f.write(chunk[:to_write])
            written += to_write
            
            # Periodically add a salt to prevent short cycles
            if written % (1024 * 1024) == 0:
                chunk = hashlib.sha256(chunk + struct_pack_u32(written)).digest()

    print(f"Success: Created {target_path} ({os.path.getsize(target_path) / 1e6:.2f} MB)")

def struct_pack_u32(val):
    import struct
    return struct.pack("<I", val)

if __name__ == "__main__":
    # Source is the original 8-byte root seed
    source = os.path.expanduser("~/.gemini/antigravity/scratch/seismic_primer.dat")
    # Target is the 1GB expanded baseline
    target = os.path.expanduser("~/.gemini/antigravity/scratch/seismic_primer_1gb.dat")
    expand_primer(source, target, 1000) # 1GB
