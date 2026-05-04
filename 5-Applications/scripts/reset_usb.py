import usb.core
import usb.util
import os

VENDOR_ID = 0x048d
PRODUCT_ID = 0x1234

def reset_and_reattach():
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        print("Device not found")
        return

    try:
        dev.reset()
        print("Device reset sent")
    except Exception as e:
        print(f"Reset failed: {e}")

    # Re-attach is usually automatic after reset, but we can try to force it
    # if the device didn't disappear and reappear
    try:
        if not dev.is_kernel_driver_active(0):
            dev.attach_kernel_driver(0)
            print("Attached kernel driver")
    except Exception as e:
        print(f"Attach failed (may be normal if device re-enumerated): {e}")

if __name__ == "__main__":
    reset_and_reattach()
