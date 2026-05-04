#!/usr/bin/env python3
"""
Consolidate All Language Databases for Training Data

This script pulls in every available language database in the codebase and
consolidates them into a unified training dataset for NII cores to become
n-semantic morphic.
"""

import sys
import json
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import hashlib

def extract_sqlite_data(db_path: str) -> List[Dict[str, Any]]:
    """Extract data from SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        data = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    key = columns[i]
                    # Convert bytes to string for JSON serialization
                    if isinstance(value, bytes):
                        try:
                            row_dict[key] = value.decode('utf-8', errors='ignore')
                        except:
                            row_dict[key] = str(value)
                    else:
                        row_dict[key] = value
                row_dict['_source_db'] = str(db_path)
                row_dict['_source_table'] = table_name
                data.append(row_dict)
        
        conn.close()
        return data
    except Exception as e:
        print(f"Error extracting from {db_path}: {e}")
        return []

def extract_jsonl_data(jsonl_path: str) -> List[Dict[str, Any]]:
    """Extract data from JSONL file."""
    try:
        data = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and line.startswith('{'):
                    try:
                        record = json.loads(line)
                        record['_source_file'] = str(jsonl_path)
                        data.append(record)
                    except json.JSONDecodeError:
                        # Skip non-JSON lines
                        continue
        return data
    except Exception as e:
        print(f"Error extracting from {jsonl_path}: {e}")
        return []

def extract_json_data(json_path: str) -> List[Dict[str, Any]]:
    """Extract data from JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for record in data:
                    record['_source_file'] = str(json_path)
                return data
            elif isinstance(data, dict):
                data['_source_file'] = str(json_path)
                return [data]
            else:
                return []
    except Exception as e:
        print(f"Error extracting from {json_path}: {e}")
        return []

def consolidate_all_databases(base_path: str) -> Dict[str, Any]:
    """Consolidate all available language databases."""
    print("=" * 70)
    print("CONSOLIDATING ALL LANGUAGE DATABASES FOR TRAINING DATA")
    print("=" * 70)
    
    base_path = Path(base_path)
    
    consolidated_data = {
        'timestamp': datetime.now().isoformat(),
        'sources': {
            'sqlite_databases': [],
            'jsonl_files': [],
            'json_files': [],
            'other_files': []
        },
        'data': {
            'sqlite_data': [],
            'jsonl_data': [],
            'json_data': []
        },
        'statistics': {
            'total_records': 0,
            'sqlite_records': 0,
            'jsonl_records': 0,
            'json_records': 0,
            'unique_sources': 0
        }
    }
    
    # 1. Extract SQLite databases
    print("\n[1/4] Extracting SQLite databases...")
    db_files = list(base_path.rglob("*.db"))
    print(f"Found {len(db_files)} database files")
    
    for db_file in db_files:
        if 'ene' in db_file.name.lower():
            # Skip ENE databases (credential management, not language data)
            continue
        
        print(f"  Processing: {db_file.name}")
        data = extract_sqlite_data(str(db_file))
        if data:
            consolidated_data['sources']['sqlite_databases'].append(str(db_file))
            consolidated_data['data']['sqlite_data'].extend(data)
            consolidated_data['statistics']['sqlite_records'] += len(data)
            print(f"    Extracted {len(data)} records")
    
    # 2. Extract JSONL files
    print("\n[2/4] Extracting JSONL files...")
    jsonl_files = list(base_path.rglob("*.jsonl"))
    print(f"Found {len(jsonl_files)} JSONL files")
    
    for jsonl_file in jsonl_files:
        print(f"  Processing: {jsonl_file.name}")
        data = extract_jsonl_data(str(jsonl_file))
        if data:
            consolidated_data['sources']['jsonl_files'].append(str(jsonl_file))
            consolidated_data['data']['jsonl_data'].extend(data)
            consolidated_data['statistics']['jsonl_records'] += len(data)
            print(f"    Extracted {len(data)} records")
    
    # 3. Extract JSON files
    print("\n[3/4] Extracting JSON files...")
    json_files = list(base_path.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files")
    
    for json_file in json_files:
        # Skip certain JSON files that aren't language data
        skip_patterns = ['ene_', 'dag_', 'benchmark', 'codon_table', 'connectome']
        if any(pattern in json_file.name.lower() for pattern in skip_patterns):
            continue
        
        print(f"  Processing: {json_file.name}")
        data = extract_json_data(str(json_file))
        if data:
            consolidated_data['sources']['json_files'].append(str(json_file))
            consolidated_data['data']['json_data'].extend(data)
            consolidated_data['statistics']['json_records'] += len(data)
            print(f"    Extracted {len(data)} records")
    
    # 4. Calculate statistics
    print("\n[4/4] Calculating statistics...")
    consolidated_data['statistics']['total_records'] = (
        consolidated_data['statistics']['sqlite_records'] +
        consolidated_data['statistics']['jsonl_records'] +
        consolidated_data['statistics']['json_records']
    )
    consolidated_data['statistics']['unique_sources'] = (
        len(consolidated_data['sources']['sqlite_databases']) +
        len(consolidated_data['sources']['jsonl_files']) +
        len(consolidated_data['sources']['json_files'])
    )
    
    print(f"\nConsolidation Statistics:")
    print(f"  Total Records: {consolidated_data['statistics']['total_records']}")
    print(f"  SQLite Records: {consolidated_data['statistics']['sqlite_records']}")
    print(f"  JSONL Records: {consolidated_data['statistics']['jsonl_records']}")
    print(f"  JSON Records: {consolidated_data['statistics']['json_records']}")
    print(f"  Unique Sources: {consolidated_data['statistics']['unique_sources']}")
    
    return consolidated_data

def save_consolidated_data(consolidated_data: Dict[str, Any], output_path: str):
    """Save consolidated data to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save full consolidated data
    full_output = f"{output_path}/language_databases_consolidated_{timestamp}.json"
    with open(full_output, 'w', encoding='utf-8') as f:
        json.dump(consolidated_data, f, indent=2)
    print(f"\n✅ Full consolidated data saved to: {full_output}")
    
    # Save training-ready dataset (flattened)
    training_data = []
    training_data.extend(consolidated_data['data']['sqlite_data'])
    training_data.extend(consolidated_data['data']['jsonl_data'])
    training_data.extend(consolidated_data['data']['json_data'])
    
    training_output = f"{output_path}/training_dataset_{timestamp}.jsonl"
    with open(training_output, 'w', encoding='utf-8') as f:
        for record in training_data:
            f.write(json.dumps(record) + '\n')
    print(f"✅ Training dataset saved to: {training_output}")
    
    # Save statistics summary
    stats_output = f"{output_path}/consolidation_statistics_{timestamp}.json"
    with open(stats_output, 'w', encoding='utf-8') as f:
        json.dump(consolidated_data['statistics'], f, indent=2)
    print(f"✅ Statistics saved to: {stats_output}")
    
    return full_output, training_output, stats_output

def main():
    base_path = "/home/allaun/Research Stack"
    output_path = "/home/allaun/Documents/Research Stack/data/training_data"
    
    # Create output directory
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    # Consolidate all databases
    consolidated_data = consolidate_all_databases(base_path)
    
    # Save consolidated data
    save_consolidated_data(consolidated_data, output_path)
    
    print("\n" + "=" * 70)
    print("LANGUAGE DATABASE CONSOLIDATION COMPLETE")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
