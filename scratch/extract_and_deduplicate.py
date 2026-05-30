#!/usr/bin/env python3
import os
import sys
import zipfile
import subprocess
import hashlib
import random
from pathlib import Path

# Paths
GDRIVE_DIR = Path("/home/allaun/gdrive")
TAKEOUT_DIR = GDRIVE_DIR / "Takeout"
TARGET_DIR = Path("/home/allaun/Takeout_extracted")

def get_gdrive_md5(gdrive_rel_path):
    """Get the MD5 hash of a file on Google Drive using rclone md5sum."""
    rclone_path = f"gdrive:{gdrive_rel_path}"
    try:
        res = subprocess.run(
            ["rclone", "md5sum", rclone_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = res.stdout.strip().split()
            if parts:
                return parts[0].strip()
    except subprocess.TimeoutExpired:
        pass
    except Exception as e:
        print(f"Error querying rclone md5sum: {e}")
    return None

def check_file_duplicate(zip_ref, info):
    """Check if a file in the zip is a duplicate of a file in Google Drive."""
    path_parts = Path(info.filename).parts
    if len(path_parts) > 1 and path_parts[0] == "Takeout":
        if len(path_parts) > 2 and path_parts[1] == "Drive":
            gdrive_rel = Path(*path_parts[2:])
        else:
            gdrive_rel = Path(*path_parts[1:])
    else:
        gdrive_rel = Path(info.filename)
    
    gdrive_file = GDRIVE_DIR / gdrive_rel
    
    if gdrive_file.exists():
        try:
            gdrive_size = gdrive_file.stat().st_size
            if gdrive_size == info.file_size:
                # Sizes match, verify with MD5
                remote_md5 = get_gdrive_md5(str(gdrive_rel))
                if remote_md5:
                    hasher = hashlib.md5()
                    with zip_ref.open(info) as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
                    zip_md5 = hasher.hexdigest()
                    if zip_md5 == remote_md5:
                        return True, gdrive_rel
        except Exception as e:
            print(f"Error checking {gdrive_file}: {e}")
            
    return False, gdrive_rel

def run_metaprobe(zip_path, zip_ref, infolist):
    """
    Run a windowed metaprobe (sampling test) on the ZIP.
    Returns True if the entire ZIP is highly likely to be 100% redundant.
    """
    files_only = [info for info in infolist if not info.is_dir()]
    total_files = len(files_only)
    
    if total_files == 0:
        return True # Empty zip is redundant/trivial
        
    # Sample size: 5% of files, min 10, max 30
    sample_size = min(max(int(total_files * 0.05), 10), 30)
    sample_size = min(sample_size, total_files)
    
    random.seed(42) # Deterministic sampling
    sample = random.sample(files_only, sample_size)
    
    print(f"  [Metaprobe] Sampling {sample_size}/{total_files} files for redundancy...")
    
    duplicates = 0
    for idx, info in enumerate(sample):
        is_dup, rel_path = check_file_duplicate(zip_ref, info)
        if is_dup:
            duplicates += 1
        else:
            print(f"  [Metaprobe] Unique file found: {info.filename}")
            return False # Found a unique file, must process this zip
            
    # If all sampled files are duplicates
    if duplicates == sample_size:
        print(f"  [Metaprobe] 100% redundancy in sample window. Trusting and SKIPPING zip.")
        return True
        
    return False

def process_zip(zip_path, dry_run=False):
    print(f"\nProcessing {zip_path.name}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            infolist = zip_ref.infolist()
            
            # Run metaprobe sampling check first
            is_redundant = run_metaprobe(zip_path, zip_ref, infolist)
            if is_redundant:
                print(f"SKIPPED (Metaprobe: 100% redundant): {zip_path.name}")
                return
                
            # If not redundant, proceed with extracting unique files
            print(f"  Metaprobe failed (unique files present). Running full extraction...")
            total_files = len(infolist)
            redundant_count = 0
            unique_count = 0
            skipped_dirs = 0
            
            for idx, info in enumerate(infolist):
                if info.is_dir():
                    skipped_dirs += 1
                    continue
                
                is_duplicate, gdrive_rel = check_file_duplicate(zip_ref, info)
                
                if is_duplicate:
                    redundant_count += 1
                    if idx % 100 == 0 or idx == total_files - 1:
                        print(f"  Progress: Checked {idx+1}/{total_files} | Duplicates: {redundant_count} | Unique: {unique_count}")
                else:
                    unique_count += 1
                    target_file = TARGET_DIR / info.filename
                    print(f"  [UNIQUE] {info.filename} -> {target_file}")
                    if not dry_run:
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(info) as source, open(target_file, "wb") as target:
                            target.write(source.read())
            
            print(f"Finished {zip_path.name}: Duplicates: {redundant_count}, Unique: {unique_count}")
    except Exception as e:
        print(f"Error reading zip {zip_path.name}: {e}")

def main():
    dry_run = "--dry-run" in sys.argv
    single_zip = None
    for arg in sys.argv[1:]:
        if arg.endswith(".zip"):
            single_zip = arg
            break
            
    if dry_run:
        print("Running in DRY RUN mode.")
        
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    if single_zip:
        zip_path = TAKEOUT_DIR / single_zip
        if zip_path.exists():
            process_zip(zip_path, dry_run=dry_run)
        else:
            print(f"Zip file {zip_path} not found.")
            sys.exit(1)
    else:
        # Find all zip files
        zips = sorted(list(TAKEOUT_DIR.glob("*.zip")))
        if not zips:
            print(f"No zip files found in {TAKEOUT_DIR}")
            sys.exit(1)
        print(f"Found {len(zips)} zip files to process.")
        for zip_path in zips:
            process_zip(zip_path, dry_run=dry_run)

if __name__ == "__main__":
    main()
