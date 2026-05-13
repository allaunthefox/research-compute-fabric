#!/usr/bin/env python3
"""
Research Stack Finance Manager (RSFM)
The actual finance program for managing personal_accounts.db and affirm_accounts.db.
"""

import sqlite3
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "shared-data" / "data" / "personal_accounts.db"
AFFIRM_DB_PATH = REPO_ROOT / "shared-data" / "data" / "affirm_accounts.db"

def get_connection(db_path):
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return None
    return sqlite3.connect(db_path)

def list_accounts():
    conn = get_connection(DB_PATH)
    if not conn: return
    
    print("\n--- Accounts Overview ---")
    query = "SELECT merchant, amount, status, type FROM accounts"
    df = pd.read_sql_query(query, conn)
    if df.empty:
        print("No accounts found.")
    else:
        print(df.to_string(index=False))
    conn.close()

def spending_summary(month=None):
    conn = get_connection(DB_PATH)
    if not conn: return
    
    print("\n--- Spending Summary by Category ---")
    # Use rocket_money_transactions for categorized spending
    query = "SELECT category, SUM(amount) as total FROM rocket_money_transactions"
    if month:
        query += f" WHERE date LIKE '{month}%'"
    query += " GROUP BY category ORDER BY total DESC"
    
    df = pd.read_sql_query(query, conn)
    if df.empty:
        print("No transactions found.")
    else:
        print(df.to_string(index=False))
        print(f"\nTotal: {df['total'].sum():.2f}")
    conn.close()

def search_transactions(query_term):
    conn = get_connection(DB_PATH)
    if not conn: return
    
    print(f"\n--- Search Results for '{query_term}' ---")
    # Search across main transactions and rocket money
    q1 = f"SELECT date, amount, description FROM transactions WHERE description LIKE '%{query_term}%'"
    q2 = f"SELECT date, amount, name as description FROM rocket_money_transactions WHERE name LIKE '%{query_term}%' OR custom_name LIKE '%{query_term}%'"
    
    df1 = pd.read_sql_query(q1, conn)
    df2 = pd.read_sql_query(q2, conn)
    
    combined = pd.concat([df1, df2]).sort_values(by='date', ascending=False)
    
    if combined.empty:
        print("No matches found.")
    else:
        print(combined.to_string(index=False))
    conn.close()

def affirm_summary():
    conn = get_connection(AFFIRM_DB_PATH)
    if not conn: return
    
    print("\n--- Affirm Loan Summary ---")
    # Assuming affirm_accounts.db has a similar structure or check its tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print("No data in Affirm database.")
    else:
        for (table_name,) in tables:
            print(f"\nTable: {table_name}")
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            print(df.head().to_string(index=False))
            
    conn.close()

def dashboard():
    print("\n" + "="*50)
    print("   RESEARCH STACK FINANCIAL DASHBOARD")
    print("="*50)
    list_accounts()
    spending_summary()
    print("\n" + "="*50)

def main():
    parser = argparse.ArgumentParser(description="Research Stack Finance Manager")
    parser.add_argument("--dashboard", action="store_true", help="Show full financial dashboard")
    parser.add_argument("--accounts", action="store_true", help="Show accounts overview")
    parser.add_argument("--summary", nargs="?", const="all", help="Show spending summary for a month (format: YYYY-MM) or 'all' for total")
    parser.add_argument("--search", metavar="TERM", help="Search transactions for a term")
    parser.add_argument("--affirm", action="store_true", help="Show Affirm loan status")
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1 or args.dashboard:
        dashboard()
        if not args.dashboard: sys.exit(0)
        
    if args.accounts:
        list_accounts()
    if args.summary:
        if args.summary == "all":
            spending_summary()
        else:
            spending_summary(args.summary)
    if args.search:
        search_transactions(args.search)
    if args.affirm:
        affirm_summary()



if __name__ == "__main__":
    main()
