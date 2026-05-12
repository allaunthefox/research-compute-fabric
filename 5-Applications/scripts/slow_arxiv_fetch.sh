#!/bin/bash
# Slow arXiv fetcher: 1 request every 6s, 49 domains ≈ 5 minutes
# Writes directly to /dev/shm SQLite, copies back on completion

python3 /home/allaun/serial_arxiv.py 2>&1
