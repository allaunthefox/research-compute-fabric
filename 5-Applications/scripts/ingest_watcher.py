#!/usr/bin/env python3
import time
import os
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
WATCH_DIR = "shared-data/data/ingested"
INGEST_URL = "http://localhost:3000/ingest"

class IngestHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            self.process(event.src_path)

    def process(self, file_path):
        filename = os.path.basename(file_path)
        if filename.endswith(".old") or filename.startswith("."):
            return

        print(f"[*] New file detected: {filename}")
        time.sleep(1) # Wait for file to be fully written

        try:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
            
            payload = {
                "title": f"WATCHER: {filename}",
                "body": content,
                "kind": "document",
                "tags": ["automated-watch", os.path.splitext(filename)[1][1:]],
                "target": "ene"
            }

            resp = requests.post(INGEST_URL, json=payload)
            if resp.status_code == 200:
                print(f"    ✅ INGESTED: {filename}")
                # Rename to .old to avoid re-ingesting on service restart
                os.rename(file_path, file_path + ".old")
            else:
                print(f"    ❌ FAILED: {resp.text}")
        except Exception as e:
            print(f"    ⚠️ ERROR: {str(e)}")

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR)

    event_handler = IngestHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    print(f"[+] Ingest Watcher started on {WATCH_DIR}...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
