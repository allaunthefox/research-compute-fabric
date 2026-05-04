import json
import os

MAP_PATH = "/home/allaun/Documents/Research Stack/docs/geometry/EPISTEMIC_MAP_V1.json"
TEMP_PATH = MAP_PATH + ".tmp"

NEW_ENTRIES = {
    "6-Documentation/docs/formal_spec/BLINK_DIAT_AMMR_SPEC.md": {
        "pos": [5.5, 9.85, 0.9],
        "sha256": "f61af6b7a8dc94581e14158b512202d5428b1892c79a2de0fc6265dab07547bf",
        "category": "SPECIFICATION",
        "tags": ["AUDIT", "CRYPTOGRAPHY", "DOCUMENTATION", "GEOMETRY", "SPECIFICATION", "BLINK"]
    },
    "tools/verify_blink_proof.py": {
        "pos": [5.5, 5.86, 0.8],
        "sha256": "9043a6ec1d1df822ffa8c87a2ec1e46de98391f31599e390b111feff6b399ae8",
        "category": "CODE",
        "tags": ["AUDIT", "CODE", "CRYPTOGRAPHY", "GEOMETRY", "RELIABILITY"]
    },
    "0-Core-Formalism/core/gwl-vm/src/consensus/blink_avalanche.rs": {
        "pos": [5.5, 1.9, 0.8],
        "sha256": "cdc38a2f0ddd0d765fa381474cafa9b39b986fed0be3dfd3ed5b00174d8c4235",
        "category": "CODE",
        "tags": ["CODE", "CORE", "CRYPTOGRAPHY", "RELIABILITY"]
    }
}

def update_map():
    print(f"Loading {MAP_PATH}...")
    with open(MAP_PATH, "r") as f:
        data = json.load(f)
    
    # Update count
    initial_count = data["total_files"]
    for key, val in NEW_ENTRIES.items():
        if key not in data["coordinates"]:
            data["total_files"] += 1
        data["coordinates"][key] = val
        print(f"Update: {key}")
    
    print(f"Saving {TEMP_PATH} (Initial files: {initial_count}, Final: {data['total_files']})")
    with open(TEMP_PATH, "w") as f:
        json.dump(data, f, indent=2)
    
    # Atomic rename
    os.rename(TEMP_PATH, MAP_PATH)
    print("Optimization Complete.")

if __name__ == "__main__":
    update_map()
