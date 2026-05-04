import usb.core
import usb.util
import struct
import time

# Chipsbank / ITE CBM2199
# VID: 0x048d, PID: 0x1234
VID = 0x048d
PID = 0x1234

class ChipsbankBOT:
    def __init__(self, vid, pid):
        self.dev = usb.core.find(idVendor=vid, idProduct=pid)
        if self.dev is None:
            raise ValueError("Device not found")

        # Detach kernel driver if necessary (Linux)
        if self.dev.is_kernel_driver_active(0):
            try:
                self.dev.detach_kernel_driver(0)
                print("[*] Detached kernel driver")
            except usb.core.USBError as e:
                print(f"[!] Could not detach driver: {e}")

        # Set configuration
        try:
            self.dev.set_configuration()
        except usb.core.USBError as e:
             print(f"[!] Could not set configuration: {e}")

        cfg = self.dev.get_active_configuration()
        intf = cfg[(0,0)]

        # Find Bulk endpoints
        self.ep_out = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
        self.ep_in = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
        
        if not self.ep_out or not self.ep_in:
            raise ValueError("Endpoints not found")

        self.tag = 0xDEADBEEF

    def send_cbw(self, cmd, data_len, direction_in=True):
        """Constructs and sends a 31-byte Command Block Wrapper."""
        self.tag += 1
        flags = 0x80 if direction_in else 0x00
        # Signature 'USBC', Tag, DataLen, Flags, LUN, CmdLen, CmdBlock(16 bytes)
        cbw = struct.pack("<4sIIBB B 16s", b"USBC", self.tag, data_len, flags, 0, len(cmd), cmd.ljust(16, b'\x00'))
        self.ep_out.write(cbw)
        return self.tag

    def receive_csw(self, expected_tag):
        """Reads the 13-byte Command Status Wrapper."""
        try:
            data = self.ep_in.read(13, timeout=2000)
            if len(data) < 13:
                print(f"[!] CSW truncated: {len(data)} bytes")
                return -1
            # Signature 'USBS', Tag, Residue, Status
            sig, tag, residue, status = struct.unpack("<4sIIB", data)
            if sig != b"USBS":
                print(f"[!] CSW Invalid Signature: {sig}")
            if tag != expected_tag:
                print(f"[!] CSW Tag Mismatch: {tag} (Expected {expected_tag})")
            return status
        except usb.core.USBError as e:
            print(f"[!] CSW Read Error: {e}")
            return -1

    def execute_command(self, cmd, data_len, direction_in=True):
        """Full BOT transaction: CBW -> Data -> CSW."""
        try:
            tag = self.send_cbw(cmd, data_len, direction_in)
            
            payload = None
            if data_len > 0:
                if direction_in:
                    payload = self.ep_in.read(data_len, timeout=2000)
                else:
                    # For OUT commands, you would send data here
                    pass 
            
            status = self.receive_csw(tag)
            return status, payload
        except usb.core.USBError as e:
            print(f"[!] Command Execution Error: {e}")
            # Try to clear stall
            try:
                self.dev.clear_halt(self.ep_in.bEndpointAddress)
                self.dev.clear_halt(self.ep_out.bEndpointAddress)
            except: pass
            return -1, None

    def scsi_inquiry(self):
        """Standard SCSI Inquiry (0x12)."""
        print("[*] Sending SCSI Inquiry...")
        cmd = struct.pack("B B B B B B", 0x12, 0, 0, 0, 36, 0)
        status, data = self.execute_command(cmd, 36)
        if status == 0 and data:
            data_bytes = data.tobytes() if hasattr(data, 'tobytes') else bytes(data)
            vendor = data_bytes[8:16].decode('ascii', 'ignore').strip()
            product = data_bytes[16:32].decode('ascii', 'ignore').strip()
            rev = data_bytes[32:36].decode('ascii', 'ignore').strip()
            print(f"  [+] Success! Vendor: {vendor}, Product: {product}, Rev: {rev}")
        return data

    def probe_vendor_command(self, opcode, sub, desc):
        print(f"[*] Probing Vendor Command: {desc} ({hex(opcode)} {hex(sub)})...")
        # Chipsbank style: [Opcode, Sub, ...]
        cmd = struct.pack("B B 14x", opcode, sub)
        status, data = self.execute_command(cmd, 36) # Try 36 bytes for info
        if status == 0 and data:
            data_bytes = data.tobytes() if hasattr(data, 'tobytes') else bytes(data)
            print(f"  [+] Success! Data: {data_bytes.hex().upper()}")
            # Try to decode as ASCII
            try:
                print(f"  [+] ASCII: {data_bytes.decode('ascii', 'ignore')}")
            except: pass
        else:
            print(f"  [-] Command rejected or failed (Status: {status})")

if __name__ == "__main__":
    try:
        bot = ChipsbankBOT(VID, PID)
        bot.scsi_inquiry()
        
        # Test common vendor entrance points
        # Chipsbank: 0xEF, 0xF0, 0xF1, 0x06
        # ITE: 0x8A, 0xBE, 0xFE
        probes = [
            (0xEF, 0xF1, "Chipsbank Get Info"),
            (0xEF, 0x06, "Chipsbank Read FID"),
            (0xF0, 0x01, "Chipsbank Alt Get Info"),
            (0x8A, 0x01, "ITE Get Info"),
            (0xBE, 0x01, "ITE Read FID"),
            (0xFE, 0x00, "Generic Vendor Inquiry")
        ]
        
        for op, sub, desc in probes:
            bot.probe_vendor_command(op, sub, desc)
            time.sleep(0.5)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("[*] Re-attaching kernel driver...")
        # Re-attach logic would go here if needed, but dev.reset() is easier
