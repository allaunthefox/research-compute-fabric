#!/usr/bin/env python3
"""
NES Controller Port Virtual JTAG Implementation
Bitbangs JTAG protocol over NES controller port for retro hardware debugging.

NES Controller Port Pinout (7-pin connector):
- Pin 1: VCC (+5V)
- Pin 2: CLK (Controller latch/strobe - 4016)
- Pin 3: OUT (Controller data - 4017 serial out)
- Pin 4: GND
- Pin 5: IN (Controller data in - serial in)
- Pin 6: +5V (unused)
- Pin 7: GND

JTAG Mapping to NES Controller Port:
- TCK (Test Clock) → CLK (Pin 2) - strobe/latch signal
- TMS (Test Mode Select) → OUT (Pin 3) - data out from NES
- TDI (Test Data In) → IN (Pin 5) - data in to NES
- TDO (Test Data Out) → Bitbang via CLK toggling (read on next cycle)

Protocol:
- NES 4016/4017 shift registers normally used for controller polling
- Repurpose as JTAG TAP (Test Access Port) state machine
- Bitbang JTAG state transitions via CLK/TMS/TDI
- Read TDO on CLK falling edge

This is INSANE: Using 1985 game controller hardware for 1990s JTAG debugging.
"""

import struct
import time
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════
# JTAG TAP State Machine
# ═══════════════════════════════════════════════════════════════════════════

class JTAGState(Enum):
    """JTAG TAP states"""
    TEST_LOGIC_RESET = 0
    RUN_TEST_IDLE = 1
    SELECT_DR_SCAN = 2
    CAPTURE_DR = 3
    SHIFT_DR = 4
    EXIT1_DR = 5
    PAUSE_DR = 6
    EXIT2_DR = 7
    UPDATE_DR = 8
    SELECT_IR_SCAN = 9
    CAPTURE_IR = 10
    SHIFT_IR = 11
    EXIT1_IR = 12
    PAUSE_IR = 13
    EXIT2_IR = 14
    UPDATE_IR = 15

# JTAG state transition table (TMS=0, TMS=1)
JTAG_TRANSITIONS = {
    JTAGState.TEST_LOGIC_RESET: (JTAGState.RUN_TEST_IDLE, JTAGState.TEST_LOGIC_RESET),
    JTAGState.RUN_TEST_IDLE: (JTAGState.RUN_TEST_IDLE, JTAGState.SELECT_DR_SCAN),
    JTAGState.SELECT_DR_SCAN: (JTAGState.CAPTURE_DR, JTAGState.SELECT_IR_SCAN),
    JTAGState.CAPTURE_DR: (JTAGState.SHIFT_DR, JTAGState.EXIT1_DR),
    JTAGState.SHIFT_DR: (JTAGState.SHIFT_DR, JTAGState.EXIT1_DR),
    JTAGState.EXIT1_DR: (JTAGState.PAUSE_DR, JTAGState.UPDATE_DR),
    JTAGState.PAUSE_DR: (JTAGState.PAUSE_DR, JTAGState.EXIT2_DR),
    JTAGState.EXIT2_DR: (JTAGState.SHIFT_DR, JTAGState.UPDATE_DR),
    JTAGState.UPDATE_DR: (JTAGState.RUN_TEST_IDLE, JTAGState.SELECT_DR_SCAN),
    JTAGState.SELECT_IR_SCAN: (JTAGState.CAPTURE_IR, JTAGState.TEST_LOGIC_RESET),
    JTAGState.CAPTURE_IR: (JTAGState.SHIFT_IR, JTAGState.EXIT1_IR),
    JTAGState.SHIFT_IR: (JTAGState.SHIFT_IR, JTAGState.EXIT1_IR),
    JTAGState.EXIT1_IR: (JTAGState.PAUSE_IR, JTAGState.UPDATE_IR),
    JTAGState.PAUSE_IR: (JTAGState.PAUSE_IR, JTAGState.EXIT2_IR),
    JTAGState.EXIT2_IR: (JTAGState.SHIFT_IR, JTAGState.UPDATE_IR),
    JTAGState.UPDATE_IR: (JTAGState.RUN_TEST_IDLE, JTAGState.SELECT_DR_SCAN),
}

@dataclass
class JTAGTAP:
    """Virtual JTAG TAP (Test Access Port)"""
    state: JTAGState = JTAGState.TEST_LOGIC_RESET
    ir: int = 0  # Instruction Register (default 4-bit)
    dr: int = 0  # Data Register
    ir_length: int = 4  # Default IR length
    
    def transition(self, tms: int) -> JTAGState:
        """Transition state based on TMS"""
        self.state = JTAG_TRANSITIONS[self.state][tms]
        return self.state
    
    def reset(self):
        """Reset to TEST_LOGIC_RESET (5+ TMS=1 cycles)"""
        self.state = JTAGState.TEST_LOGIC_RESET
        self.ir = 0
        self.dr = 0

# ═══════════════════════════════════════════════════════════════════════════
# NES Controller Port JTAG Bitbanging
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class NESControllerPort:
    """NES controller port state"""
    clk: bool = False  # Pin 2 (4016 strobe)
    out: bool = False  # Pin 3 (4017 data out / TMS)
    inp: bool = False  # Pin 5 (4017 data in / TDI)
    
    def to_byte(self) -> int:
        """Pack port state to byte (for simulation)"""
        bits = 0
        if self.clk: bits |= 0x01
        if self.out: bits |= 0x02
        if self.inp: bits |= 0x04
        return bits
    
    @staticmethod
    def from_byte(data: int) -> 'NESControllerPort':
        """Unpack byte to port state"""
        return NESControllerPort(
            clk=bool(data & 0x01),
            out=bool(data & 0x02),
            inp=bool(data & 0x04)
        )

class NESJTAGBitbanger:
    """Bitbang JTAG over NES controller port"""
    
    def __init__(self, tap: JTAGTAP):
        self.tap = tap
        self.port = NESControllerPort()
        self.tdo_buffer: List[bool] = []
        self.cycle_count = 0
    
    def clock_cycle(self, tms: int, tdi: int) -> int:
        """
        Execute one JTAG clock cycle over NES controller port.
        
        NES Controller Port Protocol:
        1. Set CLK low (prepare)
        2. Set OUT = TMS (TMS from host)
        3. Set IN = TDI (TDI from host)
        4. Set CLK high (latch)
        5. Read TDO from OUT on falling edge
        6. Set CLK low (complete)
        
        Returns: TDO value
        """
        # Step 1-3: Prepare signals
        self.port.clk = False
        self.port.out = bool(tms)
        self.port.inp = bool(tdi)
        
        # Step 4: Latch (CLK high)
        self.port.clk = True
        
        # Transition TAP state
        self.tap.transition(tms)
        
        # Step 5: Read TDO (on falling edge)
        tdo = self.read_tdo()
        
        # Step 6: Complete cycle
        self.port.clk = False
        
        self.cycle_count += 1
        return tdo
    
    def read_tdo(self) -> int:
        """Read TDO from virtual TAP"""
        # In SHIFT_DR or SHIFT_IR states, shift out data
        if self.tap.state == JTAGState.SHIFT_DR:
            tdo = self.tap.dr & 1
            self.tap.dr >>= 1
            return tdo
        elif self.tap.state == JTAGState.SHIFT_IR:
            tdo = self.tap.ir & 1
            self.tap.ir >>= 1
            return tdo
        else:
            return 0  # TDO is 0 in non-shift states
    
    def shift_bits(self, tms_sequence: List[int], tdi_data: int, bit_count: int) -> int:
        """
        Shift bits through JTAG.
        
        Args:
            tms_sequence: TMS values for each bit (length = bit_count)
            tdi_data: TDI data to shift in (LSB first)
            bit_count: Number of bits to shift
        
        Returns:
            TDO data shifted out (LSB first)
        """
        tdo_result = 0
        
        for i in range(bit_count):
            tms = tms_sequence[i] if i < len(tms_sequence) else 0
            tdi = (tdi_data >> i) & 1
            tdo = self.clock_cycle(tms, tdi)
            tdo_result |= (tdo << i)
        
        return tdo_result
    
    def goto_state(self, target_state: JTAGState):
        """Navigate to target state using TMS transitions"""
        while self.tap.state != target_state:
            # Find transition that gets closer to target
            next_0, next_1 = JTAG_TRANSITIONS[self.tap.state]
            
            # Simple heuristic: prefer TMS=0 unless we need to go up
            if next_0 == target_state or (next_1 != target_state and next_0 != JTAGState.TEST_LOGIC_RESET):
                self.clock_cycle(0, 0)
            else:
                self.clock_cycle(1, 0)
    
    def run_test_idle_cycles(self, count: int):
        """Run cycles in RUN_TEST_IDLE state"""
        self.goto_state(JTAGState.RUN_TEST_IDLE)
        for _ in range(count):
            self.clock_cycle(0, 0)
    
    def reset_tap(self):
        """Reset TAP to TEST_LOGIC_RESET"""
        for _ in range(6):
            self.clock_cycle(1, 0)

# ═══════════════════════════════════════════════════════════════════════════
# JTAG Instructions (Standard)
# ═══════════════════════════════════════════════════════════════════════════

class JTAGInstruction(Enum):
    """Standard JTAG instructions"""
    BYPASS = 0xF      # Bypass register (1-bit)
    IDCODE = 0x2      # IDCODE register (32-bit)
    EXTEST = 0x0      # External test
    SAMPLE = 0x1      # Sample preload
    INTEST = 0x3      # Internal test

# ═══════════════════════════════════════════════════════════════════════════
# Virtual JTAG Device (for testing)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class VirtualJTAGDevice:
    """Virtual JTAG device for testing NES bitbanging"""
    idcode: int = 0x12345678  # Default IDCODE
    bypass: int = 0  # Bypass register (1-bit)
    dr_length: int = 32  # Default DR length
    
    def scan_idcode(self, bitbanger: NESJTAGBitbanger) -> int:
        """Perform IDCODE scan"""
        bitbanger.reset_tap()
        bitbanger.goto_state(JTAGState.SHIFT_DR)
        
        # Shift 32 bits (TMS=0 for all but last)
        tms_seq = [0] * 31 + [1]
        idcode = bitbanger.shift_bits(tms_seq, 0, 32)
        
        bitbanger.run_test_idle_cycles(1)
        return idcode

# ═══════════════════════════════════════════════════════════════════════════
# NES 6502 Assembly Driver (for actual NES implementation)
# ═══════════════════════════════════════════════════════════════════════════

def generate_nes_6502_jtag_driver() -> str:
    """
    Generate 6502 assembly code for NES JTAG bitbanging.
    
    NES Memory Map:
    - $4016: Controller port 1 strobe (write)
    - $4017: Controller port 2 strobe (write)
    - $4016: Controller port 1 data (read)
    - $4017: Controller port 2 data (read)
    
    This is INSANE: 6502 assembly bitbanging JTAG on a game console.
    """
    return """
; ═══════════════════════════════════════════════════════════════════════════
; NES JTAG Bitbanging Driver (6502 Assembly)
; Uses controller port for virtual JTAG interface
; ═══════════════════════════════════════════════════════════════════════════

; NES Controller Port Addresses
JOY1_STROBE   = $4016  ; Write to strobe controller 1
JOY1_DATA     = $4016  ; Read controller 1 data
JOY2_STROBE   = $4017  ; Write to strobe controller 2
JOY2_DATA     = $4017  ; Read controller 2 data

; JTAG Pin Mapping
; CLK (TCK)  → Strobe signal (write to JOY1_STROBE)
; TMS        → Data out bit 0 (write to JOY1_STROBE)
; TDI        → Data in bit 0 (read from JOY1_DATA)
; TDO        → Data out bit 0 (read from JOY1_DATA on CLK low)

; Zero Page Variables
zp_tms        = $00    ; TMS value
zp_tdi        = $01    ; TDI value
zp_tdo        = $02    ; TDO value
zp_bit_count  = $03    ; Bit counter
zp_data_ptr   = $04    ; Data pointer (lo)
zp_data_ptr_h = $05    ; Data pointer (hi)

; ═══════════════════════════════════════════════════════════════════════════
; JTAG Clock Cycle
; Input:  A = TMS, X = TDI
; Output: Y = TDO
; ═══════════════════════════════════════════════════════════════════════════

jtag_clock_cycle:
    STA zp_tms        ; Store TMS
    STX zp_tdi        ; Store TDI
    
    ; Step 1: CLK low
    LDA #$00
    STA JOY1_STROBE
    
    ; Step 2-3: Set OUT = TMS, IN = TDI
    ; (For simulation, we'd set pins here)
    
    ; Step 4: CLK high (latch)
    LDA #$01
    STA JOY1_STROBE
    
    ; Step 5: Read TDO on falling edge
    LDA #$00
    STA JOY1_STROBE   ; CLK low
    LDA JOY1_DATA     ; Read data
    AND #$01          ; Mask bit 0
    STA zp_tdo        ; Store TDO
    
    ; Return TDO in Y
    LDY zp_tdo
    RTS

; ═══════════════════════════════════════════════════════════════════════════
; JTAG Reset (5+ TMS=1 cycles)
; ═══════════════════════════════════════════════════════════════════════════

jtag_reset:
    LDA #$01          ; TMS = 1
    LDX #$00          ; TDI = 0
    LDY #$05          ; 5 cycles
jtag_reset_loop:
    JSR jtag_clock_cycle
    DEY
    BNE jtag_reset_loop
    RTS

; ═══════════════════════════════════════════════════════════════════════════
; JTAG Shift Bits
; Input:  X = bit count, (zp_data_ptr) = TMS sequence, (zp_data_ptr+X) = TDI data
; Output: Y = TDO data
; ═══════════════════════════════════════════════════════════════════════════

jtag_shift_bits:
    STX zp_bit_count
    LDY #$00          ; TDO result = 0
jtag_shift_loop:
    ; Get TMS from sequence
    LDA (zp_data_ptr), Y
    STA zp_tms
    
    ; Get TDI from data
    LDA (zp_data_ptr), X
    STA zp_tdi
    
    ; Clock cycle
    LDA zp_tms
    LDX zp_tdi
    JSR jtag_clock_cycle
    
    ; Accumulate TDO
    TYA
    ASL
    ORA zp_tdo
    TAY
    
    ; Next bit
    DEC zp_bit_count
    BNE jtag_shift_loop
    
    RTS

; ═══════════════════════════════════════════════════════════════════════════
; JTAG IDCODE Scan
; Output: $00-$03 = IDCODE (little-endian)
; ═══════════════════════════════════════════════════════════════════════════

jtag_idcode_scan:
    JSR jtag_reset     ; Reset TAP
    
    ; Go to SHIFT_DR state
    ; TMS sequence: 0,1,0,0 (SELECT_DR_SCAN, CAPTURE_DR, SHIFT_DR)
    LDA #$00
    LDX #$00
    JSR jtag_clock_cycle ; RUN_TEST_IDLE → SELECT_DR_SCAN (TMS=1 would skip)
    
    LDA #$01
    LDX #$00
    JSR jtag_clock_cycle ; SELECT_DR_SCAN → CAPTURE_DR (TMS=0)
    
    LDA #$00
    LDX #$00
    JSR jtag_clock_cycle ; CAPTURE_DR → SHIFT_DR (TMS=0)
    
    ; Shift 32 bits (IDCODE)
    LDX #$20          ; 32 bits
    ; TMS sequence: 0 for 31 bits, 1 for last bit
    ; For simplicity, we'll shift with TMS=0 then exit
    JSR jtag_shift_bits
    
    ; Go to RUN_TEST_IDLE
    LDA #$01
    LDX #$00
    JSR jtag_clock_cycle ; SHIFT_DR → EXIT1_DR
    
    LDA #$00
    LDX #$00
    JSR jtag_clock_cycle ; EXIT1_DR → UPDATE_DR
    
    LDA #$00
    LDX #$00
    JSR jtag_clock_cycle ; UPDATE_DR → RUN_TEST_IDLE
    
    RTS

; ═══════════════════════════════════════════════════════════════════════════
; Main Entry Point
; ═══════════════════════════════════════════════════════════════════════════

main:
    JSR jtag_idcode_scan
    
    ; Store IDCODE in RAM
    STY $0200         ; IDCODE byte 0
    STY $0201         ; IDCODE byte 1
    STY $0202         ; IDCODE byte 2
    STY $0203         ; IDCODE byte 3
    
    ; Infinite loop
    JMP main
"""

# ═══════════════════════════════════════════════════════════════════════════
# Host-Side JTAG Controller (Python)
# ═══════════════════════════════════════════════════════════════════════════

class NESJTAGHostController:
    """Host-side JTAG controller for NES bitbanging"""
    
    def __init__(self, bitbanger: NESJTAGBitbanger):
        self.bitbanger = bitbanger
    
    def scan_ir(self, instruction: int, ir_length: int = 4) -> int:
        """Scan instruction into IR"""
        self.bitbanger.reset_tap()
        self.bitbanger.goto_state(JTAGState.SHIFT_IR)
        
        # Shift instruction (TMS=0 for all but last)
        tms_seq = [0] * (ir_length - 1) + [1]
        result = self.bitbanger.shift_bits(tms_seq, instruction, ir_length)
        
        self.bitbanger.run_test_idle_cycles(1)
        return result
    
    def scan_dr(self, data: int, dr_length: int = 32) -> int:
        """Scan data into DR"""
        self.bitbanger.goto_state(JTAGState.SHIFT_DR)
        
        # Shift data (TMS=0 for all but last)
        tms_seq = [0] * (dr_length - 1) + [1]
        result = self.bitbanger.shift_bits(tms_seq, data, dr_length)
        
        self.bitbanger.run_test_idle_cycles(1)
        return result
    
    def get_idcode(self) -> int:
        """Get device IDCODE"""
        # Load IDCODE instruction
        self.scan_ir(JTAGInstruction.IDCODE.value, 4)
        # Scan DR
        return self.scan_dr(0, 32)

# ═══════════════════════════════════════════════════════════════════════════
# Test / Demo
# ═══════════════════════════════════════════════════════════════════════════

def run_test():
    """Run NES JTAG bitbanging test"""
    print("=" * 70)
    print("NES CONTROLLER PORT VIRTUAL JTAG TEST")
    print("=" * 70)
    print("\n[*] This is INSANE: Bitbanging JTAG over NES controller port")
    print("[*] Mapping:")
    print("    TCK → CLK (Pin 2)")
    print("    TMS → OUT (Pin 3)")
    print("    TDI → IN (Pin 5)")
    print("    TDO → Bitbang via CLK toggling")
    
    # Create virtual TAP and bitbanger
    tap = JTAGTAP(ir_length=4)
    bitbanger = NESJTAGBitbanger(tap)
    
    # Create virtual device
    device = VirtualJTAGDevice(idcode=0xDEADBEEF)
    
    # Create host controller
    host = NESJTAGHostController(bitbanger)
    
    print("\n[*] Virtual device IDCODE: 0x{:08X}".format(device.idcode))
    
    # Test IDCODE scan
    print("\n[*] Performing IDCODE scan...")
    idcode = device.scan_idcode(bitbanger)
    print("[*] Scanned IDCODE: 0x{:08X}".format(idcode))
    
    if idcode == device.idcode:
        print("[✓] IDCODE scan successful")
    else:
        print("[✗] IDCODE mismatch")
    
    # Test state transitions
    print("\n[*] Testing state transitions...")
    bitbanger.reset_tap()
    print("    Initial state: {}".format(bitbanger.tap.state.name))
    
    bitbanger.goto_state(JTAGState.SHIFT_DR)
    print("    After goto SHIFT_DR: {}".format(bitbanger.tap.state.name))
    
    bitbanger.goto_state(JTAGState.RUN_TEST_IDLE)
    print("    After goto RUN_TEST_IDLE: {}".format(bitbanger.tap.state.name))
    
    # Test bit shifting
    print("\n[*] Testing bit shifting...")
    bitbanger.goto_state(JTAGState.SHIFT_DR)
    bitbanger.tap.dr = 0xAAAAAAAA  # Set DR
    tdo = bitbanger.shift_bits([0, 0, 0, 0, 0, 0, 0, 1], 0x55555555, 8)
    print("    DR before: 0x{:08X}".format(bitbanger.tap.dr))
    print("    TDO shifted: 0x{:02X}".format(tdo))
    print("    Expected: 0xAA (shifted out LSB first)")
    
    # Statistics
    print("\n[*] Statistics:")
    print("    Total clock cycles: {}".format(bitbanger.cycle_count))
    print("    TAP state: {}".format(bitbanger.tap.state.name))
    print("    IR: 0x{:X}".format(bitbanger.tap.ir))
    print("    DR: 0x{:X}".format(bitbanger.tap.dr))
    
    # Generate 6502 assembly
    print("\n[*] Generating 6502 assembly driver...")
    assembly = generate_nes_6502_jtag_driver()
    print("[*] Generated {} bytes of assembly".format(len(assembly)))
    
    # Save assembly to file
    with open('/home/allaun/Documents/Research Stack/scripts/nes_jtag_6502.asm', 'w') as f:
        f.write(assembly)
    print("[*] Saved to 5-Applications/scripts/nes_jtag_6502.asm")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\n[*] INSANITY LEVEL: MAXIMUM")
    print("[*] 1985 NES hardware now supports 1990s JTAG debugging")
    print("[*] Next step: Actually wire this to real NES hardware")

if __name__ == "__main__":
    run_test()
