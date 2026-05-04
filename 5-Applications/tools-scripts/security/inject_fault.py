import sqlite3
import json
import os
from datetime import datetime

def inject_phonon_fault():
    db_path = os.path.expanduser("~/.tardy_mmr.db")
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    ts = datetime.utcnow().isoformat() + "+00:00"
    
    # Payload indicating hardware algebraic parity failure
    payload = {
        "agent": "TaN-Systolic-Ring",
        "fault": True,
        "parity_error": True,
        "ring_node": 7,
        "root": "ffffffffffffffff"
    }
    
    conn.execute(
        "INSERT INTO mmr (leaf_type, payload, leaf_hash, root_hash, ts, node_id, sig) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("PHONON_AMMR", json.dumps(payload), "deadbeef", "deadbeef", ts, "Node-07", "FAULT")
    )
    conn.commit()
    conn.close()
    print("Success: Injected PHONON_AMMR fault record into MMR.")

if __name__ == "__main__":
    inject_phonon_fault()
