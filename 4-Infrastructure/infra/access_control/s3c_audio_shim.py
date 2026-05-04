#!/usr/bin/env python3
"""
S3C Audio Shim for Sound Card Testing
Extracts S3C manifold processing from Lean for main machine sound card testing
"""

import numpy as np
import json
from dataclasses import dataclass
from typing import Optional, Tuple
import sys

# Try to import pyaudio for sound card testing
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: pyaudio not available. Sound card testing disabled.")
    print("Install with: pip install pyaudio")

@dataclass
class ShellCoords:
    """Shell coordinates for integer decomposition n = k^2 + a"""
    k: int  # Shell index (coarse handle)
    a: int  # Lower offset (medium handle)
    b: int  # Upper offset (fine handle)
    mass: int  # Intersection form a*b
    width: int  # Shell width = 2k+1 = a+b+1

@dataclass
class ManifoldHandle:
    """3-handle manifold structure for soundwave features"""
    handleK: int  # Coarse handle (amplitude envelope)
    handleA: int  # Medium handle (spectral content)
    handleB: int  # Fine handle (phase information)

@dataclass
class ThreePointContact:
    """3-point contact detection"""
    kappaA: bool  # Forward spectral prediction
    kappaB: bool  # Temporal midpoint
    kappaC: bool  # Backward phase correction

@dataclass
class JScore:
    """J-score interaction: J(n) = ab*F_m + (a-b)*F_p + <chi, F_c>"""
    massResonance: int  # ab*F_m
    mirrorResonance: int  # (a-b)*F_p
    spectralCoupling: int  # <chi, F_c>
    total: int  # J(n)

@dataclass
class S3CState:
    """S3C audio processing state"""
    sample: int
    handles: ManifoldHandle
    contact: ThreePointContact
    jScore: JScore
    emit: bool

def shell_decomposition(n: int) -> ShellCoords:
    """Compute shell decomposition n = k^2 + a"""
    k = int(np.sqrt(n))
    k_sq = k * k
    a = n - k_sq
    k1_sq = (k + 1) * (k + 1)
    b = k1_sq - n
    mass = a * b
    width = a + b + 1
    return ShellCoords(k=k, a=a, b=b, mass=mass, width=width)

def audio_to_manifold(sample: int) -> ManifoldHandle:
    """Map audio sample to 3-handle manifold"""
    coords = shell_decomposition(sample)
    return ManifoldHandle(
        handleK=coords.k,
        handleA=coords.a,
        handleB=coords.b
    )

def detect_contact(handles: ManifoldHandle) -> ThreePointContact:
    """Detect 3-point contact from manifold handles"""
    kappaA = handles.handleA > 0
    kappaB = handles.handleK > 0
    kappaC = handles.handleB > 0
    return ThreePointContact(kappaA=kappaA, kappaB=kappaB, kappaC=kappaC)

def compute_j_score(handles: ManifoldHandle) -> JScore:
    """Compute J-score from manifold handles"""
    massResonance = handles.handleA * handles.handleB  # ab
    mirrorResonance = abs(handles.handleA - handles.handleB)  # |a-b|
    spectralCoupling = handles.handleK  # chi ~ k
    total = massResonance + mirrorResonance + spectralCoupling
    return JScore(
        massResonance=massResonance,
        mirrorResonance=mirrorResonance,
        spectralCoupling=spectralCoupling,
        total=total
    )

def emission_gate(contact: ThreePointContact, jScore: JScore) -> bool:
    """Emission gate: emit only if kappa_A AND kappa_C AND J > 0"""
    return contact.kappaA and contact.kappaC and jScore.total > 0

def process_audio_sample(sample: int) -> S3CState:
    """Process audio sample through S3C manifold"""
    handles = audio_to_manifold(sample)
    contact = detect_contact(handles)
    jScore = compute_j_score(handles)
    emit = emission_gate(contact, jScore)
    return S3CState(
        sample=sample,
        handles=handles,
        contact=contact,
        jScore=jScore,
        emit=emit
    )

def progressive_binding_cost(n: int) -> float:
    """1/n progressive binding cost"""
    if n == 0:
        return 1.0
    return 1.0 / n

def is_throat(handles: ManifoldHandle) -> bool:
    """Throat blending at a = b (shell midpoint)"""
    return handles.handleA == handles.handleB

class S3CAudioProcessor:
    """S3C audio processor for sound card testing"""
    
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 1024):
        if not PYAUDIO_AVAILABLE:
            raise RuntimeError("pyaudio not available. Install with: pip install pyaudio")
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.paudio = pyaudio.PyAudio()
        self.stream = None
        self.emitted_count = 0
        self.total_count = 0
        
    def start_input(self):
        """Start audio input stream"""
        self.stream = self.paudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
    def stop(self):
        """Stop audio stream"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.paudio.terminate()
        
    def process_chunk(self, chunk: np.ndarray) -> list:
        """Process audio chunk through S3C manifold"""
        results = []
        for sample in chunk:
            # Convert 16-bit signed to unsigned
            unsigned_sample = int(sample) + 32768
            state = process_audio_sample(unsigned_sample)
            results.append(state)
            self.total_count += 1
            if state.emit:
                self.emitted_count += 1
        return results
        
    def get_emission_rate(self) -> float:
        """Get emission rate"""
        if self.total_count == 0:
            return 0.0
        return self.emitted_count / self.total_count
        
    def process_audio_stream(self, duration_seconds: float = 5.0) -> dict:
        """Process audio stream for specified duration"""
        self.start_input()
        
        results = []
        try:
            chunks = int(self.sample_rate * duration_seconds / self.chunk_size)
            for i in range(chunks):
                data = self.stream.read(self.chunk_size)
                chunk = np.frombuffer(data, dtype=np.int16)
                chunk_results = self.process_chunk(chunk)
                results.extend(chunk_results)
                
                # Print progress
                if i % 10 == 0:
                    print(f"Processed chunk {i}/{chunks}, emission rate: {self.get_emission_rate():.3f}")
                    
        finally:
            self.stop()
            
        return {
            'total_samples': self.total_count,
            'emitted_samples': self.emitted_count,
            'emission_rate': self.get_emission_rate(),
            'results': results[:100]  # Return first 100 results for analysis
        }

def main():
    """Main entry point for S3C audio testing"""
    print("S3C Audio Processor - Sound Card Testing")
    print("=" * 50)
    
    # Test with synthetic data first
    print("\nTesting with synthetic audio samples...")
    test_samples = [100, 256, 1000, 5000, 10000]
    for sample in test_samples:
        state = process_audio_sample(sample)
        print(f"Sample {sample}: k={state.handles.handleK}, a={state.handles.handleA}, b={state.handles.handleB}, "
              f"mass={state.jScore.massResonance}, emit={state.emit}")
    
    # Test with sound card if requested
    if len(sys.argv) > 1 and sys.argv[1] == '--soundcard':
        if not PYAUDIO_AVAILABLE:
            print("\nError: pyaudio not available. Cannot test with sound card.")
            print("Install with: pip install pyaudio")
            sys.exit(1)
            
        print("\nInitializing sound card...")
        processor = S3CAudioProcessor(sample_rate=44100, chunk_size=1024)
        
        print("Processing audio stream (5 seconds)...")
        print("Speak or play audio to test S3C manifold processing...")
        
        results = processor.process_audio_stream(duration_seconds=5.0)
        
        print("\n" + "=" * 50)
        print("Results:")
        print(f"Total samples: {results['total_samples']}")
        print(f"Emitted samples: {results['emitted_samples']}")
        print(f"Emission rate: {results['emission_rate']:.3f}")
        
        # Save results to JSON
        with open('/home/allaun/Documents/Research Stack/data/s3c_audio_test_results.json', 'w') as f:
            # Convert dataclasses to dicts for JSON serialization
            serializable_results = []
            for state in results['results']:
                serializable_results.append({
                    'sample': state.sample,
                    'handles': {
                        'handleK': state.handles.handleK,
                        'handleA': state.handles.handleA,
                        'handleB': state.handles.handleB
                    },
                    'contact': {
                        'kappaA': state.contact.kappaA,
                        'kappaB': state.contact.kappaB,
                        'kappaC': state.contact.kappaC
                    },
                    'jScore': {
                        'massResonance': state.jScore.massResonance,
                        'mirrorResonance': state.jScore.mirrorResonance,
                        'spectralCoupling': state.jScore.spectralCoupling,
                        'total': state.jScore.total
                    },
                    'emit': state.emit
                })
            
            json.dump({
                'total_samples': results['total_samples'],
                'emitted_samples': results['emitted_samples'],
                'emission_rate': results['emission_rate'],
                'results': serializable_results
            }, f, indent=2)
        
        print(f"\nResults saved to /home/allaun/Documents/Research Stack/data/s3c_audio_test_results.json")
    else:
        print("\nTo test with sound card, run:")
        print("python3 s3c_audio_shim.py --soundcard")

if __name__ == '__main__':
    main()
