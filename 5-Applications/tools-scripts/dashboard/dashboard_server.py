#!/usr/bin/env python3
import os
import time
import json
import threading
import urllib.parse
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8888
LOG_FILE = "lambda_trace.jsonl"

class SSEHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Initial catch-up
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    f.seek(0, os.SEEK_END)
                    file_size = f.tell()
                    f.seek(max(0, file_size - 10000), os.SEEK_SET) 
                    lines = f.readlines()
                    for line in lines[-20:]:
                        self.wfile.write(f"data: {line.strip()}\n\n".encode())
                        self.wfile.flush()

            # Tail the file
            with open(LOG_FILE, 'r') as f:
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if line:
                        self.wfile.write(f"data: {line.strip()}\n\n".encode())
                        self.wfile.flush()
                    else:
                        time.sleep(0.5)
        
        elif self.path.startswith('/api/search'):
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            q = query_params.get('q', [''])[0]
            
            DB_PATH = "/home/allaun/Documents/Research Stack/data/substrate_index.db"
            results = []
            if os.path.exists(DB_PATH):
                try:
                    domain = query_params.get('domain', ['LINEAR'])[0]
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT pkg, description, tags 
                        FROM packages_fts 
                        WHERE domain = ? AND (description MATCH ? OR pkg MATCH ?)
                        LIMIT 50
                    """, (domain, f"{q}*", f"{q}*"))
                    for row in cur.fetchall():
                        results.append({
                            "id": row[0],
                            "description": row[1],
                            "tags": row[2]
                        })
                    conn.close()
                except Exception as e:
                    print(f"Search error: {e}")

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())

        else:
            if self.path == '/':
                self.path = '/index.html'
            
            original_path = self.path
            self.path = '/dashboard' + original_path
            
            if not os.path.exists('.' + self.path):
                self.path = original_path

            return super().do_GET()

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, SSEHandler)
    print(f"[🛡️ DASHBOARD SERVER] Online at http://localhost:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            pass
    run_server()
