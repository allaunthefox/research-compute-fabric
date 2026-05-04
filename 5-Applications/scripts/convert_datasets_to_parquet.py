#!/usr/bin/env python3
"""
Convert Training Datasets to Parquet Format

This script converts the consolidated training datasets from JSONL to Parquet format
for efficient storage and processing.
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def convert_jsonl_to_parquet(jsonl_path: str, parquet_path: str) -> int:
    """Convert JSONL file to Parquet format using chunked processing."""
    try:
        chunk_size = 5000  # Process 5000 records at a time
        total_records = 0
        chunk_files = []
        
        print(f"Reading {jsonl_path} in chunks of {chunk_size}...")
        
        # Create temporary directory for chunks
        temp_dir = Path(parquet_path).parent / "temp_chunks"
        temp_dir.mkdir(exist_ok=True)
        
        # Read and process in chunks
        records = []
        chunk_num = 0
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        records.append(record)
                        total_records += 1
                        
                        # Process chunk when we reach chunk_size
                        if len(records) >= chunk_size:
                            chunk_num += 1
                            print(f"  Processing chunk {chunk_num} (records {total_records - chunk_size + 1}-{total_records})...")
                            chunk_file = process_chunk_to_file(records, temp_dir, chunk_num)
                            chunk_files.append(chunk_file)
                            records = []
                    except json.JSONDecodeError:
                        continue
        
        # Process remaining records
        if records:
            chunk_num += 1
            print(f"  Processing final chunk {chunk_num} (records {total_records - len(records) + 1}-{total_records})...")
            chunk_file = process_chunk_to_file(records, temp_dir, chunk_num)
            chunk_files.append(chunk_file)
        
        print(f"  Total records: {total_records}")
        print(f"  Merging {len(chunk_files)} chunk files...")
        
        # Merge all chunk files
        merge_chunk_files(chunk_files, parquet_path)
        
        # Clean up temporary files
        print(f"  Cleaning up temporary files...")
        for chunk_file in chunk_files:
            chunk_file.unlink()
        temp_dir.rmdir()
        
        # Get file size
        parquet_size = Path(parquet_path).stat().st_size / 1024 / 1024  # MB
        print(f"  Parquet file size: {parquet_size:.2f} MB")
        
        return total_records
    except Exception as e:
        print(f"Error converting {jsonl_path}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def process_chunk_to_file(records: list, temp_dir: Path, chunk_num: int) -> Path:
    """Process a chunk of records and write to separate parquet file."""
    df = pd.DataFrame(records)
    
    # Clean data types for parquet compatibility
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
    
    # Handle large content fields by truncating if necessary
    if 'content' in df.columns:
        max_content_length = 100000  # 100KB max per content field
        df['content'] = df['content'].apply(
            lambda x: x[:max_content_length] if isinstance(x, str) and len(x) > max_content_length else x
        )
    
    # Write chunk to separate file
    chunk_file = temp_dir / f"chunk_{chunk_num}.parquet"
    df.to_parquet(chunk_file, engine='pyarrow', compression='snappy')
    
    return chunk_file

def merge_chunk_files(chunk_files: list, output_path: str) -> None:
    """Merge all chunk files into single parquet file."""
    import pyarrow.parquet as pq
    import pyarrow as pa
    
    # Read and concatenate all chunks
    dfs = []
    for chunk_file in chunk_files:
        df = pd.read_parquet(chunk_file)
        dfs.append(df)
    
    # Concatenate all dataframes
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Clean all object columns to string for parquet compatibility
    for col in combined_df.columns:
        if combined_df[col].dtype == 'object':
            combined_df[col] = combined_df[col].astype(str)
    
    # Write to final parquet file
    combined_df.to_parquet(output_path, engine='pyarrow', compression='snappy')

def main():
    print("=" * 70)
    print("CONVERTING TRAINING DATASETS TO PARQUET FORMAT")
    print("=" * 70)
    
    base_path = Path("/home/allaun/Documents/Research Stack/data/training_data")
    
    # Find all JSONL training datasets (Updated pattern to include all training variants)
    jsonl_files = list(base_path.glob("*training_dataset_*.jsonl"))
    
    print(f"\nFound {len(jsonl_files)} JSONL training datasets")
    
    total_records = 0
    
    for jsonl_file in jsonl_files:
        print(f"\nProcessing: {jsonl_file.name}")
        
        # Generate parquet filename
        parquet_file = jsonl_file.with_suffix('.parquet')
        
        # Convert
        records = convert_jsonl_to_parquet(str(jsonl_file), str(parquet_file))
        total_records += records
        
        if records > 0:
            print(f"✅ Successfully converted {records} records")
        else:
            print(f"❌ Conversion failed")
    
    print("\n" + "=" * 70)
    print(f"CONVERSION COMPLETE: {total_records} total records converted to Parquet")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
