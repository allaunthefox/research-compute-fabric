#!/usr/bin/env python3
import argparse
import os
import select
import sys
import termios
import time
import tty
import subprocess

# Adaptive USB Fabric Controller
# Orchestrates the Tang Nano 9K FPGA and displays "Fabric Tension" telemetry.
# Derived from monitor_uart.py and HachimojiPipeline.lean

BAUD_FLAGS = {
    9600: termios.B9600,
    115200: termios.B115200,
}

def configure_uart(port, baud):
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    attrs = termios.tcgetattr(fd)
    baud_flag = BAUD_FLAGS[baud]
    attrs[4] = baud_flag
    attrs[5] = baud_flag
    attrs[2] |= termios.CLOCAL | termios.CREAD
    attrs[2] &= ~termios.CSTOPB
    attrs[2] &= ~termios.PARENB
    attrs[2] &= ~termios.CSIZE
    attrs[2] |= termios.CS8
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    return fd, old

def flash_fpga(bitstream):
    print(f"[*] Burning bitstream: {bitstream}")
    cmd = ["openFPGALoader", "-b", "tangnano9k", bitstream]
    try:
        subprocess.run(cmd, check=True)
        print("[+] Flash successful.")
    except Exception as e:
        print(f"[-] Flash failed: {e}")

def render_tension(stress_val):
    # stress_val is Q16.16 mapped to 0-65535
    width = 40
    level = int((stress_val / 65535.0) * width)
    bar = "█" * level + "░" * (width - level)
    return f" Tension: [{bar}] {stress_val:5d}"

def decode_cmyk(state_byte):
    states = {0: "K (Fast)   ", 1: "C (Monitor)", 2: "M (Verify) ", 3: "Y (Prune)  "}
    return states.get(state_byte & 0x3, "UNKNOWN    ")

def main():
    parser = argparse.ArgumentParser(description="Adaptive USB Fabric Controller")
    parser.add_argument("--port", default="/dev/ttyUSB1")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--burn", action="store_true", help="Flash the FPGA before monitoring")
    parser.add_argument("--bitstream", default="4-Infrastructure/hardware/adaptive_fabric_connector.fs")
    args = parser.parse_args()

    if args.burn:
        flash_fpga(args.bitstream)

    try:
        fd, old_attrs = configure_uart(args.port, args.baud)
    except Exception as e:
        print(f"[-] Could not open UART: {e}")
        return 1

    print(f"[*] Monitoring Adaptive Fabric on {args.port}...")
    print("    Press Ctrl+C to stop.")
    
    try:
        while True:
            ready, _, _ = select.select([fd], [], [], 0.1)
            if not ready:
                continue
            
            data = os.read(fd, 1024)
            for byte in data:
                # Simple protocol: 
                # Bit 7-6: CMYK state
                # Bit 5-0: Coarse stress level
                state = (byte >> 6) & 0x3
                stress_coarse = (byte & 0x3F) << 10 # Scale to 16-bit
                
                sys.stdout.write(f"\r[FABRIC] State: {decode_cmyk(state)} | {render_tension(stress_coarse)}")
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        print("\n[*] Stopping...")
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old_attrs)
        os.close(fd)

if __name__ == "__main__":
    main()
