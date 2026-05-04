#!/usr/bin/env python3
"""
Palette Generator Slaved to DSP Math
NES palette generator (proto-shader) controlled by DSP math operations on audio lines.

Architecture:
- DSP math on audio lines generates values
- Values control NES palette generator
- Palette generator affects visual output
- Feedback loop: audio → math → palette → visual

This is horrific because:
- Audio DSP math controls video palette
- Cross-domain repurposing (audio → video)
- Palette generator becomes slave to computation

This is wonderful because:
- Video synthesizer controlled by audio math
- Generative visuals from DSP operations
- Maximum retro insanity: audio math = video palette
"""

import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════
# NES Palette Generator (Proto-Shader)
# Generates NES palette colors from parameters
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class NESColor:
    """NES color (RGB, 2 bits per channel)"""
    r: int  # 0-3
    g: int  # 0-3
    b: int  # 0-3
    
    def to_index(self) -> int:
        """Convert to NES palette index (0-63)"""
        return (self.r << 4) | (self.g << 2) | self.b
    
    @staticmethod
    def from_index(index: int) -> 'NESColor':
        """Convert from NES palette index"""
        return NESColor(
            r=(index >> 4) & 0x03,
            g=(index >> 2) & 0x03,
            b=index & 0x03
        )
    
    def to_rgb888(self) -> Tuple[int, int, int]:
        """Convert to 8-bit RGB"""
        return (self.r * 85, self.g * 85, self.b * 85)

class PaletteGenerator:
    """NES palette generator acting as proto-shader"""
    
    @staticmethod
    def generate_color(params: Tuple[float, float, float]) -> NESColor:
        """
        Generate NES color from parameters (x, y, t).
        
        This acts as a fragment shader - takes parameters and outputs color.
        """
        x, y, t = params
        
        # Map parameters to color channels
        # x → red, y → green, t → blue
        r = int((math.sin(x + t) + 1) * 1.5) % 4
        g = int((math.cos(y + t) + 1) * 1.5) % 4
        b = int((math.sin(x + y + t) + 1) * 1.5) % 4
        
        return NESColor(r, g, b)
    
    @staticmethod
    def generate_palette(num_colors: int, params: List[Tuple[float, float, float]]) -> List[NESColor]:
        """Generate a palette of colors"""
        palette = []
        for i in range(num_colors):
            if i < len(params):
                color = PaletteGenerator.generate_color(params[i])
            else:
                # Default color if no params
                color = NESColor(0, 0, 0)
            palette.append(color)
        return palette

# ═══════════════════════════════════════════════════════════════════════════
# DSP Math to Palette Control
# Map DSP math operations to palette generator parameters
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AudioSignal:
    """Audio signal from DSP math"""
    frequency: float
    amplitude: float
    duty_cycle: float

class DSPPaletteSlave:
    """DSP math slaved to control palette generator"""
    
    def __init__(self):
        self.palette_generator = PaletteGenerator()
        self.audio_history: List[AudioSignal] = []
        self.palette_history: List[List[NESColor]] = []
    
    def audio_to_palette_params(self, signal: AudioSignal) -> Tuple[float, float, float]:
        """
        Convert audio signal to palette generator parameters.
        
        Maps: frequency → x, amplitude → y, duty_cycle → t
        """
        # Normalize parameters to 0-2π range
        x = signal.frequency / 1000.0 * math.pi  # Normalize freq
        y = signal.amplitude * 2 * math.pi  # Normalize amplitude
        t = signal.duty_cycle * 2 * math.pi  # Normalize duty
        
        return (x, y, t)
    
    def dsp_to_palette(self, signals: List[AudioSignal]) -> List[NESColor]:
        """
        Convert DSP audio signals to palette.
        
        Each audio signal controls one palette entry.
        """
        params_list = [self.audio_to_palette_params(s) for s in signals]
        palette = self.palette_generator.generate_palette(len(signals), params_list)
        
        self.audio_history = signals
        self.palette_history.append(palette)
        
        return palette
    
    def dsp_operation_to_palette(self, operation: str, signals: List[AudioSignal]) -> List[NESColor]:
        """
        Perform DSP operation and convert result to palette.
        
        Operations: add, multiply, integrate, differentiate
        """
        if operation == "add":
            # Add signals: combine amplitudes
            combined_amp = sum(s.amplitude for s in signals)
            combined_freq = sum(s.frequency for s in signals) / len(signals)
            combined_duty = sum(s.duty_cycle for s in signals) / len(signals)
            combined = AudioSignal(combined_freq, combined_amp, combined_duty)
            return self.dsp_to_palette([combined])
        
        elif operation == "multiply":
            # Multiply signals: AM modulation
            if len(signals) >= 2:
                mul_amp = signals[0].amplitude * signals[1].amplitude
                mul_freq = math.sqrt(signals[0].frequency * signals[1].frequency)
                mul_duty = signals[0].duty_cycle if signals[0].duty_cycle >= 0.5 else 1.0 - signals[0].duty_cycle
                mul_duty *= signals[1].duty_cycle if signals[1].duty_cycle >= 0.5 else 1.0 - signals[1].duty_cycle
                combined = AudioSignal(mul_freq, mul_amp, mul_duty)
                return self.dsp_to_palette([combined])
        
        elif operation == "integrate":
            # Integrate: accumulate over history
            if self.audio_history:
                integrated = AudioSignal(
                    frequency=sum(s.frequency for s in self.audio_history + signals),
                    amplitude=sum(s.amplitude for s in self.audio_history + signals),
                    duty_cycle=sum(s.duty_cycle for s in self.audio_history + signals) / (len(self.audio_history) + len(signals))
                )
                return self.dsp_to_palette([integrated])
        
        elif operation == "differentiate":
            # Differentiate: rate of change
            if len(signals) >= 2:
                diff = AudioSignal(
                    frequency=signals[-1].frequency - signals[-2].frequency,
                    amplitude=signals[-1].amplitude - signals[-2].amplitude,
                    duty_cycle=signals[-1].duty_cycle - signals[-2].duty_cycle
                )
                return self.dsp_to_palette([diff])
        
        # Default: direct conversion
        return self.dsp_to_palette(signals)

# ═══════════════════════════════════════════════════════════════════════════
# Video Synthesizer
# Audio DSP math controls video palette generation
# ═══════════════════════════════════════════════════════════════════════════

class VideoSynthesizer:
    """Video synthesizer controlled by audio DSP math"""
    
    def __init__(self):
        self.dsp_slave = DSPPaletteSlave()
        self.frame_count = 0
    
    def generate_frame(self, audio_signals: List[AudioSignal], 
                      dsp_operation: str = "none") -> List[NESColor]:
        """
        Generate video frame from audio DSP math.
        
        Audio signals → DSP operation → Palette → Video frame
        """
        self.frame_count += 1
        
        if dsp_operation == "none":
            palette = self.dsp_slave.dsp_to_palette(audio_signals)
        else:
            palette = self.dsp_slave.dsp_operation_to_palette(dsp_operation, audio_signals)
        
        return palette
    
    def animate(self, base_signals: List[AudioSignal], 
               frames: int, dsp_operation: str = "none") -> List[List[NESColor]]:
        """
        Generate animation frames.
        
        Modulates audio signals over time to create animated palette.
        """
        animation = []
        
        for frame in range(frames):
            # Modulate signals over time
            modulated = []
            for i, signal in enumerate(base_signals):
                modulated_signal = AudioSignal(
                    frequency=signal.frequency * (1 + 0.1 * math.sin(frame * 0.1 + i)),
                    amplitude=signal.amplitude * (1 + 0.1 * math.cos(frame * 0.1 + i)),
                    duty_cycle=(signal.duty_cycle + 0.01 * math.sin(frame * 0.05 + i)) % 1.0
                )
                modulated.append(modulated_signal)
            
            frame_palette = self.generate_frame(modulated, dsp_operation)
            animation.append(frame_palette)
        
        return animation

# ═══════════════════════════════════════════════════════════════════════════
# Test / Demo
# ═══════════════════════════════════════════════════════════════════════════

def run_test():
    """Run palette generator slave to DSP math test"""
    print("=" * 70)
    print("PALETTE GENERATOR SLAVED TO DSP MATH")
    print("=" * 70)
    
    print("\n[*] Architecture:")
    print("    Audio DSP math → Palette generator parameters → Video palette")
    print("    Frequency → x (red channel)")
    print("    Amplitude → y (green channel)")
    print("    Duty cycle → t (blue channel)")
    print("    DSP operations (add, multiply, integrate) modulate palette")
    
    synthesizer = VideoSynthesizer()
    
    # Create base audio signals
    print("\n[*] Creating base audio signals...")
    base_signals = [
        AudioSignal(frequency=440.0, amplitude=0.5, duty_cycle=0.5),
        AudioSignal(frequency=880.0, amplitude=0.7, duty_cycle=0.25),
        AudioSignal(frequency=220.0, amplitude=0.3, duty_cycle=0.75),
    ]
    print(f"    Signal 1: {base_signals[0].frequency}Hz, amp={base_signals[0].amplitude}, duty={base_signals[0].duty_cycle}")
    print(f"    Signal 2: {base_signals[1].frequency}Hz, amp={base_signals[1].amplitude}, duty={base_signals[1].duty_cycle}")
    print(f"    Signal 3: {base_signals[2].frequency}Hz, amp={base_signals[2].amplitude}, duty={base_signals[2].duty_cycle}")
    
    # Direct conversion
    print("\n[*] Direct audio-to-palette conversion...")
    palette = synthesizer.generate_frame(base_signals, "none")
    print("    Palette generated:")
    for i, color in enumerate(palette):
        rgb = color.to_rgb888()
        print(f"      Entry {i}: R={rgb[0]}, G={rgb[1]}, B={rgb[2]} (index={color.to_index()})")
    
    # DSP addition
    print("\n[*] DSP addition (add signals)...")
    palette_add = synthesizer.generate_frame(base_signals, "add")
    print("    Palette after addition:")
    for i, color in enumerate(palette_add):
        rgb = color.to_rgb888()
        print(f"      Entry {i}: R={rgb[0]}, G={rgb[1]}, B={rgb[2]} (index={color.to_index()})")
    
    # DSP multiplication
    print("\n[*] DSP multiplication (AM modulation)...")
    palette_mul = synthesizer.generate_frame(base_signals, "multiply")
    print("    Palette after multiplication:")
    for i, color in enumerate(palette_mul):
        rgb = color.to_rgb888()
        print(f"      Entry {i}: R={rgb[0]}, G={rgb[1]}, B={rgb[2]} (index={color.to_index()})")
    
    # Animation
    print("\n[*] Generating 10-frame animation...")
    animation = synthesizer.animate(base_signals, frames=10, dsp_operation="multiply")
    print(f"    Animation generated: {len(animation)} frames")
    print("    Frame 0 palette:")
    for i, color in enumerate(animation[0]):
        rgb = color.to_rgb888()
        print(f"      Entry {i}: R={rgb[0]}, G={rgb[1]}, B={rgb[2]}")
    print("    Frame 5 palette:")
    for i, color in enumerate(animation[5]):
        rgb = color.to_rgb888()
        print(f"      Entry {i}: R={rgb[0]}, G={rgb[1]}, B={rgb[2]}")
    
    print("\n" + "=" * 70)
    print("PALETTE-DSP SLAVE SYSTEM COMPLETE")
    print("=" * 70)
    print("\n[*] Horrific: Audio DSP math controls video palette")
    print("[*] Wonderful: Video synthesizer from audio computation")
    print("[*] Maximum retro insanity: audio math = video palette")

if __name__ == "__main__":
    run_test()
