#!/usr/bin/env python3
"""
S3C PCM Wave File Processor
Applies S3C manifold processing to PCM wave files for accelerated testing
"""

import numpy as np
import json
import wave
import struct
from dataclasses import dataclass
from typing import List, Optional
import sys
import os

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

def read_pcm_file(filepath: str) -> np.ndarray:
    """Read PCM wave file"""
    try:
        with wave.open(filepath, 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)
            
            # Convert to numpy array based on sample width
            if params.sampwidth == 2:
                samples = np.frombuffer(frames, dtype=np.int16)
            elif params.sampwidth == 4:
                samples = np.frombuffer(frames, dtype=np.int32)
            else:
                raise ValueError(f"Unsupported sample width: {params.sampwidth}")
            
            print(f"PCM File Info:")
            print(f"  Channels: {params.nchannels}")
            print(f"  Sample width: {params.sampwidth} bytes")
            print(f"  Frame rate: {params.framerate} Hz")
            print(f"  Number of frames: {params.nframes}")
            print(f"  Duration: {params.nframes / params.framerate:.2f} seconds")
            
            return samples
    except Exception as e:
        print(f"Error reading PCM file: {e}")
        return np.array([])

def generate_sine_wave(frequency: int = 440, duration: float = 1.0, sample_rate: int = 44100, amplitude: int = 16000) -> np.ndarray:
    """Generate synthetic sine wave for testing"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    samples = (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
    return samples

def process_pcm_samples(samples: np.ndarray, max_samples: Optional[int] = None) -> dict:
    """Process PCM samples through S3C manifold"""
    if max_samples:
        samples = samples[:max_samples]
    
    results = []
    emitted_count = 0
    total_count = 0
    
    for sample in samples:
        # Convert signed to unsigned
        unsigned_sample = int(sample) + 32768
        state = process_audio_sample(unsigned_sample)
        results.append(state)
        total_count += 1
        if state.emit:
            emitted_count += 1
    
    return {
        'total_samples': total_count,
        'emitted_samples': emitted_count,
        'emission_rate': emitted_count / total_count if total_count > 0 else 0.0,
        'results': results
    }

def analyze_manifold_geometry(results: List[S3CState]) -> dict:
    """Analyze manifold geometry from S3C results"""
    k_values = [state.handles.handleK for state in results]
    a_values = [state.handles.handleA for state in results]
    b_values = [state.handles.handleB for state in results]
    mass_values = [state.jScore.massResonance for state in results]
    
    return {
        'k_stats': {
            'min': min(k_values),
            'max': max(k_values),
            'mean': np.mean(k_values),
            'std': np.std(k_values)
        },
        'a_stats': {
            'min': min(a_values),
            'max': max(a_values),
            'mean': np.mean(a_values),
            'std': np.std(a_values)
        },
        'b_stats': {
            'min': min(b_values),
            'max': max(b_values),
            'mean': np.mean(b_values),
            'std': np.std(b_values)
        },
        'mass_stats': {
            'min': min(mass_values),
            'max': max(mass_values),
            'mean': np.mean(mass_values),
            'std': np.std(mass_values)
        },
        'throat_count': sum(1 for state in results if state.handles.handleA == state.handles.handleB)
    }

def save_results(results: dict, output_path: str):
    """Save S3C processing results to JSON"""
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
    
    output_data = {
        'total_samples': results['total_samples'],
        'emitted_samples': results['emitted_samples'],
        'emission_rate': results['emission_rate'],
        'results': serializable_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Results saved to {output_path}")

def main():
    """Main entry point for S3C PCM processing"""
    print("S3C PCM Wave File Processor")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 s3c_pcm_processor.py <pcm_file.wav>")
        print("  python3 s3c_pcm_processor.py --sine [frequency] [duration]")
        print("\nExample:")
        print("  python3 s3c_pcm_processor.py audio.wav")
        print("  python3 s3c_pcm_processor.py --sine 440 2.0")
        sys.exit(1)
    
    # Parse arguments
    if sys.argv[1] == '--sine':
        # Generate synthetic sine wave
        frequency = int(sys.argv[2]) if len(sys.argv) > 2 else 440
        duration = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
        
        print(f"\nGenerating sine wave: {frequency} Hz, {duration} seconds")
        samples = generate_sine_wave(frequency=frequency, duration=duration)
        output_prefix = f"sine_{frequency}Hz_{duration}s"
    else:
        # Read PCM file
        filepath = sys.argv[1]
        if not os.path.exists(filepath):
            print(f"Error: File not found: {filepath}")
            sys.exit(1)
        
        print(f"\nReading PCM file: {filepath}")
        samples = read_pcm_file(filepath)
        if len(samples) == 0:
            print("Error: No samples found in file")
            sys.exit(1)
        
        output_prefix = os.path.splitext(os.path.basename(filepath))[0]
    
    # Process samples
    print(f"\nProcessing {len(samples)} samples through S3C manifold...")
    max_samples = min(len(samples), 100000)  # Limit to 100k samples for testing
    results = process_pcm_samples(samples, max_samples=max_samples)
    
    print(f"\nResults:")
    print(f"  Total samples: {results['total_samples']}")
    print(f"  Emitted samples: {results['emitted_samples']}")
    print(f"  Emission rate: {results['emission_rate']:.3f}")
    
    # Analyze manifold geometry
    print(f"\nAnalyzing manifold geometry...")
    geometry = analyze_manifold_geometry(results['results'])
    print(f"  k (coarse): min={geometry['k_stats']['min']}, max={geometry['k_stats']['max']}, mean={geometry['k_stats']['mean']:.2f}")
    print(f"  a (medium): min={geometry['a_stats']['min']}, max={geometry['a_stats']['max']}, mean={geometry['a_stats']['mean']:.2f}")
    print(f"  b (fine): min={geometry['b_stats']['min']}, max={geometry['b_stats']['max']}, mean={geometry['b_stats']['mean']:.2f}")
    print(f"  mass: min={geometry['mass_stats']['min']}, max={geometry['mass_stats']['max']}, mean={geometry['mass_stats']['mean']:.2f}")
    print(f"  Throat events (a=b): {geometry['throat_count']}")
    
    # Save results
    output_path = f"/home/allaun/Documents/Research Stack/data/s3c_{output_prefix}_results.json"
    save_results(results, output_path)
    
    # Save geometry analysis
    geometry_path = f"/home/allaun/Documents/Research Stack/data/s3c_{output_prefix}_geometry.json"
    with open(geometry_path, 'w') as f:
        json.dump(geometry, f, indent=2)
    print(f"Geometry analysis saved to {geometry_path}")

if __name__ == '__main__':
    main()
