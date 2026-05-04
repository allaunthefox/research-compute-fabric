import sqlite3
import math
import json
import os

DB_PATH = "/home/allaun/Documents/Research Stack/data/substrate_index.db"

def calculate_pist_phase(n):
    if n == 0: return "GROUNDED"
    k = math.isqrt(n)
    a = n - k**2
    b = (k+1)**2 - n
    m = a * b
    
    max_m = (2*k + 1)**2 / 4.0
    rho = 4 * m / (2*k + 1)**2 if max_m > 0 else 0
    
    if m == 0: return "GROUNDED"
    if rho < 0.5: return "DRIFT"
    return "SEISMIC"

def run_sweep():
    if not os.path.exists(DB_PATH):
        print("❌ Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("🚀 Initiating PIST-mass sweep for NOTION domain...")
    
    cur.execute("SELECT pkg, tags FROM packages_fts WHERE domain = 'NOTION'")
    rows = cur.fetchall()
    
    updates = []
    for idx, (pkg, tags_json) in enumerate(rows):
        n = idx + 1 # Manifold Coordinate
        phase = calculate_pist_phase(n)
        
        tags = json.loads(tags_json) if tags_json else []
        # Remove old phase tags
        tags = [t for t in tags if t not in ["GROUNDED", "DRIFT", "SEISMIC"]]
        tags.append(phase)
        
        updates.append((json.dumps(tags), pkg))
    
    cur.executemany("UPDATE packages_fts SET tags = ? WHERE pkg = ? AND domain = 'NOTION'", updates)
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully neutralized {len(updates)} Notion nodes with PIST phase tags.")

if __name__ == "__main__":
    run_sweep()
