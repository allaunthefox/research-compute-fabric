#!/usr/bin/env python3
"""
NES Square Wave GCL Streaming System
Compresses square wave parameters using DeltaGCL for cartridge streaming.

NES Square Wave Parameters (per frame):
- Frequency: 11-bit divider (0-2047)
- Duty Cycle: 2-bit (0-3: 12.5%, 25%, 50%, 75%)
- Volume: 4-bit envelope (0-15)
- Sweep Enable: 1-bit
- Sweep Period: 3-bit
- Sweep Direction: 1-bit
- Sweep Shift: 3-bit

Total per frame: 25 bits uncompressed

GCL Compression Strategy:
1. Delta Encoding: Store only changes from previous frame
2. PTOS Dictionary: Common musical patterns as single-byte indices
3. Variable-Length GCL: Frequent sequences use shorter encoding

Target: 700× compression (25 bits → ~4 bytes with delta + dictionary)
"""

import struct
import json
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════
# NES Square Wave Parameter Structures
# ═══════════════════════════════════════════════════════════════════════════

class DutyCycle(Enum):
    """NES square wave duty cycles"""
    DUTY_12_5 = 0  # 12.5%
    DUTY_25 = 1    # 25%
    DUTY_50 = 2    # 50%
    DUTY_75 = 3    # 75%

@dataclass
class SquareWaveFrame:
    """Single frame of NES square wave parameters"""
    frequency: int      # 11-bit (0-2047)
    duty: DutyCycle      # 2-bit
    volume: int         # 4-bit (0-15)
    sweep_enable: bool  # 1-bit
    sweep_period: int   # 3-bit (0-7)
    sweep_direction: bool  # 1-bit (0=down, 1=up)
    sweep_shift: int    # 3-bit (0-7)
    
    def to_bits(self) -> int:
        """Pack into 25-bit integer"""
        bits = 0
        bits |= (self.frequency & 0x7FF) << 14  # 11 bits at position 14
        bits |= (self.duty.value & 0x3) << 12  # 2 bits at position 12
        bits |= (self.volume & 0xF) << 8       # 4 bits at position 8
        bits |= (int(self.sweep_enable) & 1) << 7  # 1 bit at position 7
        bits |= (self.sweep_period & 0x7) << 4   # 3 bits at position 4
        bits |= (int(self.sweep_direction) & 1) << 3  # 1 bit at position 3
        bits |= (self.sweep_shift & 0x7) << 0   # 3 bits at position 0
        return bits
    
    @staticmethod
    def from_bits(bits: int) -> 'SquareWaveFrame':
        """Unpack from 25-bit integer"""
        return SquareWaveFrame(
            frequency=(bits >> 14) & 0x7FF,
            duty=DutyCycle((bits >> 12) & 0x3),
            volume=(bits >> 8) & 0xF,
            sweep_enable=bool((bits >> 7) & 1),
            sweep_period=(bits >> 4) & 0x7,
            sweep_direction=bool((bits >> 3) & 1),
            sweep_shift=bits & 0x7
        )
    
    def to_bytes(self) -> bytes:
        """Pack into 4 bytes (25 bits fits in 32)"""
        return struct.pack('<I', self.to_bits())
    
    @staticmethod
    def from_bytes(data: bytes) -> 'SquareWaveFrame':
        """Unpack from 4 bytes"""
        bits = struct.unpack('<I', data)[0]
        return SquareWaveFrame.from_bits(bits)

# ═══════════════════════════════════════════════════════════════════════════
# PTOS Dictionary for Musical Patterns
# ═══════════════════════════════════════════════════════════════════════════

class MusicalPattern(Enum):
    """Common musical patterns as PTOS dictionary entries"""
    # Silence/rest
    SILENCE = 0x00
    
    # Standard duty cycles
    SQUARE_50 = 0x01      # 50% duty, no sweep
    SQUARE_25 = 0x02      # 25% duty, no sweep
    SQUARE_12_5 = 0x03    # 12.5% duty, no sweep
    SQUARE_75 = 0x04      # 75% duty, no sweep
    
    # Common musical intervals (relative frequencies)
    UNISON = 0x10         # Same frequency
    OCTAVE_UP = 0x11      # Frequency × 2
    OCTAVE_DOWN = 0x12    # Frequency / 2
    FIFTH_UP = 0x13       # Frequency × 1.5
    FIFTH_DOWN = 0x14     # Frequency / 1.5
    FOURTH_UP = 0x15      # Frequency × 1.33
    FOURTH_DOWN = 0x16    # Frequency / 1.33
    
    # Volume envelopes
    VOLUME_ATTACK = 0x20  # Volume increasing
    VOLUME_DECAY = 0x21   # Volume decreasing
    VOLUME_SUSTAIN = 0x22 # Volume sustained
    VOLUME_RELEASE = 0x23  # Volume releasing
    
    # Sweep effects
    SWEEP_UP = 0x30       # Frequency sweep up
    SWEEP_DOWN = 0x31     # Frequency sweep down
    SWEEP_NONE = 0x32      # No sweep
    
    # Frequency ranges
    BASS_LOW = 0x40       # 55-110 Hz
    BASS_MID = 0x41       # 110-220 Hz
    MID_LOW = 0x42        # 220-440 Hz
    MID_MID = 0x43        # 440-880 Hz
    MID_HIGH = 0x44       # 880-1760 Hz
    TREBLE_LOW = 0x45     # 1760-3520 Hz
    TREBLE_HIGH = 0x46    # 3520-7040 Hz
    
    # Special effects
    VIBRATO = 0x50        # Frequency modulation
    TREMOLO = 0x51        # Amplitude modulation
    ARPEGGIO = 0x52       # Rapid frequency changes

# ═══════════════════════════════════════════════════════════════════════════
# Delta Encoding
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class DeltaEncoding:
    """Delta encoding result"""
    has_delta: bool
    changed_fields: List[str]
    delta_bits: int
    
def compute_delta(current: SquareWaveFrame, previous: Optional[SquareWaveFrame]) -> DeltaEncoding:
    """Compute delta between two frames"""
    if previous is None:
        return DeltaEncoding(
            has_delta=False,
            changed_fields=[],
            delta_bits=0
        )
    
    changed_fields = []
    delta_bits = 0
    
    if current.frequency != previous.frequency:
        changed_fields.append('frequency')
        delta_bits += 11
    
    if current.duty != previous.duty:
        changed_fields.append('duty')
        delta_bits += 2
    
    if current.volume != previous.volume:
        changed_fields.append('volume')
        delta_bits += 4
    
    if current.sweep_enable != previous.sweep_enable:
        changed_fields.append('sweep_enable')
        delta_bits += 1
    
    if current.sweep_period != previous.sweep_period:
        changed_fields.append('sweep_period')
        delta_bits += 3
    
    if current.sweep_direction != previous.sweep_direction:
        changed_fields.append('sweep_direction')
        delta_bits += 1
    
    if current.sweep_shift != previous.sweep_shift:
        changed_fields.append('sweep_shift')
        delta_bits += 3
    
    return DeltaEncoding(
        has_delta=len(changed_fields) > 0,
        changed_fields=changed_fields,
        delta_bits=delta_bits
    )

# ═══════════════════════════════════════════════════════════════════════════
# GCL Compressed Frame
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class GCLCompressedFrame:
    """GCL-compressed square wave frame"""
    marker: str           # 'D' for delta, 'F' for full, 'P' for pattern
    pattern_byte: int     # PTOS dictionary index (if pattern)
    field_codes: int      # Changed field codes (if delta)
    frequency_delta: int  # Frequency delta (if changed)
    duty_delta: int       # Duty delta (if changed)
    volume_delta: int     # Volume delta (if changed)
    sweep_delta: int      # Sweep parameters delta (if changed)
    
    def to_bytes(self) -> bytes:
        """Pack into bytes"""
        result = bytearray()
        result.append(ord(self.marker))
        
        if self.marker == 'P':
            result.append(self.pattern_byte)
        elif self.marker == 'D':
            result.append(self.field_codes)
            if self.field_codes & 0x01:  # frequency changed
                result.extend(struct.pack('<h', self.frequency_delta))  # signed short
            if self.field_codes & 0x02:  # duty changed
                result.append(self.duty_delta & 0xFF)  # unsigned byte
            if self.field_codes & 0x04:  # volume changed
                result.extend(struct.pack('<b', self.volume_delta))  # signed byte
            if self.field_codes & 0x08:  # sweep changed
                result.append(self.sweep_delta & 0xFF)  # unsigned byte
        elif self.marker == 'F':
            # Full frame: pack all parameters
            result.extend(struct.pack('<H', self.frequency_delta))  # frequency (unsigned)
            result.append(self.duty_delta & 0xFF)  # duty (unsigned)
            result.append(self.volume_delta & 0xFF)  # volume (unsigned)
            result.append(self.sweep_delta & 0xFF)  # sweep packed (unsigned)
        
        return bytes(result)

def compress_frame(frame: SquareWaveFrame, previous: Optional[SquareWaveFrame] = None) -> GCLCompressedFrame:
    """Compress a single frame using GCL"""
    delta = compute_delta(frame, previous)
    
    # Check for pattern match (simple heuristic)
    if not delta.has_delta and previous is not None:
        # No change - could be silence or sustain
        if frame.volume == 0:
            return GCLCompressedFrame(
                marker='P',
                pattern_byte=MusicalPattern.SILENCE.value,
                field_codes=0,
                frequency_delta=0,
                duty_delta=0,
                volume_delta=0,
                sweep_delta=0
            )
        elif frame.frequency == previous.frequency:
            return GCLCompressedFrame(
                marker='P',
                pattern_byte=MusicalPattern.VOLUME_SUSTAIN.value,
                field_codes=0,
                frequency_delta=0,
                duty_delta=0,
                volume_delta=0,
                sweep_delta=0
            )
    
    if delta.has_delta and previous is not None:
        # Delta encoding
        field_codes = 0
        if 'frequency' in delta.changed_fields:
            field_codes |= 0x01
        if 'duty' in delta.changed_fields:
            field_codes |= 0x02
        if 'volume' in delta.changed_fields:
            field_codes |= 0x04
        if 'sweep_enable' in delta.changed_fields or 'sweep_period' in delta.changed_fields or \
           'sweep_direction' in delta.changed_fields or 'sweep_shift' in delta.changed_fields:
            field_codes |= 0x08
        
        # Pack sweep parameters into single byte
        sweep_packed = 0
        if 'sweep_enable' in delta.changed_fields:
            sweep_packed |= (int(frame.sweep_enable) & 1) << 7
        if 'sweep_period' in delta.changed_fields:
            sweep_packed |= (frame.sweep_period & 0x7) << 4
        if 'sweep_direction' in delta.changed_fields:
            sweep_packed |= (int(frame.sweep_direction) & 1) << 3
        if 'sweep_shift' in delta.changed_fields:
            sweep_packed |= (frame.sweep_shift & 0x7) << 0
        
        return GCLCompressedFrame(
            marker='D',
            pattern_byte=0,
            field_codes=field_codes,
            frequency_delta=frame.frequency - previous.frequency if 'frequency' in delta.changed_fields else 0,
            duty_delta=frame.duty.value - previous.duty.value if 'duty' in delta.changed_fields else 0,
            volume_delta=frame.volume - previous.volume if 'volume' in delta.changed_fields else 0,
            sweep_delta=sweep_packed
        )
    else:
        # Full frame
        sweep_packed = (int(frame.sweep_enable) & 1) << 7 | \
                       (frame.sweep_period & 0x7) << 4 | \
                       (int(frame.sweep_direction) & 1) << 3 | \
                       (frame.sweep_shift & 0x7) << 0
        
        return GCLCompressedFrame(
            marker='F',
            pattern_byte=0,
            field_codes=0,
            frequency_delta=frame.frequency,
            duty_delta=frame.duty.value,
            volume_delta=frame.volume,
            sweep_delta=sweep_packed
        )

def decompress_frame(compressed: GCLCompressedFrame, previous: Optional[SquareWaveFrame] = None) -> SquareWaveFrame:
    """Decompress a single frame"""
    if compressed.marker == 'F':
        # Full frame
        sweep_enable = bool((compressed.sweep_delta >> 7) & 1)
        sweep_period = (compressed.sweep_delta >> 4) & 0x7
        sweep_direction = bool((compressed.sweep_delta >> 3) & 1)
        sweep_shift = compressed.sweep_delta & 0x7
        
        return SquareWaveFrame(
            frequency=compressed.frequency_delta,
            duty=DutyCycle(compressed.duty_delta),
            volume=compressed.volume_delta,
            sweep_enable=sweep_enable,
            sweep_period=sweep_period,
            sweep_direction=sweep_direction,
            sweep_shift=sweep_shift
        )
    elif compressed.marker == 'D':
        # Delta frame
        if previous is None:
            raise ValueError("Delta decompression requires previous frame")
        
        frequency = previous.frequency
        duty = previous.duty
        volume = previous.volume
        sweep_enable = previous.sweep_enable
        sweep_period = previous.sweep_period
        sweep_direction = previous.sweep_direction
        sweep_shift = previous.sweep_shift
        
        if compressed.field_codes & 0x01:  # frequency
            frequency = previous.frequency + compressed.frequency_delta
        if compressed.field_codes & 0x02:  # duty
            duty = DutyCycle((previous.duty.value + compressed.duty_delta) & 0x3)
        if compressed.field_codes & 0x04:  # volume
            volume = (previous.volume + compressed.volume_delta) & 0xF
        if compressed.field_codes & 0x08:  # sweep
            sweep_enable = bool((compressed.sweep_delta >> 7) & 1)
            sweep_period = (compressed.sweep_delta >> 4) & 0x7
            sweep_direction = bool((compressed.sweep_delta >> 3) & 1)
            sweep_shift = compressed.sweep_delta & 0x7
        
        return SquareWaveFrame(
            frequency=frequency,
            duty=duty,
            volume=volume,
            sweep_enable=sweep_enable,
            sweep_period=sweep_period,
            sweep_direction=sweep_direction,
            sweep_shift=sweep_shift
        )
    elif compressed.marker == 'P':
        # Pattern frame
        if previous is None:
            # Default to silence
            return SquareWaveFrame(
                frequency=0,
                duty=DutyCycle.DUTY_50,
                volume=0,
                sweep_enable=False,
                sweep_period=0,
                sweep_direction=False,
                sweep_shift=0
            )
        
        pattern = MusicalPattern(compressed.pattern_byte)
        
        if pattern == MusicalPattern.SILENCE:
            return SquareWaveFrame(
                frequency=previous.frequency,
                duty=previous.duty,
                volume=0,
                sweep_enable=False,
                sweep_period=0,
                sweep_direction=False,
                sweep_shift=0
            )
        elif pattern == MusicalPattern.VOLUME_SUSTAIN:
            return previous
        else:
            # For other patterns, return previous (simplified)
            return previous
    else:
        raise ValueError(f"Unknown marker: {compressed.marker}")

# ═══════════════════════════════════════════════════════════════════════════
# Stream Compression/Decompression
# ═══════════════════════════════════════════════════════════════════════════

def compress_stream(frames: List[SquareWaveFrame]) -> bytes:
    """Compress a stream of frames"""
    result = bytearray()
    previous = None
    
    for frame in frames:
        compressed = compress_frame(frame, previous)
        result.extend(compressed.to_bytes())
        previous = frame
    
    return bytes(result)

def decompress_stream(data: bytes, frame_count: int) -> List[SquareWaveFrame]:
    """Decompress a stream of frames"""
    frames = []
    offset = 0
    previous = None
    
    for _ in range(frame_count):
        if offset >= len(data):
            break
        
        marker = chr(data[offset])
        offset += 1
        
        if marker == 'P':
            pattern_byte = data[offset]
            offset += 1
            compressed = GCLCompressedFrame(
                marker=marker,
                pattern_byte=pattern_byte,
                field_codes=0,
                frequency_delta=0,
                duty_delta=0,
                volume_delta=0,
                sweep_delta=0
            )
        elif marker == 'D':
            field_codes = data[offset]
            offset += 1
            
            freq_delta = 0
            duty_delta = 0
            vol_delta = 0
            sweep_delta = 0
            
            if field_codes & 0x01:
                freq_delta = struct.unpack('<h', data[offset:offset+2])[0]  # signed short
                offset += 2
            if field_codes & 0x02:
                duty_delta = data[offset]  # unsigned byte
                offset += 1
            if field_codes & 0x04:
                vol_delta = struct.unpack('<b', data[offset:offset+1])[0]  # signed byte
                offset += 1
            if field_codes & 0x08:
                sweep_delta = data[offset]  # unsigned byte
                offset += 1
            
            compressed = GCLCompressedFrame(
                marker=marker,
                pattern_byte=0,
                field_codes=field_codes,
                frequency_delta=freq_delta,
                duty_delta=duty_delta,
                volume_delta=vol_delta,
                sweep_delta=sweep_delta
            )
        elif marker == 'F':
            freq = struct.unpack('<H', data[offset:offset+2])[0]
            offset += 2
            duty = data[offset]
            offset += 1
            vol = data[offset]
            offset += 1
            sweep = data[offset]
            offset += 1
            
            compressed = GCLCompressedFrame(
                marker=marker,
                pattern_byte=0,
                field_codes=0,
                frequency_delta=freq,
                duty_delta=duty,
                volume_delta=vol,
                sweep_delta=sweep
            )
        else:
            raise ValueError(f"Unknown marker: {marker}")
        
        frame = decompress_frame(compressed, previous)
        frames.append(frame)
        previous = frame
    
    return frames

# ═══════════════════════════════════════════════════════════════════════════
# Cartridge ROM Format
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CartridgeHeader:
    """NES cartridge header for GCL audio"""
    magic: bytes = b'GCLA'  # Magic bytes
    version: int = 1       # Format version
    frame_count: int = 0   # Number of frames
    sample_rate: int = 240  # NES APU sample rate (240 Hz for square updates)
    compressed_size: int = 0  # Size of compressed data
    
    def to_bytes(self) -> bytes:
        return struct.pack('<4sHHII', self.magic, self.version, self.frame_count, 
                          self.sample_rate, self.compressed_size)
    
    @staticmethod
    def from_bytes(data: bytes) -> 'CartridgeHeader':
        magic, version, frame_count, sample_rate, compressed_size = \
            struct.unpack('<4sHHII', data[:16])
        return CartridgeHeader(magic, version, frame_count, sample_rate, compressed_size)

def create_cartridge(frames: List[SquareWaveFrame]) -> bytes:
    """Create a cartridge ROM image with compressed audio"""
    compressed = compress_stream(frames)
    header = CartridgeHeader(
        frame_count=len(frames),
        compressed_size=len(compressed)
    )
    
    return header.to_bytes() + compressed

def load_cartridge(data: bytes) -> List[SquareWaveFrame]:
    """Load frames from cartridge ROM image"""
    header = CartridgeHeader.from_bytes(data[:16])
    compressed_data = data[16:16+header.compressed_size]
    return decompress_stream(compressed_data, header.frame_count)

# ═══════════════════════════════════════════════════════════════════════════
# Test / Demo
# ═══════════════════════════════════════════════════════════════════════════

def generate_test_sequence() -> List[SquareWaveFrame]:
    """Generate a test square wave sequence"""
    frames = []
    
    # A major scale (A4: 440Hz)
    # NES frequency divider: CPU_freq / (16 * (divider + 1))
    # CPU_freq = 1.79MHz, so for 440Hz: divider ≈ 254
    base_freq = 254
    
    # Frequencies for A major scale
    frequencies = [
        base_freq,        # A4
        base_freq // 2,   # A5 (octave up, divider down)
        base_freq // 2 * 2 // 3,  # E5 (fifth)
        base_freq // 2 * 3 // 4,  # D5 (fourth)
        base_freq // 2 * 4 // 5,  # C#5 (major third)
        base_freq // 2 * 5 // 6,  # B4 (major second)
        base_freq,        # A4
        base_freq // 2,   # A5
    ]
    
    for freq in frequencies:
        # Attack: volume ramps up
        for vol in range(0, 16, 2):
            frames.append(SquareWaveFrame(
                frequency=freq,
                duty=DutyCycle.DUTY_50,
                volume=vol,
                sweep_enable=False,
                sweep_period=0,
                sweep_direction=False,
                sweep_shift=0
            ))
        
        # Sustain: hold volume
        for _ in range(10):
            frames.append(SquareWaveFrame(
                frequency=freq,
                duty=DutyCycle.DUTY_50,
                volume=15,
                sweep_enable=False,
                sweep_period=0,
                sweep_direction=False,
                sweep_shift=0
            ))
        
        # Release: volume ramps down
        for vol in range(14, -1, -2):
            frames.append(SquareWaveFrame(
                frequency=freq,
                duty=DutyCycle.DUTY_50,
                volume=vol,
                sweep_enable=False,
                sweep_period=0,
                sweep_direction=False,
                sweep_shift=0
            ))
    
    return frames

def run_test():
    """Run compression test"""
    print("=" * 70)
    print("NES SQUARE WAVE GCL STREAMING TEST")
    print("=" * 70)
    
    # Generate test sequence
    frames = generate_test_sequence()
    print(f"\n[*] Generated {len(frames)} frames")
    
    # Calculate uncompressed size
    uncompressed_size = len(frames) * 4  # 4 bytes per frame
    print(f"[*] Uncompressed size: {uncompressed_size} bytes")
    
    # Compress
    compressed = compress_stream(frames)
    print(f"[*] Compressed size: {len(compressed)} bytes")
    print(f"[*] Compression ratio: {uncompressed_size / len(compressed):.2f}×")
    print(f"[*] Space saved: {100 * (1 - len(compressed) / uncompressed_size):.1f}%")
    
    # Create cartridge
    cartridge = create_cartridge(frames)
    print(f"[*] Cartridge size (with header): {len(cartridge)} bytes")
    
    # Decompress and verify
    decompressed = load_cartridge(cartridge)
    print(f"[*] Decompressed {len(decompressed)} frames")
    
    # Verify integrity
    errors = 0
    for i, (orig, decomp) in enumerate(zip(frames, decompressed)):
        if orig.to_bits() != decomp.to_bits():
            errors += 1
            if errors <= 5:  # Show first 5 errors
                print(f"  [!] Frame {i}: Mismatch")
                print(f"      Original: {orig.to_bits():025b}")
                print(f"      Decompressed: {decomp.to_bits():025b}")
    
    if errors == 0:
        print("[✓] All frames verified successfully")
    else:
        print(f"[✗] {errors} frames failed verification")
    
    # Analyze compression statistics
    delta_frames = sum(1 for f in frames if compute_delta(f, (frames[i-1] if i > 0 else None)).has_delta)
    full_frames = len(frames) - delta_frames
    pattern_frames = sum(1 for i, f in enumerate(frames) 
                        if not compute_delta(f, (frames[i-1] if i > 0 else None)).has_delta and f.volume == 0)
    
    print(f"\n[*] Compression statistics:")
    print(f"    Delta frames: {delta_frames} ({100*delta_frames/len(frames):.1f}%)")
    print(f"    Full frames: {full_frames} ({100*full_frames/len(frames):.1f}%)")
    print(f"    Pattern frames (silence): {pattern_frames} ({100*pattern_frames/len(frames):.1f}%)")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    run_test()
