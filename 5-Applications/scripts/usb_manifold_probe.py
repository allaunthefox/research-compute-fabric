#!/usr/bin/env python3
import subprocess
import json
import os
import re

# USB Manifold Probe
# Gathers system USB state and maps it to the Sovereign Manifold schema.
# Adheres to AGENTS.md 0.4 (Safe hardware interaction).

def get_lsusb_tree():
    try:
        output = subprocess.check_output(["lsusb", "-t"], text=True)
        return output
    except Exception:
        return ""

def get_lsusb_verbose():
    try:
        # Get basic verbose info to extract IDs and strings
        output = subprocess.check_output(["lsusb", "-v"], stderr=subprocess.DEVNULL, text=True)
        return output
    except Exception:
        return ""

def parse_usb_devices():
    devices = []
    # Use 'usb-devices' if available as it is easier to parse
    try:
        output = subprocess.check_output(["usb-devices"], text=True)
        device_blocks = output.strip().split("\n\n")
        for block in device_blocks:
            dev = {}
            for line in block.split("\n"):
                if line.startswith("T:"):
                    m = re.search(r"Bus=(\d+) Lev=(\d+) Prnt=(\d+) Port=(\d+) Cnt=(\d+) Dev#=\s*(\d+) Spd=([\d.]+)\s+MxCh=\s*(\d+)", line)
                    if m:
                        dev["bus"] = int(m.group(1))
                        dev["level"] = int(m.group(2))
                        dev["port"] = int(m.group(4))
                        dev["speed"] = m.group(7)
                elif line.startswith("D:"):
                    m = re.search(r"Ver=([\d.]+) Cls=([\da-fA-F]+)\(.*\) Sub=([\da-fA-F]+) Prot=([\da-fA-F]+) MxPS=(\d+)", line)
                    if m:
                        dev["bcdUSB"] = m.group(1)
                elif line.startswith("P:"):
                    m = re.search(r"Vendor=([\da-fA-F]+) ProdID=([\da-fA-F]+) Rev=([\d.]+)", line)
                    if m:
                        dev["idVendor"] = m.group(1)
                        dev["idProduct"] = m.group(2)
                elif line.startswith("S:"):
                    if "Manufacturer=" in line:
                        dev["manufacturer"] = line.split("Manufacturer=")[1]
                    elif "Product=" in line:
                        dev["product"] = line.split("Product=")[1]
                    elif "SerialNumber=" in line:
                        dev["serial"] = line.split("SerialNumber=")[1]
            if dev:
                devices.append(dev)
    except Exception:
        pass
    return devices

def main():
    print("[*] Probing USB Manifold...")
    devices = parse_usb_devices()
    
    manifold_state = []
    
    for dev in devices:
        # Map to PTOS Metadata
        is_root = dev.get("level") == 0
        speed = dev.get("speed", "0")
        
        # Heuristic: 20000M (USB 3.2x2) or 40000M (USB4) root hubs are definitely Type-C
        is_typec_candidate = is_root and (float(speed) >= 20000)
        
        # Map metrics to 14-axis ENE manifold
        link_stability = 1.0
        jitter_frustration = 0.0
        v0_val = int(link_stability * 65536)
        
        # Speed mapping (normalized to 10Gbps = 1.0)
        speed_val = 0
        if "10000" in speed: speed_val = 0x00010000
        elif "480" in speed: speed_val = 0x00008000
        elif "12" in speed: speed_val = 0x00002000
        
        # Jitter mapping
        v10_val = int(jitter_frustration * 65536)
        
        # SWUFE Pulse (Axis 11): |v0|^2 - 0.25*v0
        v11_val = (v0_val * v0_val // 65536) - (v0_val // 4)
        if v11_val < 0: v11_val = 0
        
        ptos = {
            "metadata": {
                "layer": "usb_hardware",
                "domain": "physical_interface",
                "condition": "active",
                "stage": "operational",
                "tier": "ROOT_HUB" if is_root else "DEVICE",
                "module": dev.get("product", "unknown"),
                "tags": ["typec_high_speed" if is_typec_candidate else "standard"]
            },
            "device": {
                "idVendor": int(dev.get("idVendor", "0"), 16),
                "idProduct": int(dev.get("idProduct", "0"), 16),
                "bcdUSB": int(float(dev.get("bcdUSB", "3.2") if float(dev.get("bcdUSB", "2.0")) > 2.0 else dev.get("bcdUSB", "2.0")) * 100),
                "manufacturer": dev.get("manufacturer", "unknown"),
                "product": dev.get("product", "unknown"),
                "serial": dev.get("serial", ""),
                "speed": f"{speed}M"
            },
            "capability": {
                "typeC": is_typec_candidate,
                "powerDelivery": is_typec_candidate,
                "altModes": ["DisplayPort", "Thunderbolt"] if is_typec_candidate else [],
                "usb4": float(speed) >= 40000
            },
            "metrics": {
                "powerDraw": {"val": 0},
                "linkStability": {"val": 0x7FFF}, # 1.0 (Stable) in Q0_16
                "jitterFrustration": {"val": 0},
                "bandwidthUtilization": {"val": 0}
            },
            "concept_vector": {
                "v0": {"val": v0_val},
                "v1": {"val": 0}, "v2": {"val": 0},
                "v3": {"val": speed_val},
                "v4": {"val": 0}, "v5": {"val": 0}, "v6": {"val": 0}, "v7": {"val": 0},
                "v8": {"val": 0}, "v9": {"val": 0},
                "v10": {"val": v10_val},
                "v11": {"val": v11_val},
                "v12": {"val": 0}, "v13": {"val": 0}
            },
            "ene_scalar": {"val": 0x00010000 if is_typec_candidate else 0x00008000},
            "active": True
        }
        manifold_state.append(ptos)

    # Output JSON-L for Lean ingestion
    output_path = "shared-shared-data/data/artifacts/usb_manifold_state.jsonl"
    with open(output_path, "w") as f:
        for item in manifold_state:
            f.write(json.dumps(item) + "\n")
            
    print(f"[+] Manifold state written to {output_path}")
    print(f"[*] Found {len(devices)} USB devices in manifold.")

if __name__ == "__main__":
    main()
