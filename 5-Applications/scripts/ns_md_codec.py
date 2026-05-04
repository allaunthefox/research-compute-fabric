#!/usr/bin/env python3
import struct

class NibbleSwitch:
    CONTROL_STATES = {
        0: "REJECT", # 00
        1: "ACCEPT", # 01
        2: "HOLD",   # 10
        3: "SNAP"    # 11
    }
    DOMAINS = {
        0: "K-AXIS",    # 00
        1: "C-WINDING", # 01
        2: "M-TENSION", # 10
        3: "Y-BREAK"    # 11
    }

    def __init__(self, nibble: int, count: int = 1, polarity: int = 1):
        self.nibble = nibble & 0xF
        self.count = count
        self.polarity = polarity
        
        self.control = (self.nibble >> 2) & 0x3
        self.domain = self.nibble & 0x3

    def __repr__(self):
        return f"[{self.CONTROL_STATES[self.control]}][{self.DOMAINS[self.domain]}] x{self.count}"

class GCCLRep:
    """
    GCCL-Rep: Representative Bytecode for Manifold Transitions.
    A byte array transport representative of a transition class.
    """
    def __init__(self, baseline_hash: str, target_hash: str, byte_payload: bytes, codec: str = "v1.0"):
        self.baseline_hash = baseline_hash
        self.target_hash = target_hash
        self.bytes = byte_payload
        self.codec = codec

    def decode_switches(self) -> list:
        """
        Decodes the byte array into a stream of transition atoms (2 per byte).
        """
        switches = []
        for byte in self.bytes:
            # High nibble (bits 7-4)
            high = (byte >> 4) & 0xF
            switches.append(NibbleSwitch(high, count=1))
            
            # Low nibble (bits 3-0)
            low = byte & 0xF
            switches.append(NibbleSwitch(low, count=1))
        return switches

    def __repr__(self):
        return f"<GCCL-Rep baseline={self.baseline_hash[:8]} target={self.target_hash[:8]} bytes={len(self.bytes)}>"

def test_gccl_rep():
    # Byte 0x5A = 0101 1010
    # 0101 = ACCEPT + C-winding
    # 1010 = HOLD + M-tension
    payload = bytes([0x5A, 0x0F]) # 0101 1010, 0000 1111
    
    rep = GCCLRep("hash_a", "hash_b", payload)
    print(f"--- GCCL-Rep Test ---")
    print(rep)
    
    switches = rep.decode_switches()
    for i, sw in enumerate(switches):
        print(f"  Atom {i}: {sw}")

if __name__ == "__main__":
    test_gccl_rep()
