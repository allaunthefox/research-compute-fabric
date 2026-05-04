#!/usr/bin/env python3
"""
Unified Computational Stack: Proto-Shader + GCL + Square Wave
Most minimal OISC with NES palette generator as proto-shader.

Architecture:
1. Minimal OISC (SUBLEQ: M[b] = M[b] - M[a]; if M[b] ≤ 0 goto c)
2. NES Palette Generator as Proto-Shader (generates color/grayscale from parameters)
3. GCL Compression (DeltaGCL) for data
4. Square Wave Generator (audio output)

The NES palette generator acts as a shader primitive:
- Input: Parameters (frequency, phase, modulation)
- Output: Color/grayscale values (0-63 for NES palette)
- Like a fragment shader: f(x,y,t) → color

Unified Memory Map (64K):
- $0000-$00FF: Zero page (OISC registers)
- $0100-$01FF: Shader parameters
- $0200-$02FF: Palette LUT (64 NES colors)
- $0300-$03FF: GCL compressed data
- $0400-$07FF: Square wave LUT
- $0800-$7FFF: OISC program + workspace
- $8000-$FFFF: I/O (audio, video output)

This is the unified stack: shader primitive + compression + audio in minimal OISC.
"""

import struct
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════
# Minimal OISC: SUBLEQ (One Instruction Set Computer)
# Instruction: M[b] = M[b] - M[a]; if M[b] ≤ 0 goto c
# This is the most minimal Turing-complete OISC
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SUBLEQInstruction:
    """SUBLEQ instruction: M[b] = M[b] - M[a]; if M[b] ≤ 0 goto c"""
    a: int  # Source address
    b: int  # Destination address
    c: int  # Jump address

class MinimalOISC:
    """Minimal SUBLEQ OISC with unified memory"""
    
    def __init__(self, memory_size: int = 65536):
        self.memory = [0] * memory_size
        self.pc = 0  # Program counter
        self.halted = False
        self.cycle_count = 0
    
    def load_program(self, instructions: List[Tuple[int, int, int]], start_addr: int = 0x0800):
        """Load SUBLEQ program into memory"""
        for i, (a, b, c) in enumerate(instructions):
            addr = start_addr + i * 3
            self.memory[addr] = a & 0xFF
            self.memory[addr + 1] = (a >> 8) & 0xFF
            self.memory[addr + 2] = b & 0xFF
            self.memory[addr + 3] = (b >> 8) & 0xFF
            self.memory[addr + 4] = c & 0xFF
            self.memory[addr + 5] = (c >> 8) & 0xFF
    
    def step(self) -> bool:
        """Execute one SUBLEQ instruction"""
        if self.halted:
            return False
        
        # Fetch instruction (6 bytes)
        a = self.memory[self.pc] | (self.memory[self.pc + 1] << 8)
        b = self.memory[self.pc + 2] | (self.memory[self.pc + 3] << 8)
        c = self.memory[self.pc + 4] | (self.memory[self.pc + 5] << 8)
        
        # Execute: M[b] = M[b] - M[a]
        src_val = self.memory[a]
        dst_val = self.memory[b]
        result = (dst_val - src_val) & 0xFF
        self.memory[b] = result
        
        # Branch if result <= 0 (signed)
        if result & 0x80 or result == 0:
            self.pc = c
        else:
            self.pc += 6
        
        self.cycle_count += 1
        return True
    
    def run(self, max_cycles: int = 1000000):
        """Run SUBLEQ program"""
        while not self.halted and self.cycle_count < max_cycles:
            if not self.step():
                break

# ═══════════════════════════════════════════════════════════════════════════
# NES Palette Generator as Proto-Shader
# Acts like a fragment shader: f(parameters) → color
# NES palette: 64 colors (6-bit: 2 red, 2 green, 2 blue)
# ═══════════════════════════════════════════════════════════════════════════

class NESPaletteShader:
    """NES palette generator as proto-shader primitive"""
    
    # NES color levels (0-3 for each channel)
    COLOR_LEVELS = [0x00, 0x55, 0xAA, 0xFF]  # 0%, 33%, 66%, 100%
    
    @staticmethod
    def encode_color(r: int, g: int, b: int) -> int:
        """Encode RGB to NES palette index (0-63)"""
        # Each channel: 2 bits
        r_bits = (r & 0x3) << 4
        g_bits = (g & 0x3) << 2
        b_bits = (b & 0x3) << 0
        return r_bits | g_bits | b_bits
    
    @staticmethod
    def decode_color(index: int) -> Tuple[int, int, int]:
        """Decode NES palette index to RGB"""
        r = (index >> 4) & 0x3
        g = (index >> 2) & 0x3
        b = (index >> 0) & 0x3
        return (r, g, b)
    
    @staticmethod
    def shader_compute(x: int, y: int, t: int, params: bytes) -> int:
        """
        Proto-shader compute function.
        
        Like a fragment shader: f(x, y, t, params) → color
        
        Args:
            x: X coordinate (0-255)
            y: Y coordinate (0-255)
            t: Time/phase (0-255)
            params: Shader parameters (e.g., frequency, modulation)
        
        Returns:
            NES palette index (0-63)
        """
        # Simple shader: gradient based on position + time
        # This is the "proto-shader" - minimal but functional
        
        # Extract parameters
        freq = params[0] if len(params) > 0 else 1
        mod = params[1] if len(params) > 1 else 0
        
        # Compute gradient
        r = ((x + t * freq) % 256) >> 6  # 2 bits
        g = ((y + t * freq) % 256) >> 6
        b = ((x + y + mod) % 256) >> 6
        
        return NESPaletteShader.encode_color(r, g, b)
    
    @staticmethod
    def generate_palette_lut(params: bytes) -> List[int]:
        """Generate complete NES palette LUT (64 entries)"""
        lut = []
        for i in range(64):
            # Use index as x, y, t for shader
            x = i % 8
            y = (i // 8) % 8
            t = i // 64
            color = NESPaletteShader.shader_compute(x * 32, y * 32, t * 32, params)
            lut.append(color)
        return lut

# ═══════════════════════════════════════════════════════════════════════════
# GCL Compression (from nes_gcl_square_stream.py)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SquareWaveFrame:
    """Square wave parameters (25 bits)"""
    frequency: int
    duty: int
    volume: int
    sweep_enable: int
    sweep_period: int
    sweep_direction: int
    sweep_shift: int
    
    def to_int(self) -> int:
        bits = 0
        bits |= (self.frequency & 0x7FF) << 14
        bits |= (self.duty & 0x3) << 12
        bits |= (self.volume & 0xF) << 8
        bits |= (self.sweep_enable & 1) << 7
        bits |= (self.sweep_period & 0x7) << 4
        bits |= (self.sweep_direction & 1) << 3
        bits |= (self.sweep_shift & 0x7) << 0
        return bits

# ═══════════════════════════════════════════════════════════════════════════
# Unified Memory Map
# ═══════════════════════════════════════════════════════════════════════════

class UnifiedMemoryMap:
    """Unified memory map for shader + GCL + audio stack"""
    
    # Memory regions
    ZERO_PAGE = 0x0000      # $0000-$00FF: OISC registers
    SHADER_PARAMS = 0x0100   # $0100-$01FF: Shader parameters
    PALETTE_LUT = 0x0200     # $0200-$02FF: NES palette LUT (64 entries)
    GCL_BUFFER = 0x0300      # $0300-$03FF: GCL compressed data
    AUDIO_LUT = 0x0400      # $0400-$07FF: Square wave LUT
    OISC_CODE = 0x0800      # $0800-$7FFF: OISC program
    IO_MAPPED = 0x8000      # $8000-$FFFF: I/O (audio, video)

# ═══════════════════════════════════════════════════════════════════════════
# Unified Computational Stack
# ═══════════════════════════════════════════════════════════════════════════

class UnifiedShaderStack:
    """Unified stack: Proto-shader + GCL + Square wave in minimal OISC"""
    
    def __init__(self):
        # Minimal SUBLEQ OISC
        self.oisc = MinimalOISC(memory_size=65536)
        
        # NES palette shader
        self.shader = NESPaletteShader()
        
        # Audio LUT
        self.audio_lut: List[int] = [0] * 256
        
        # Palette LUT
        self.palette_lut: List[int] = [0] * 64
    
    def load_shader_params(self, params: bytes):
        """Load shader parameters into memory"""
        for i, byte in enumerate(params):
            self.oisc.memory[UnifiedMemoryMap.SHADER_PARAMS + i] = byte
    
    def generate_palette_with_shader(self, params: bytes):
        """Generate palette LUT using proto-shader"""
        self.palette_lut = self.shader.generate_palette_lut(params)
        
        # Load into OISC memory
        for i, color in enumerate(self.palette_lut):
            self.oisc.memory[UnifiedMemoryMap.PALETTE_LUT + i] = color
    
    def load_gcl_data(self, gcl_bytes: bytes):
        """Load GCL compressed data"""
        for i, byte in enumerate(gcl_bytes):
            self.oisc.memory[UnifiedMemoryMap.GCL_BUFFER + i] = byte
    
    def generate_oisc_shader_program(self) -> List[Tuple[int, int, int]]:
        """
        Generate SUBLEQ program that:
        1. Uses shader to generate palette
        2. Decompresses GCL data
        3. Populates audio LUT
        4. Outputs to I/O registers
        
        This is the unified program in minimal OISC.
        """
        code = []
        
        # Initialize pointers
        # $0000 = shader_ptr (points to shader params at $0100)
        # $0002 = gcl_ptr (points to GCL buffer at $0300)
        # $0004 = audio_ptr (points to audio LUT at $0400)
        # $0006 = temp
        
        # Set initial pointers
        code.append((0x0006, 0x0006, 1))     # Zero temp
        code.append((0x0006, 0x0000, 2))     # temp = 0 - 0 = 0
        
        # Set shader_ptr = $0100
        code.append((0x0006, 0x0006, 3))     # temp = 0
        code.append((0x0006, 0x0100, 4))     # temp = $0100
        code.append((0x0006, 0x0000, 5))     # shader_ptr = $0100
        
        # Set gcl_ptr = $0300
        code.append((0x0006, 0x0300, 6))     # temp = $0300
        code.append((0x0006, 0x0002, 7))     # gcl_ptr = $0300
        
        # Set audio_ptr = $0400
        code.append((0x0006, 0x0400, 8))     # temp = $0400
        code.append((0x0006, 0x0004, 9))     # audio_ptr = $0400
        
        # Main loop: process GCL data
        # Read marker from GCL buffer
        code.append((0x0002, 0x0006, 10))    # temp = M[gcl_ptr]
        code.append((0x0006, 0x0044, 11))    # Check if 'D' (68)
        code.append((0x0006, 0x0006, 12))    # If equal, goto delta_decode
        code.append((0x0006, 0x0046, 13))    # Check if 'F' (70)
        code.append((0x0006, 0x0006, 14))    # If equal, goto full_decode
        code.append((0x0006, 0x0050, 15))    # Check if 'P' (80)
        code.append((0x0006, 0x0006, 16))    # If equal, goto pattern_decode
        code.append((0x0006, 0x0006, 100))   # Halt (unknown marker)
        
        # Simplified: just copy GCL to audio LUT (placeholder)
        # In real implementation, this would be full GCL decompression
        
        # Increment pointers and loop
        code.append((0x0002, 0x0006, 17))    # temp = M[gcl_ptr]
        code.append((0x0006, 0x0002, 18))    # gcl_ptr++
        code.append((0x0004, 0x0006, 19))    # audio_ptr++
        code.append((0x0006, 0x0006, 10))    # Loop back
        
        # Delta decode (placeholder)
        code.append((0x0006, 0x0006, 20))    # temp = 0
        code.append((0x0006, 0x0006, 10))    # Loop back
        
        # Full decode (placeholder)
        code.append((0x0006, 0x0006, 21))    # temp = 0
        code.append((0x0006, 0x0006, 10))    # Loop back
        
        # Pattern decode (placeholder)
        code.append((0x0006, 0x0006, 22))    # temp = 0
        code.append((0x0006, 0x0006, 10))    # Loop back
        
        # Halt
        code.append((0x0006, 0x0006, 0xFFFF)) # Halt (branch to $FFFF)
        
        return code
    
    def run_unified_stack(self, shader_params: bytes, gcl_data: bytes):
        """Run the unified computational stack"""
        print("=" * 70)
        print("UNIFIED SHADER + GCL + AUDIO STACK")
        print("=" * 70)
        
        # Load shader parameters
        print("\n[*] Loading shader parameters...")
        self.load_shader_params(shader_params)
        print("    Parameters: {}".format([hex(b) for b in shader_params]))
        
        # Generate palette with proto-shader
        print("\n[*] Generating palette with proto-shader...")
        self.generate_palette_with_shader(shader_params)
        print("    Palette LUT: {} entries".format(len(self.palette_lut)))
        print("    Sample colors: {}".format(self.palette_lut[:8]))
        
        # Load GCL data
        print("\n[*] Loading GCL compressed data...")
        self.load_gcl_data(gcl_data)
        print("    GCL data: {} bytes".format(len(gcl_data)))
        
        # Generate and load OISC program
        print("\n[*] Generating unified OISC program...")
        program = self.generate_oisc_shader_program()
        self.oisc.load_program(program)
        print("    Program: {} instructions".format(len(program)))
        
        # Run OISC
        print("\n[*] Running SUBLEQ OISC...")
        self.oisc.run(max_cycles=1000)
        print("    Cycles: {}".format(self.oisc.cycle_count))
        print("    Halted: {}".format(self.oisc.halted))
        
        # Read audio LUT from memory
        print("\n[*] Reading audio LUT from memory...")
        for i in range(16):
            addr = UnifiedMemoryMap.AUDIO_LUT + i
            val = self.oisc.memory[addr]
            if val != 0:
                print("    LUT[{}]: 0x{:02X}".format(i, val))
        
        print("\n" + "=" * 70)
        print("UNIFIED STACK COMPLETE")
        print("=" * 70)
        print("\n[*] Architecture Summary:")
        print("    Minimal OISC: SUBLEQ (1 instruction)")
        print("    Proto-Shader: NES palette generator")
        print("    GCL Compression: Delta encoding")
        print("    Square Wave: Audio LUT")
        print("\n[*] Unified in 64K memory map")

# ═══════════════════════════════════════════════════════════════════════════
# Test / Demo
# ═══════════════════════════════════════════════════════════════════════════

def run_test():
    """Run unified shader stack test"""
    # Create unified stack
    stack = UnifiedShaderStack()
    
    # Shader parameters (frequency, modulation)
    shader_params = bytes([0x05, 0x02, 0x00, 0x00])  # freq=5, mod=2
    
    # GCL data (simplified)
    gcl_data = bytes([
        ord('F'), 0x00, 0x10, 0x0F, 0x00,  # Full frame
        ord('D'), 0x01, 0x02, 0x01, 0x00,  # Delta
    ])
    
    # Run unified stack
    stack.run_unified_stack(shader_params, gcl_data)

if __name__ == "__main__":
    run_test()
