#!/usr/bin/env python3
import os
import subprocess
import time
import requests
from dotenv import load_dotenv

load_dotenv()

import sys

# Configuration
I2P_SERVICE_NAME = "i2p"  # or "i2p-router" depending on system
FORGEJO_I2P_URL = "http://fshn3nnomefzjxp77zbotyjr2ageh54jq6nvgpzmpuuqvewdzvfa.b32.i2p"
MAX_RETRIES = 3
TSDM_ROUTING_ENDPOINT = "http://localhost:3000/tsdm/packet"

def route_tsdm_packet(hex_payload):
    """Routes a received TSDM compressed packet to the local manifold node."""
    try:
        if not hex_payload.startswith("0xTS"):
            print("[WARDEN] Ignoring non-TSDM packet.")
            return False
            
        print(f"[WARDEN] Routing TSDM Packet ({len(hex_payload)} bytes) to local node...")
        # In a full implementation, this would send over a raw socket or HTTP to the server.js handler
        res = requests.post(TSDM_ROUTING_ENDPOINT, json={"payload": hex_payload})
        if res.status_code == 200:
            print("[WARDEN] TSDM Packet successfully blitted.")
            return True
        else:
            print(f"[WARDEN] TSDM Routing failed: {res.status_code}")
            return False
    except Exception as e:
        print(f"[WARDEN] TSDM Error: {e}")
        return False


def check_i2p_service():
    """Checks if the i2p system service is running."""
    try:
        result = subprocess.run(["systemctl", "is-active", I2P_SERVICE_NAME], capture_output=True, text=True)
        return result.stdout.strip() == "active"
    except Exception as e:
        print(f"[WARDEN] Error checking systemd: {e}")
        return False

def attempt_restart():
    """Attempts to restart the i2p service."""
    print(f"[WARDEN] i2p down. Attempting restart...")
    try:
        subprocess.run(["sudo", "systemctl", "restart", I2P_SERVICE_NAME], check=True)
        time.sleep(10) # Wait for router to warm up
        return check_i2p_service()
    except Exception as e:
        print(f"[WARDEN] Restart failed: {e}")
        return False

def alert_user(message):
    """Alerts the user via console and potentially other channels."""
    print(f"\n[!!! WARDEN ALERT !!!] {message}")
    # Integration with Linear or Forgejo could go here
    # For now, we use a high-visibility console alert

def main():
    print("[WARDEN] i2p Enforcement Active.")
    is_running = check_i2p_service()
    
    if not is_running:
        success = False
        for i in range(MAX_RETRIES):
            print(f"[WARDEN] Retry {i+1}/{MAX_RETRIES}...")
            if attempt_restart():
                print("[WARDEN] i2p successfully recovered.")
                success = True
                break
            time.sleep(5)
            
        if not success:
            alert_user("i2p Router is FATALLY OFFLINE. Manual intervention required.")
            # Optional: push to Forgejo if Tailscale is up
            return False
    else:
        print("[WARDEN] i2p is healthy.")
    return True

if __name__ == "__main__":
    main()
