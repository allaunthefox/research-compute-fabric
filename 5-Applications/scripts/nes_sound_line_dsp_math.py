#!/usr/bin/env python3
"""
NES Sound Line DSP Math - Horrifically Wonderful
Hijack NES audio output lines to perform DSP mathematical operations.

Architecture:
1. Encode mathematical values as audio signals (frequency/amplitude)
2. Use NES APU mixing/filtering as computational operations
3. Decode audio output back to mathematical results
4. Analog computation disguised as audio output

This is horrific because:
- Repurposes audio hardware for general computation
- Steganographic computation (hiding math in audio)
- Hybrid analog-digital computing on retro hardware
- Completely unexpected use of NES sound lines

This is wonderful because:
- Creative repurposing of hardware
- Novel computational paradigm
- Combines analog and digital computing
- Maximum retro insanity
"""

import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════
# NES Audio Lines (Analog Output)
# NES APU outputs 2 square wave channels, triangle, noise, DPCM
# These can be hijacked for DSP math operations
# ═══════════════════════════════════════════════════════════════════════════

class NESAudioLine(Enum):
    """NES audio output lines"""
    SQUARE1 = 0  # Square wave channel 1
    SQUARE2 = 1  # Square wave channel 2
    TRIANGLE = 2 # Triangle wave channel
    NOISE = 3    # Noise channel
    DPCM = 4     # DPCM channel

@dataclass
class AudioSignal:
    """Audio signal representing a mathematical value"""
    frequency: float  # Hz (represents value magnitude)
    amplitude: float  # 0.0-1.0 (represents value precision)
    duty_cycle: float = 0.5  # 0.0-1.0 (represents sign/phase)
    
    def to_value(self) -> float:
        """Convert audio signal to mathematical value"""
        # Frequency represents magnitude
        # Amplitude represents precision
        # Duty cycle represents sign
        sign = 1.0 if self.duty_cycle >= 0.5 else -1.0
        return sign * self.frequency * self.amplitude
    
    @staticmethod
    def from_value(value: float, base_freq: float = 440.0) -> 'AudioSignal':
        """Convert mathematical value to audio signal"""
        sign = 1.0 if value >= 0 else -1.0
        magnitude = abs(value)
        
        # Frequency represents magnitude (logarithmic scale)
        frequency = base_freq * (1.0 + magnitude)
        
        # Amplitude represents precision (normalize to 0-1)
        amplitude = min(magnitude / 1000.0, 1.0)
        
        # Duty cycle represents sign
        duty_cycle = 0.75 if sign > 0 else 0.25
        
        return AudioSignal(frequency, amplitude, duty_cycle)

# ═══════════════════════════════════════════════════════════════════════════
# DSP Operations Using NES APU
# Use APU mixing, filtering, and modulation as mathematical operations
# ═══════════════════════════════════════════════════════════════════════════

class NESDSPMath:
    """DSP mathematical operations using NES audio lines"""
    
    @staticmethod
    def add(signals: List[AudioSignal]) -> AudioSignal:
        """
        Addition: Mix audio signals (APU mixing).
        
        In NES APU, multiple channels are mixed together.
        This mixing operation can represent addition.
        """
        if not signals:
            return AudioSignal(0, 0, 0.5)
        
        # Mix frequencies (weighted average)
        total_freq = sum(s.frequency * s.amplitude for s in signals)
        total_amp = sum(s.amplitude for s in signals)
        
        if total_amp == 0:
            return AudioSignal(0, 0, 0.5)
        
        avg_freq = total_freq / total_amp
        avg_amp = min(total_amp / len(signals), 1.0)
        
        # Determine sign from majority duty cycle
        positive_count = sum(1 for s in signals if s.duty_cycle >= 0.5)
        duty_cycle = 0.75 if positive_count > len(signals) / 2 else 0.25
        
        return AudioSignal(avg_freq, avg_amp, duty_cycle)
    
    @staticmethod
    def multiply(signal1: AudioSignal, signal2: AudioSignal) -> AudioSignal:
        """
        Multiplication: Modulate amplitude.
        
        In NES APU, amplitude modulation can represent multiplication.
        """
        # Multiply amplitudes
        new_amp = signal1.amplitude * signal2.amplitude
        
        # Multiply frequencies (geometric mean for audio)
        new_freq = math.sqrt(signal1.frequency * signal2.frequency)
        
        # XOR duty cycles for sign
        sign1 = 1 if signal1.duty_cycle >= 0.5 else -1
        sign2 = 1 if signal2.duty_cycle >= 0.5 else -1
        new_sign = sign1 * sign2
        new_duty = 0.75 if new_sign > 0 else 0.25
        
        return AudioSignal(new_freq, new_amp, new_duty)
    
    @staticmethod
    def subtract(signal1: AudioSignal, signal2: AudioSignal) -> AudioSignal:
        """
        Subtraction: Invert and add.
        
        In NES APU, phase inversion can represent negation.
        """
        # Invert signal2 (phase shift by 180° = duty cycle flip)
        inverted_signal2 = AudioSignal(
            signal2.frequency,
            signal2.amplitude,
            0.75 if signal2.duty_cycle < 0.5 else 0.25
        )
        
        return NESDSPMath.add([signal1, inverted_signal2])
    
    @staticmethod
    def divide(signal1: AudioSignal, signal2: AudioSignal) -> AudioSignal:
        """
        Division: Frequency ratio.
        
        In NES APU, frequency division can represent division.
        """
        if signal2.frequency == 0:
            return AudioSignal(0, 0, 0.5)
        
        # Divide frequencies
        new_freq = signal1.frequency / signal2.frequency
        
        # Divide amplitudes
        new_amp = signal1.amplitude / signal2.amplitude if signal2.amplitude > 0 else 0
        
        # XOR duty cycles for sign
        sign1 = 1 if signal1.duty_cycle >= 0.5 else -1
        sign2 = 1 if signal2.duty_cycle >= 0.5 else -1
        new_sign = sign1 * sign2
        new_duty = 0.75 if new_sign > 0 else 0.25
        
        return AudioSignal(new_freq, min(new_amp, 1.0), new_duty)
    
    @staticmethod
    def integrate(signals: List[AudioSignal]) -> AudioSignal:
        """
        Integration: Accumulate over time.
        
        In NES APU, envelope generation can represent integration.
        """
        if not signals:
            return AudioSignal(0, 0, 0.5)
        
        # Integrate frequencies (cumulative sum)
        total_freq = sum(s.frequency for s in signals)
        
        # Integrate amplitudes (cumulative sum, normalized)
        total_amp = min(sum(s.amplitude for s in signals), 1.0)
        
        # Use last signal's duty cycle
        duty_cycle = signals[-1].duty_cycle if signals else 0.5
        
        return AudioSignal(total_freq, total_amp, duty_cycle)
    
    @staticmethod
    def differentiate(signals: List[AudioSignal]) -> AudioSignal:
        """
        Differentiation: Rate of change.
        
        In NES APU, sweep modulation can represent differentiation.
        """
        if len(signals) < 2:
            return AudioSignal(0, 0, 0.5)
        
        # Differentiate frequencies (difference)
        freq_diff = signals[-1].frequency - signals[-2].frequency
        
        # Differentiate amplitudes (difference)
        amp_diff = signals[-1].amplitude - signals[-2].amplitude
        
        # Use last signal's duty cycle
        duty_cycle = signals[-1].duty_cycle
        
        return AudioSignal(abs(freq_diff), abs(amp_diff), duty_cycle)

# ═══════════════════════════════════════════════════════════════════════════
# DSP Math Pipeline
# Chain multiple DSP operations using NES audio lines
# ═══════════════════════════════════════════════════════════════════════════

class NESDSPPipeline:
    """Pipeline for DSP math operations on NES audio lines"""
    
    def __init__(self):
        self.channels: Dict[NESAudioLine, AudioSignal] = {
            NESAudioLine.SQUARE1: AudioSignal(0, 0, 0.5),
            NESAudioLine.SQUARE2: AudioSignal(0, 0, 0.5),
            NESAudioLine.TRIANGLE: AudioSignal(0, 0, 0.5),
            NESAudioLine.NOISE: AudioSignal(0, 0, 0.5),
        }
        self.history: List[Dict[NESAudioLine, AudioSignal]] = []
    
    def load_value(self, line: NESAudioLine, value: float, base_freq: float = 440.0):
        """Load mathematical value into audio line"""
        self.channels[line] = AudioSignal.from_value(value, base_freq)
    
    def add_channels(self, line1: NESAudioLine, line2: NESAudioLine, 
                    output_line: NESAudioLine):
        """Add two audio channels (mixing)"""
        result = NESDSPMath.add([self.channels[line1], self.channels[line2]])
        self.channels[output_line] = result
    
    def multiply_channels(self, line1: NESAudioLine, line2: NESAudioLine,
                         output_line: NESAudioLine):
        """Multiply two audio channels (amplitude modulation)"""
        result = NESDSPMath.multiply(self.channels[line1], self.channels[line2])
        self.channels[output_line] = result
    
    def subtract_channels(self, line1: NESAudioLine, line2: NESAudioLine,
                          output_line: NESAudioLine):
        """Subtract two audio channels (phase inversion + mixing)"""
        result = NESDSPMath.subtract(self.channels[line1], self.channels[line2])
        self.channels[output_line] = result
    
    def integrate_channel(self, line: NESAudioLine, output_line: NESAudioLine):
        """Integrate audio channel over time (envelope)"""
        # Get history for this channel
        channel_history = [state[line] for state in self.history]
        result = NESDSPMath.integrate(channel_history)
        self.channels[output_line] = result
    
    def differentiate_channel(self, line: NESAudioLine, output_line: NESAudioLine):
        """Differentiate audio channel (sweep)"""
        # Get history for this channel
        channel_history = [state[line] for state in self.history]
        result = NESDSPMath.differentiate(channel_history)
        self.channels[output_line] = result
    
    def tick(self):
        """Advance one time step (save history)"""
        self.history.append(self.channels.copy())
        if len(self.history) > 100:  # Keep last 100 states
            self.history.pop(0)
    
    def get_value(self, line: NESAudioLine) -> float:
        """Get mathematical value from audio line"""
        return self.channels[line].to_value()

# ═══════════════════════════════════════════════════════════════════════════
# Test / Demo
# ═══════════════════════════════════════════════════════════════════════════

def run_test():
    """Run NES sound line DSP math test"""
    print("=" * 70)
    print("NES SOUND LINE DSP MATH - HORRIFICALLY WONDERFUL")
    print("=" * 70)
    
    print("\n[*] Architecture:")
    print("    Encode: mathematical value → audio signal (freq/amp/duty)")
    print("    Compute: NES APU mixing/filtering/modulation")
    print("    Decode: audio signal → mathematical value")
    print("    Purpose: Hijack audio lines for general computation")
    
    # Create DSP pipeline
    pipeline = NESDSPPipeline()
    
    # Load test values
    print("\n[*] Loading test values into audio lines...")
    pipeline.load_value(NESAudioLine.SQUARE1, 100.0)
    pipeline.load_value(NESAudioLine.SQUARE2, 50.0)
    print("    SQUARE1: 100.0 → {} Hz".format(pipeline.channels[NESAudioLine.SQUARE1].frequency))
    print("    SQUARE2: 50.0 → {} Hz".format(pipeline.channels[NESAudioLine.SQUARE2].frequency))
    
    # Addition
    print("\n[*] Performing addition (mixing)...")
    pipeline.add_channels(NESAudioLine.SQUARE1, NESAudioLine.SQUARE2, NESAudioLine.TRIANGLE)
    result = pipeline.get_value(NESAudioLine.TRIANGLE)
    print("    Result: {:.2f} (expected: ~150.0)".format(result))
    
    # Multiplication
    print("\n[*] Performing multiplication (amplitude modulation)...")
    pipeline.multiply_channels(NESAudioLine.SQUARE1, NESAudioLine.SQUARE2, NESAudioLine.NOISE)
    result = pipeline.get_value(NESAudioLine.NOISE)
    print("    Result: {:.2f} (expected: ~5000.0)".format(result))
    
    # Subtraction
    print("\n[*] Performing subtraction (phase inversion + mixing)...")
    pipeline.subtract_channels(NESAudioLine.SQUARE1, NESAudioLine.SQUARE2, NESAudioLine.TRIANGLE)
    result = pipeline.get_value(NESAudioLine.TRIANGLE)
    print("    Result: {:.2f} (expected: ~50.0)".format(result))
    
    # Integration
    print("\n[*] Performing integration (envelope generation)...")
    for i in range(5):
        pipeline.load_value(NESAudioLine.SQUARE1, 10.0 * (i + 1))
        pipeline.tick()
    
    pipeline.integrate_channel(NESAudioLine.SQUARE1, NESAudioLine.TRIANGLE)
    result = pipeline.get_value(NESAudioLine.TRIANGLE)
    print("    Result: {:.2f} (expected: ~30.0)".format(result))
    
    # Differentiation
    print("\n[*] Performing differentiation (sweep modulation)...")
    pipeline.differentiate_channel(NESAudioLine.SQUARE1, NESAudioLine.NOISE)
    result = pipeline.get_value(NESAudioLine.NOISE)
    print("    Result: {:.2f} (expected: ~10.0)".format(result))
    
    print("\n" + "=" * 70)
    print("DSP MATH COMPLETE")
    print("=" * 70)
    print("\n[*] Horrific: Using audio lines for general computation")
    print("[*] Wonderful: Novel analog-digital hybrid computing")
    print("[*] Maximum retro insanity: NES APU as mathematical coprocessor")

if __name__ == "__main__":
    run_test()
