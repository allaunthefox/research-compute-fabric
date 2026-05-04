import usb.core
import usb.util
import sys

VENDOR_ID = 0x048d
PRODUCT_ID = 0x1234

def probe_backdoor():
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        print("Device not found")
        return

    print(f"Found Device: {hex(VENDOR_ID)}:{hex(PRODUCT_ID)}")
    
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)

    # bRequest = 0x06 (Execute Vendor Command)
    # wValue = Command Code
    # wIndex = Sub-command
    # wLength = Data Length
    
    commands = [
        (0x06, 0x01, 0, 6, "Read NAND ID"),
        (0x06, 0x01, 0x01, 6, "Read NAND ID Alt"),
        (0x01, 0, 0, 1, "Read Register 0"),
        (0x02, 0, 0, 1, "Read Register 0 Alt"),
    ]

    for req, val, idx, length, desc in commands:
        print(f"[*] Testing {desc} (Req: {hex(req)}, Val: {hex(val)})...")
        try:
            # 0xC0 = Device-to-Host, Vendor, Device
            ret = dev.ctrl_transfer(0xC0, req, val, idx, length, timeout=1000)
            if ret:
                print(f"  [+] Success! Data: {bytes(ret).hex().upper()}")
        except usb.core.USBError as e:
            print(f"  [-] Failed: {e}")

if __name__ == "__main__":
    probe_backdoor()
