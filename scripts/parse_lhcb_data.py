#!/usr/bin/env python3
"""
parse_lhcb_data.py — Parse LHCb B→K*μμ angular observables from HEPData CSV

Input: CSV files downloaded via hepdata-cli
Output: JSON format for Lean pipeline ingestion

Usage:
    python3 parse_lhcb_data.py /tmp/hepdata-downloads/HEPData-ins1409497-v1-csv/
"""

import csv
import json
import sys
import os

def parse_table4(filepath):
    """Parse Table 4: Optimised angular observables (P1-P8')."""
    observables = {}
    current_obs = None
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Detect observable name from header lines
            if '$P^{\\prime}_{5}$' in line or "P'_{5}" in line:
                current_obs = "P5p"
                continue
            elif '$P^{\\prime}_{4}$' in line or "P'_{4}" in line:
                current_obs = "P4p"
                continue
            elif '$P^{\\prime}_{6}$' in line or "P'_{6}" in line:
                current_obs = "P6p"
                continue
            elif '$P^{\\prime}_{8}$' in line or "P'_{8}" in line:
                current_obs = "P8p"
                continue
            elif '$P_{1}$' in line:
                current_obs = "P1"
                continue
            elif '$P_{2}$' in line:
                current_obs = "P2"
                continue
            elif '$P_{3}$' in line:
                current_obs = "P3"
                continue
            elif '$F_{\\rm L}$' in line:
                current_obs = "FL"
                continue
            
            # Skip comment/header lines
            if line.startswith('#') or not line:
                continue
            
            # Parse data lines
            parts = line.split(',')
            if len(parts) >= 5 and current_obs:
                try:
                    q2_center = float(parts[0])
                    q2_lo = float(parts[1])
                    q2_hi = float(parts[2])
                    value = float(parts[3])
                    stat_err = float(parts[4])
                    
                    bin_key = f"{q2_lo:.2f}-{q2_hi:.2f}"
                    if bin_key not in observables:
                        observables[bin_key] = {
                            "q2_lo": q2_lo,
                            "q2_hi": q2_hi,
                            "q2_center": q2_center
                        }
                    observables[bin_key][current_obs] = {
                        "value": value,
                        "stat_err": stat_err
                    }
                except (ValueError, IndexError):
                    continue
    
    return observables

def parse_table2(filepath):
    """Parse Table 2: CP-averaged observables (FL, S3-S9, AFB)."""
    observables = {}
    current_obs = None
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Detect observable name from header lines
            if '$F_{\\rm L}$' in line:
                current_obs = "FL"
                continue
            elif '$S_{3}$' in line:
                current_obs = "S3"
                continue
            elif '$S_{4}$' in line:
                current_obs = "S4"
                continue
            elif '$S_{5}$' in line:
                current_obs = "S5"
                continue
            elif '$A_{\\rm FB}$' in line:
                current_obs = "AFB"
                continue
            
            # Skip comment/header lines
            if line.startswith('#') or not line:
                continue
            
            parts = line.split(',')
            if len(parts) >= 5 and current_obs:
                try:
                    q2_center = float(parts[0])
                    q2_lo = float(parts[1])
                    q2_hi = float(parts[2])
                    value = float(parts[3])
                    stat_err = float(parts[4])
                    
                    bin_key = f"{q2_lo:.2f}-{q2_hi:.2f}"
                    if bin_key not in observables:
                        observables[bin_key] = {
                            "q2_lo": q2_lo,
                            "q2_hi": q2_hi,
                            "q2_center": q2_center
                        }
                    observables[bin_key][current_obs] = {
                        "value": value,
                        "stat_err": stat_err
                    }
                except (ValueError, IndexError):
                    continue
    
    return observables

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 parse_lhcb_data.py <hepdata-csv-directory>")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    
    # Parse Table 4 (P' observables)
    table4_path = os.path.join(data_dir, "Table4.csv")
    p_obs = parse_table4(table4_path) if os.path.exists(table4_path) else {}
    
    # Parse Table 2 (FL, S3-S9)
    table2_path = os.path.join(data_dir, "Table2.csv")
    s_obs = parse_table2(table2_path) if os.path.exists(table2_path) else {}
    
    # Merge observations
    all_data = {}
    for bin_key, data in s_obs.items():
        all_data[bin_key] = data
    for bin_key, data in p_obs.items():
        if bin_key in all_data:
            all_data[bin_key].update(data)
        else:
            all_data[bin_key] = data
    
    # Convert to list and sort by q²
    result = []
    for bin_key, data in sorted(all_data.items(), key=lambda x: float(x[0].split('-')[0])):
        entry = {
            "q2_bin": bin_key,
            "q2_lo": data["q2_lo"],
            "q2_hi": data["q2_hi"],
            "q2_center": data["q2_center"]
        }
        for obs in ["FL", "S3", "S4", "S5", "AFB", "P1", "P2", "P3", "P4p", "P5p", "P6p", "P8p"]:
            if obs in data:
                entry[obs] = data[obs]["value"]
                entry[f"{obs}_err"] = data[obs]["stat_err"]
        result.append(entry)
    
    # Output JSON
    output = {
        "source": "LHCb Collaboration, JHEP 02 (2016) 104",
        "hepdata_record": "ins1409497",
        "dataset": "B0 → K*(892)0 μ+ μ-",
        "luminosity": "3.0 fb⁻¹",
        "observables": result
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
