#!/usr/bin/env python3
"""Test script for RAM loopback writer functionality"""

import sys
import os
import json
import time
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scripts')

from enhanced_integrated_swarm import RAMLoopbackWriter

def test_ram_loopback_writer():
    """Test RAM loopback writer functionality"""
    
    print("[TEST] Testing RAM loopback writer...")
    
    # Create RAM loopback writer
    writer = RAMLoopbackWriter()
    
    # Test 1: Write improvement to RAM
    print("\n[TEST 1] Writing improvement to RAM...")
    writer.write_improvement(
        agent_id=1,
        improvement_type="test_improvement",
        improvement_data={
            'description': 'Test improvement for RAM loopback',
            'value': 42.0,
            'status': 'success'
        }
    )
    print("  ✓ Improvement written to RAM")
    
    # Test 2: Read improvements from RAM
    print("\n[TEST 2] Reading improvements from RAM...")
    improvements = writer.read_improvements(agent_id=1)
    print(f"  ✓ Read {len(improvements)} improvements from RAM")
    if improvements:
        print(f"  Latest improvement: {improvements[-1]['type']}")
    
    # Test 3: Sync to disk
    print("\n[TEST 3] Syncing to disk...")
    writer.sync_to_disk()
    print("  ✓ Synced to disk")
    
    # Test 4: Verify disk file exists and contains data
    print("\n[TEST 4] Verifying disk file...")
    disk_path = Path(writer.disk_path)
    if disk_path.exists():
        with open(disk_path, 'r') as f:
            disk_data = json.load(f)
        print(f"  ✓ Disk file exists with {len(disk_data)} improvements")
    else:
        print("  ✗ Disk file does not exist")
        return False
    
    # Test 5: Write multiple improvements and test buffer
    print("\n[TEST 5] Writing multiple improvements...")
    for i in range(5):
        writer.write_improvement(
            agent_id=2,
            improvement_type=f"batch_improvement_{i}",
            improvement_data={
                'batch_index': i,
                'value': i * 10.0
            }
        )
    print(f"  ✓ Wrote 5 improvements, buffer size: {len(writer.improvements_buffer)}")
    
    # Test 6: Get improvement summary
    print("\n[TEST 6] Getting improvement summary...")
    summary = writer.get_improvement_summary()
    print(f"  ✓ Summary:")
    print(f"    Total improvements: {summary['total_improvements']}")
    print(f"    Type counts: {summary['type_counts']}")
    print(f"    RAM path: {summary['ram_path']}")
    print(f"    Disk path: {summary['disk_path']}")
    print(f"    Buffer size: {summary['buffer_size']}")
    
    # Test 7: Verify RAM files exist
    print("\n[TEST 7] Verifying RAM files...")
    ram_dir = Path(writer.ram_path)
    if ram_dir.exists():
        ram_files = list(ram_dir.glob("*.json"))
        print(f"  ✓ RAM directory exists with {len(ram_files)} files")
    else:
        print("  ✗ RAM directory does not exist")
        return False
    
    print("\n[SUCCESS] All RAM loopback writer tests passed!")
    return True

if __name__ == "__main__":
    success = test_ram_loopback_writer()
    sys.exit(0 if success else 1)
