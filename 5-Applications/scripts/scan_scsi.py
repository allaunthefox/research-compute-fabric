import subprocess
import sys

def scan_opcodes(dev, opcode_base):
    print(f"Scanning Vendor Opcodes for {dev} starting with {hex(opcode_base)}...")
    
    for sub in range(0x100):
        # Construct 12-byte CDB
        cdb = [opcode_base, sub, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        cdb_str = " ".join([f"{b:02x}" for b in cdb])
        
        cmd = ["sudo", "sg_raw", "-r", "8", dev] + cdb_str.split()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1)
            output = result.stdout + result.stderr
            
            if "Illegal Request" not in output and "Invalid field in cdb" not in output:
                print(f"[!] POTENTIAL COMMAND FOUND: {cdb_str}")
                print(output)
            
        except subprocess.TimeoutExpired:
            print(f"[?] Timeout at {cdb_str}")
        except Exception as e:
            pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scan_scsi.py <device>")
    else:
        # Scan common vendor bases: 0xEF, 0xF0, 0xF1, 0x06, 0x8A, 0xBE
        for base in [0xEF, 0xF0, 0xF1, 0x06, 0x8A, 0xBE]:
            scan_opcodes(sys.argv[1], base)
