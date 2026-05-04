"""Minimal shim for attestation scripts."""
import sqlite3
from pathlib import Path

DB_PATH = Path("/home/allaun/Documents/Research Stack/data/math_entities.db")

class SwarmAPISystem:
    """Provides sqlite3 connection to math_entities database."""
    def __init__(self):
        self.conn = None
        try:
            self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except Exception:
            self.conn = None
