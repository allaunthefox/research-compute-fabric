import usb.core
import usb.util
import sys

# Chipsbank / ITE CBM2199
# VID: 048d, PID: 1234
VENDOR_ID = 0x048d
PRODUCT_ID = 0x1234

def probe_registers():
    # Find device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    
    if dev is None:
        print("Device not found")
        return

    print(f"Found Device: {hex(VENDOR_ID)}:{hex(PRODUCT_ID)}")
    
    # Detach kernel driver if necessary
    if dev.is_kernel_driver_active(0):
        try:
            dev.detach_kernel_driver(0)
            print("Detached kernel driver")
        except usb.core.USBError as e:
            print(f"Could not detach kernel driver: {e}")

    # bmRequestType: 0xC0 (Device to Host, Vendor, Device)
    # bRequest: 0x01 (Read Register)
    # wValue: Register Address
    # wIndex: 0
    # wLength: 1 or 4
    
    print("\nRegister Sweep (0x00 - 0x1F):")
    for reg in range(0x20):
        try:
            # Try reading 1 byte
            ret = dev.ctrl_transfer(0xC0, 0x01, reg, 0, 1)
            if ret:
                print(f"Reg {hex(reg)}: {hex(ret[0])}")
        except usb.core.USBError as e:
            # print(f"Reg {hex(reg)}: Error {e}")
            pass

    # Try standard inquiry via control transfer if 0x01 fails
    # Or try 0x06 Exec command
    
    # Re-attach kernel driver
    usb.util.dispose_resources(dev)

if __name__ == "__main__":
    probe_registers()
