#!/usr/bin/env python3
"""
csv_to_parquet.py — Convert 50 years of HEPData CSVs to Parquet format

Input:  /tmp/hepdata-bulk/ (49 records, 642 CSV files)
Output: /tmp/hepdata-parquet/ (consolidated Parquet files)

Parquet advantages:
  - Columnar storage (10x faster reads for analytics)
  - Compression (typically 3-10x smaller)
  - Schema enforcement
  - Predicate pushdown for filtering

Usage:
    python3 csv_to_parquet.py
"""

import os
import json
import glob
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
import re
import sys

def parse_hepdata_csv(filepath):
    """Parse a HEPData CSV file into a DataFrame."""
    rows = []
    metadata = {}
    current_table = None
    current_observable = None
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Extract metadata from comments
            if line.startswith('#:'):
                parts = line[2:].split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key == 'table_doi':
                        metadata['doi'] = value
                    elif key == 'name':
                        metadata['table_name'] = value
                    elif key == 'description':
                        metadata['description'] = value
                    continue
            
            # Skip empty lines and pure comment headers
            if not line or line.startswith('#'):
                continue
            
            # Try to parse as CSV
            parts = line.split(',')
            
            # Check if this looks like data (first element is numeric)
            try:
                first_val = float(parts[0])
                # This is a data row
                row = {
                    'source_file': os.path.basename(filepath),
                    'row_data': line
                }
                
                # Extract observable name from previous header if available
                if current_observable:
                    row['observable'] = current_observable
                
                rows.append(row)
            except ValueError:
                # This might be a header line with observable name
                # Check for patterns like $P'_{5}$ or $F_{\rm L}$
                if '$' in line:
                    # Extract observable name
                    match = re.search(r'\$([^$]+)\$', line)
                    if match:
                        current_observable = match.group(1)
                        # Clean up LaTeX
                        current_observable = current_observable.replace('\\rm ', '')
                        current_observable = current_observable.replace('\\', '')
    
    return rows, metadata

def process_record(record_dir):
    """Process all CSV files in a HEPData record directory."""
    record_name = os.path.basename(record_dir)
    record_id = record_name.replace('HEPData-', '').replace('-csv', '')
    
    all_rows = []
    
    for csv_file in sorted(Path(record_dir).glob("*.csv")):
        rows, metadata = parse_hepdata_csv(str(csv_file))
        for row in rows:
            row['record_id'] = record_id
            row['record_name'] = record_name
            row['table_file'] = csv_file.name
            row['doi'] = metadata.get('doi', '')
            row['table_name'] = metadata.get('table_name', '')
            row['description'] = metadata.get('description', '')
        all_rows.extend(rows)
    
    return all_rows

def main():
    bulk_dir = Path("/tmp/hepdata-bulk")
    output_dir = Path("/tmp/hepdata-parquet")
    output_dir.mkdir(exist_ok=True)
    
    print("Scanning HEPData records...", file=sys.stderr)
    
    all_rows = []
    record_count = 0
    
    for record_dir in sorted(bulk_dir.iterdir()):
        if record_dir.is_dir() and record_dir.name.startswith("HEPData-"):
            rows = process_record(record_dir)
            all_rows.extend(rows)
            record_count += 1
            
            if record_count % 10 == 0:
                print(f"  Processed {record_count} records, {len(all_rows)} rows...", file=sys.stderr)
    
    print(f"Total: {record_count} records, {len(all_rows)} rows", file=sys.stderr)
    
    if not all_rows:
        print("No data found!", file=sys.stderr)
        sys.exit(1)
    
    # Create DataFrame
    df = pd.DataFrame(all_rows)
    
    # Add derived columns
    df['record_index'] = df.index
    
    # Write to Parquet (partitioned by record_id for efficient queries)
    print("Writing Parquet files...", file=sys.stderr)
    
    # Single file for small dataset
    single_path = output_dir / "hepdata_all.parquet"
    df.to_parquet(single_path, engine='pyarrow', compression='snappy')
    print(f"  Single file: {single_path} ({os.path.getsize(single_path) / 1024:.1f} KB)", file=sys.stderr)
    
    # Partitioned by record (for large-scale queries)
    partitioned_path = output_dir / "partitioned"
    df.to_parquet(partitioned_path, engine='pyarrow', compression='snappy', 
                  partition_cols=['record_id'])
    print(f"  Partitioned: {partitioned_path}", file=sys.stderr)
    
    # Summary statistics
    summary = {
        'total_records': record_count,
        'total_rows': len(df),
        'unique_records': df['record_id'].nunique(),
        'unique_tables': df['source_file'].nunique(),
        'columns': list(df.columns),
        'file_size_mb': os.path.getsize(single_path) / (1024 * 1024),
        'parquet_file': str(single_path),
        'partitioned_dir': str(partitioned_path)
    }
    
    # Save summary
    summary_path = output_dir / "summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary:", file=sys.stderr)
    print(f"  Records: {summary['total_records']}", file=sys.stderr)
    print(f"  Rows: {summary['total_rows']}", file=sys.stderr)
    print(f"  File size: {summary['file_size_mb']:.2f} MB", file=sys.stderr)
    
    # Print summary to stdout
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
