#!/usr/bin/env python3
"""
credential_loader.py — Load credentials from RDS credential_store into env.

Usage:
    from credential_loader import load_credential
    key = load_credential('quandela-api-key')
    
    # Or via CLI:
    #   python3 credential_loader.py quandela-api-key
    #   source <(python3 credential_loader.py --export quandela-api-key)
"""

import os, sys, subprocess, json

RDS_HOST = None
RDS_USER = None

def _init_rds():
    global RDS_HOST, RDS_USER
    # Try bashrc first
    bashrc = os.path.expanduser('~/.bashrc')
    if os.path.exists(bashrc):
        with open(bashrc) as f:
            for line in f:
                if line.startswith('export RDS_HOST='):
                    RDS_HOST = line.split('"')[1] if '"' in line else line.split('=')[1].strip()
                elif line.startswith('export RDS_USER='):
                    RDS_USER = line.split('"')[1] if '"' in line else line.split('=')[1].strip()
    if not RDS_HOST or not RDS_USER:
        raise RuntimeError("RDS_HOST and RDS_USER must be set in ~/.bashrc")

def _get_auth_token():
    result = subprocess.run(
        ['aws', 'rds', 'generate-db-auth-token',
         '--hostname', RDS_HOST, '--port', '5432', '--username', RDS_USER],
        capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"AWS CLI error: {result.stderr}")
    return result.stdout.strip()

def load_credential(pkg: str, password: str = None) -> str:
    """Load a credential from the RDS credential_store."""
    _init_rds()
    token = _get_auth_token()
    import psycopg2
    conn = psycopg2.connect(host=RDS_HOST, user=RDS_USER, password=token, dbname='postgres')
    cur = conn.cursor()
    if password is None:
        password = RDS_HOST  # Default encryption key
    cur.execute(
        "SELECT pgp_sym_decrypt(encrypted_payload, %s) FROM credential_store.credentials WHERE pkg = %s",
        (password, pkg))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        raise KeyError(f"Credential '{pkg}' not found")
    return row[0]

def list_credentials() -> list[dict]:
    """List all credential packages."""
    _init_rds()
    token = _get_auth_token()
    import psycopg2
    conn = psycopg2.connect(host=RDS_HOST, user=RDS_USER, password=token, dbname='postgres')
    cur = conn.cursor()
    cur.execute(
        "SELECT id, pkg, provider, classification, created_at, is_active "
        "FROM credential_store.credentials WHERE is_active = true ORDER BY pkg")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {'id': r[0], 'pkg': r[1], 'provider': r[2], 'classification': r[3],
         'created_at': str(r[4]), 'active': r[5]}
        for r in rows]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        creds = list_credentials()
        print("Available credentials:")
        for c in creds:
            print(f"  {c['pkg']:30s} provider={c['provider']:15s} active={c['active']}")
        sys.exit(0)
    if sys.argv[1] == '--export' and len(sys.argv) >= 3:
        key = load_credential(sys.argv[2])
        print(f"export {sys.argv[2].upper().replace('-', '_')}='{key}'")
    else:
        key = load_credential(sys.argv[1])
        print(key)
