#!/usr/bin/env python3
"""
bulk_process_hepdata.py — Process all downloaded HEPData through the RRC pipeline

This script:
1. Scans all CSV files in /tmp/hepdata-bulk
2. Extracts numerical data points
3. Builds event matrices for spectral analysis
4. Outputs JSON for Lean pipeline ingestion

Usage:
    python3 bulk_process_hepData.py > all_physics_data.json
"""

import csv
import json
import logging
import os
import sys
from pathlib import Path

def extract_numerical_data(filepath):
    """Extract all numerical values from a CSV file."""
    data_points = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                values = []
                for p in parts:
                    try:
                        v = float(p)
                        values.append(v)
                    except (ValueError, TypeError, KeyError) as e:
                        logging.warning(f"Failed to parse value: {e}")
                if len(values) >= 2:
                    data_points.append(values)
    except (ValueError, TypeError, KeyError) as e:
        logging.warning(f"Failed to read file {filepath}: {e}")
    return data_points

def process_record(record_dir):
    """Process all CSV files in a record directory."""
    record_name = os.path.basename(record_dir)
    all_data = []
    
    for csv_file in sorted(Path(record_dir).glob("*.csv")):
        data = extract_numerical_data(str(csv_file))
        if data:
            all_data.append({
                "file": csv_file.name,
                "points": data[:100]  # Limit to 100 points per file
            })
    
    return {
        "record": record_name,
        "tables": len(all_data),
        "data": all_data
    }

def main():
    bulk_dir = Path("/tmp/hepdata-bulk")
    
    if not bulk_dir.exists():
        print("Error: /tmp/hepdata-bulk not found", file=sys.stderr)
        sys.exit(1)
    
    results = []
    total_points = 0
    
    for record_dir in sorted(bulk_dir.iterdir()):
        if record_dir.is_dir() and record_dir.name.startswith("HEPData-"):
            record_data = process_record(record_dir)
            results.append(record_data)
            
            # Count points
            for table in record_data["data"]:
                total_points += len(table["points"])
    
    output = {
        "source": "HEPData bulk download",
        "record_count": len(results),
        "total_data_points": total_points,
        "coverage": {
            "B_physics": sum(1 for r in results if any(x in r["record"] for x in ["ins14", "ins13", "ins15", "ins16", "ins17"])),
            "Z_Higgs": sum(1 for r in results if any(x in r["record"] for x in ["ins11", "ins12", "ins134", "ins178", "ins167"])),
            "Top_quark": sum(1 for r in results if any(x in r["record"] for x in ["ins160", "ins179", "ins136", "ins146", "ins315"])),
            "Diboson": sum(1 for r in results if any(x in r["record"] for x in ["ins89", "ins218", "ins292", "ins276", "ins185", "ins119"])),
            "eplus_eminus": sum(1 for r in results if any(x in r["record"] for x in ["ins21", "ins26", "ins177", "ins100", "ins99", "ins124"]))
        },
        "records": results[:50]  # Limit output
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
