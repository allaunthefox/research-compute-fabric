import math

def to_q16_16(val):
    return int(val * 65536) & 0xFFFFFFFF

def generate_mem_files():
    # 256 entries, x = index / 16.0 (if we use ray_t[19:12] as addr)
    # However, to avoid 1/0, we'll use x = max(0.0625, index / 16.0)
    
    with open("0-Core-Formalism/core/hw/diat_inv_table.mem", "w") as f_inv, \
         open("0-Core-Formalism/core/hw/diat_sqrt_table.mem", "w") as f_sqrt:
        
        for i in range(256):
            x = i / 16.0
            if x == 0:
                x = 1/16.0 # Smallest non-zero
            
            y_inv = 1.0 / math.sqrt(x)
            y_sqrt = math.sqrt(x)
            
            f_inv.write(f"{to_q16_16(y_inv):08x}\n")
            f_sqrt.write(f"{to_q16_16(y_sqrt):08x}\n")

    print("Success: Generated diat_inv_table.mem and diat_sqrt_table.mem")

if __name__ == "__main__":
    generate_mem_files()
