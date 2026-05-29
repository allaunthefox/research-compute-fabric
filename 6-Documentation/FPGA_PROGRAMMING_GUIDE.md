# FPGA Programming Guide — SUBLEQ on the Blitter

**Last updated:** 2026-05-29
**Board:** Sipeed Tang Nano 9K (Gowin GW1NR-LV9)
**CPU:** Blitter6502OISC (One Instruction Set Computer — SUBLEQ)

---

## SUBLEQ Instruction Format

The Blitter implements a **SUBLEQ** (Subtract and Branch if Less-than-or-Equal to Zero) CPU.

Each instruction is **3 words** (3 × 16-bit = 6 bytes):

```
[src] [dst] [next]
```

**Semantics:**
```
mem[dst] = mem[dst] - mem[src]
if mem[dst] <= 0:
    PC = next
else:
    PC = PC + 3
```

**Special addresses:**
- If `next == 0` (or `next == PC`): **HALT**
- If `src == 0`: reads zero (constant source)
- If `dst == IO_ADDR`: writes to I/O

---

## Memory Map ($0000–$FFFF)

The SUBLEQ address space is 16-bit (64K words). The memory map is divided into regions:

| Address Range | Size | Function |
|---------------|------|----------|
| `$0000–$0FFF` | 4K words | Program + data (BRAM) |
| `$1000–$7FFF` | 28K words | Extended data (if available) |
| `$8000–$800F` | 16 words | Q16 LUT result registers |
| `$8010` | 1 word | Voltage controller mode |
| `$8011` | 1 word | Scale space parameter |
| `$8020–$8025` | 6 words | HiGHS pivot registers |
| `$FF00` | 1 word | UART TX data register |
| `$FF01` | 1 word | UART TX status (bit 0 = busy) |
| `$FF02` | 1 word | UART RX data register |
| `$FF03` | 1 word | UART RX status (bit 0 = data available) |
| `$FFF0` | 1 word | LED output (bits 0-5 = led[0:5]) |
| `$FFF1` | 1 word | Button input (bit 0 = user_btn) |

---

## Q16 LUT ($8000–$8025)

The Q16 LUT is a hardware-accelerated fixed-point arithmetic unit. It operates on Q16.16 values (16-bit integer, 16-bit fraction; total 1.0 = 65536).

### Q16 Operations

Write operands to the LUT registers, then read the result:

| Address | Register | Function |
|---------|----------|----------|
| `$8000` | OP_A (lo) | Operand A, low word |
| `$8001` | OP_A (hi) | Operand A, high word |
| `$8002` | OP_B (lo) | Operand B, low word |
| `$8003` | OP_B (hi) | Operand B, high word |
| `$8004` | OPCODE | Operation selector (0-7) |
| `$8008` | RESULT (lo) | Result, low word |
| `$8009` | RESULT (hi) | Result, high word |

### Opcodes

| Code | Operation | Latency |
|------|-----------|---------|
| 0 | A + B | 2 cycles (74ns @ 27MHz) |
| 1 | A - B | 2 cycles |
| 2 | A × B | 2 cycles |
| 3 | A ÷ B | 2 cycles |
| 4 | √A | 2 cycles |
| 5 | \|A\| | 2 cycles |
| 6 | min(A, B) | 2 cycles |
| 7 | max(A, B) | 2 cycles |

### Q16.16 Encoding

```
value = integer_part × 65536 + fraction_part

Examples:
  1.0  = 65536    (0x00010000)
  0.5  = 32768    (0x00008000)
  3.14 = 205887   (0x000323D7)
  -1.0 = -65536   (0xFFFF0000)
```

---

## Voltage Controller ($8010)

The voltage controller manages BRAM access modes:

| Mode | Value | Description |
|------|-------|-------------|
| STORE | 0 | Direct memory read/write |
| COMPUTE | 1 | Q16 LUT computation mode |
| APPROX | 2 | Approximate computation (fast) |
| MORPHIC | 3 | Morphic field mode |

```subleq
; Set voltage controller to COMPUTE mode
; Write 1 to address $8010
```

---

## Scale Space ($8011)

The scale space parameter controls Gaussian kernel selection:

| Value | σ (sigma) | Kernel Bank |
|-------|-----------|-------------|
| 0 | 0.25 | Bank 0 |
| 1 | 0.50 | Bank 1 |
| 2 | 0.75 | Bank 2 |
| 3 | 1.00 | Bank 3 |

---

## HiGHS Pivot Registers ($8020–$8025)

3-stage simplex pipeline interface for hardware-accelerated LP solving:

| Address | Register | Function |
|---------|----------|----------|
| `$8020` | PIVOT_ROW | Row index |
| `$8021` | PIVOT_COL | Column index |
| `$8022` | PIVOT_VAL (lo) | Pivot value, low |
| `$8023` | PIVOT_VAL (hi) | Pivot value, high |
| `$8024` | PIVOT_CTRL | Control/status |
| `$8025` | PIVOT_RESULT | Result/iteration count |

---

## Example Programs

### 1. Blink LED

Blink LED 0 in a loop:

```subleq
; Program at address 0
; Toggle LED 0 by XOR with 1

; mem[100] = 1 (constant)
; mem[101] = LED address ($FFF0)
; mem[102] = current LED state
; mem[103] = 0 (zero constant)

; Instruction 0: sub 103 from 102, store in 102 (clear 102)
addr 0:  103  102  3     ; mem[102] = mem[102] - mem[103] = 0

; Instruction 3: sub 103 from LED, store in LED (clear LED)
addr 3:  103  2545  6    ; mem[$FFF0] = mem[$FFF0] - 0

; Instruction 6: sub 100 from LED, store in LED (set bit 0)
addr 6:  100  2545  9    ; mem[$FFF0] = mem[$FFF0] - 1

; Instruction 9: delay loop
addr 9:  104  104  12    ; mem[104] = mem[104] - 1
addr 12: 104  104  0     ; if mem[104] <= 0, jump to 0 (restart)

; Data
addr 100: 1              ; toggle mask
addr 101: 0              ; unused
addr 102: 0              ; LED state
addr 103: 0              ; zero
addr 104: 50000           ; delay counter
```

**Assembled binary:**
```
0064 0066 0003
0067 09F1 0006
0064 09F1 0009
0068 0068 000C
0068 0068 0000
0001 0000 0000 0000 C350
```

### 2. Q16 Addition

Add two Q16.16 values using the hardware LUT:

```subleq
; Write operands to Q16 LUT, read result

; mem[200] = operand A = 3.14 (Q16: 205887 = 0x000323D7)
; mem[201] = operand B = 2.72 (Q16: 178258 = 0x0002B8F2)

; Write A low word to $8000
addr 0:  200  32768  3    ; mem[$8000] = mem[200] (A low)

; Write A high word to $8001
addr 3:  201  32769  6    ; mem[$8001] = 0 (A high)

; Write B low word to $8002
addr 6:  202  32770  9    ; mem[$8002] = mem[202] (B low)

; Write B high word to $8003
addr 9:  203  32771  12   ; mem[$8003] = 0 (B high)

; Set opcode to 0 (add)
addr 12: 204  32772  15   ; mem[$8004] = 0

; Read result low from $8008
addr 15: 204  32776  18   ; mem[$8008] -> read

; Store result to mem[210]
addr 18: 32776  210  21   ; mem[210] = result low

; HALT
addr 21: 0  0  0

; Data
addr 200: 23D7  ; A low (3.14)
addr 201: 0003  ; A high
addr 202: B8F2  ; B low (2.72)
addr 203: 0002  ; B high
addr 204: 0000  ; opcode 0 (add)
```

### 3. UART Send Character

Send 'A' (0x41) over UART:

```subleq
; Wait for TX to be not busy, then send character

; mem[300] = 0x41 ('A')
; mem[301] = 0 (zero)
; mem[302] = UART TX status address ($FF01)
; mem[303] = UART TX data address ($FF00)

; Check TX status (poll loop)
addr 0:  302  304  3      ; mem[304] = mem[$FF01]
addr 3:  304  304  6      ; mem[304] -= mem[304] (test if zero)
addr 6:  304  304  9      ; if <= 0 (not busy), continue
addr 9:  301  304  0      ; else, reset and retry

; Send character
addr 12: 300  303  15     ; mem[$FF00] = 0x41

; HALT
addr 15: 0  0  0

; Data
addr 300: 0041   ; 'A'
addr 301: 0000   ; zero
addr 302: FF01   ; UART TX status
addr 303: FF00   ; UART TX data
addr 304: 0000   ; temp
```

---

## Loading Programs via UART

### Using Python

```python
import serial
import struct

# Load assembled program (array of 16-bit words)
program = [0x0064, 0x0066, 0x0003, ...]  # assembled instructions

# Connect to FPGA UART
ser = serial.Serial('/dev/ttyUSB0', 115384, timeout=1)

# Send program: each word as 2 bytes, big-endian
for word in program:
    ser.write(struct.pack('>H', word))

ser.close()
```

### Using openFPGALoader (SRAM load)

For quick iteration (non-persistent):

```bash
# Load bitstream to SRAM (lost on power cycle)
openFPGALoader -b tangnano9k --sram research_stack_top.fs

# Load to flash (persistent)
openFPGALoader -b tangnano9k research_stack_top.fs
```

---

## Reading Results

### Via UART

```python
import serial

ser = serial.Serial('/dev/ttyUSB0', 115384, timeout=5)

# Read result bytes
data = ser.read(2)  # 1 word = 2 bytes
result = struct.unpack('>H', data)[0]
print(f"Result: {result} (0x{result:04X})")

ser.close()
```

### Via LEDs

Read the 6 LEDs (pins 10-16) as a 6-bit value from `led[0:5]`.
- LED 0 = bit 0 (rightmost)

### Via Memory Dump

After HALT, the UART TX beacon outputs the full memory contents.
Connect a serial terminal and observe the dump.

---

## Build Toolchain

```bash
# Synthesis
cd 4-Infrastructure/hardware && bash build_research_stack.sh

# Simulation
cd /tmp/fpga_sim_full && ./obj_dir/sim_top

# Flash
openFPGALoader -b tangnano9k research_stack_top.fs
```

### Tool Versions

| Tool | Version |
|------|---------|
| Yosys | 0.64 |
| nextpnr-himbaechel | 0.10-75 |
| gowin_pack | latest |
| Verilator | 5.048 |
| openFPGALoader | latest |

---

## Timing

- **Clock:** 27 MHz (37.04 ns period)
- **Achieved Fmax:** 195.92 MHz (7.2× margin)
- **Q16 LUT latency:** 2 cycles (74 ns)
- **MAX_CYCLES:** 1,000,000
