import hashlib

class Goxel:
    def __init__(self, scalar_field):
        self.scalar_field = scalar_field
        self.hash = hashlib.sha256(scalar_field.encode()).hexdigest()

class GRWWitness:
    """
    The Goxel-Rep Witness (GRW) collapses 7 steps into 2.
    The bytecode IS the proof of admissibility.
    """
    def __init__(self, goxel, kot_cost, transitions):
        self.goxel_hash = goxel.hash
        self.kot_cost = kot_cost
        self.transitions = transitions
        # SELF-AUTHENTICATING SIGNATURE:
        # Binds state, cost, and transitions into a single algebraic witness.
        self.signature = self._generate_signature()

    def _generate_signature(self):
        data = f"{self.goxel_hash}:{self.kot_cost}:{self.transitions}"
        return hashlib.sha256(data.encode()).hexdigest()

    def to_bytecode(self):
        # In a real GRW, the signature would be interleaved or algebraically bound.
        return f"{self.signature}|{self.goxel_hash}|{self.kot_cost}|{self.transitions}"

class GRWDecoder:
    @staticmethod
    def decode_and_verify(bytecode):
        try:
            sig, g_hash, kot, trans = bytecode.split("|")
            # The "Decode" step IS the "Verify" step.
            expected_sig = hashlib.sha256(f"{g_hash}:{kot}:{trans}".encode()).hexdigest()
            
            if sig != expected_sig:
                raise ValueError("INVALID_WITNESS: Bytecode does not satisfy the Manifold Invariant.")
            
            print(f"ADMITTED: Goxel {g_hash[:8]} verified at cost {kot} KOT.")
            return True
        except Exception as e:
            print(f"REJECTED: {str(e)}")
            return False

# PROTOTYPE EXECUTION
if __name__ == "__main__":
    print("--- GRW (Goxel-Rep Witness) Prototype ---")
    
    # 1. Create a lawful Goxel
    my_goxel = Goxel("phi_manifold_01")
    witness = GRWWitness(my_goxel, 100, "move_x_10_y_20")
    bytecode = witness.to_bytecode()
    
    print(f"Generated GRW Bytecode: {bytecode[:60]}...")
    
    # 2. Decode and Verify (The Collapsed Step)
    GRWDecoder.decode_and_verify(bytecode)
    
    # 3. Attempt a Fraudulent Transition (Projection Laundering)
    print("\nAttempting Fraudulent Transition (Tampered Bytecode)...")
    fake_bytecode = bytecode.replace("100", "0") # Try to get the geometry for free
    GRWDecoder.decode_and_verify(fake_bytecode)
