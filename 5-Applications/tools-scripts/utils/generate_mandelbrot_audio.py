#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Generate Mandelbrot boundary sequence as audio for deterministic testing.

Following FRACTAL_TEST_PROCEDURE.md specification:
- Escape time algorithm, 256 iterations
- Resolution: 4096x4096
- Extraction: Boundary pixels where |iteration| = 255
- Sequence: Hilbert curve traversal order
- Convert to audio for hybrid DSP workload selector testing
"""

import struct
import wave
import os
from pathlib import Path

REPO_ROOT = Path(os.getenv("RESEARCH_STACK_ROOT") or Path(__file__).resolve().parents[1])

def mandelbrot(c: complex, max_iter: int = 256) -> int:
    """Compute Mandelbrot escape time for point c."""
    z = 0j
    for i in range(max_iter):
        if abs(z) > 2:
            return i
        z = z * z + c
    return max_iter

def generate_mandelbrot_boundary(width: int = 4096, height: int = 4096, max_iter: int = 256) -> list:
    """Generate Mandelbrot set boundary coordinates."""
    print(f"Generating Mandelbrot boundary ({width}x{height})...")
    
    boundary_pixels = []
    
    # Scale to typical Mandelbrot view
    x_min, x_max = -2.5, 1.0
    y_min, y_max = -1.5, 1.5
    
    # Compute iteration counts for all pixels
    iterations_grid = []
    for py in range(height):
        row = []
        for px in range(width):
            x = x_min + (px / width) * (x_max - x_min)
            y = y_min + (py / height) * (y_max - y_min)
            c = complex(x, y)
            iterations = mandelbrot(c, max_iter)
            row.append(iterations)
        iterations_grid.append(row)
    
    # Find boundary pixels where iteration count changes significantly
    # This captures the actual fractal boundary
    for py in range(1, height - 1):
        for px in range(1, width - 1):
            current = iterations_grid[py][px]
            
            # Check neighbors for significant iteration difference
            neighbors = [
                iterations_grid[py-1][px],
                iterations_grid[py+1][px],
                iterations_grid[py][px-1],
                iterations_grid[py][px+1],
            ]
            
            # If current iteration differs significantly from neighbors, it's a boundary
            max_diff = max(abs(current - n) for n in neighbors)
            if max_diff > 10 and current < max_iter:
                boundary_pixels.append((px, py))
    
    print(f"Found {len(boundary_pixels)} boundary pixels")
    return boundary_pixels

def hilbert_curve_order(points: list, order: int = 10) -> list:
    """
    Sort points in Hilbert curve traversal order.
    
    Simplified approximation: sort by bit-interleaved coordinates.
    """
    def interleave_bits(x: int, y: int) -> int:
        """Interleave bits of x and y coordinates."""
        result = 0
        max_coord = max(x, y)
        bit_pos = 0
        while max_coord > 0:
            result |= ((x >> bit_pos) & 1) << (2 * bit_pos)
            result |= ((y >> bit_pos) & 1) << (2 * bit_pos + 1)
            x >>= 1
            y >>= 1
            bit_pos += 1
            max_coord >>= 1
        return result
    
    print("Sorting boundary pixels in Hilbert curve order...")
    sorted_points = sorted(points, key=lambda p: interleave_bits(p[0], p[1]))
    return sorted_points

def points_to_audio(points: list, sample_rate: int = 48000) -> bytes:
    """Convert boundary points to PCM audio samples."""
    print(f"Converting {len(points)} points to audio...")
    
    # Map coordinates to audio range [-1.0, 1.0]
    max_coord = 4096
    samples = []
    
    for px, py in points:
        # Normalize to [-1, 1]
        x_norm = (px / max_coord) * 2 - 1
        y_norm = (py / max_coord) * 2 - 1
        
        # Combine x and y into single sample (stereo interleaved)
        samples.append(x_norm)
        samples.append(y_norm)
    
    # Convert to 16-bit PCM
    pcm_data = bytearray()
    for sample in samples:
        # Clamp to [-1, 1]
        sample = max(-1.0, min(1.0, sample))
        # Convert to 16-bit signed integer
        value = int(sample * 32767)
        pcm_data.extend(struct.pack('<h', value))
    
    return bytes(pcm_data)

def save_wav(pcm_data: bytes, output_path: Path, sample_rate: int = 48000, channels: int = 2):
    """Save PCM data as WAV file."""
    print(f"Saving WAV file to {output_path}...")
    
    with wave.open(str(output_path), 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    
    duration = len(pcm_data) / (sample_rate * channels * 2)  # 2 bytes per sample
    print(f"Duration: {duration:.2f} seconds")
    print(f"Size: {len(pcm_data) / 1024 / 1024:.2f} MB")

def main():
    output_path = REPO_ROOT / "media" / "test_audio" / "mandelbrot_boundary.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate Mandelbrot boundary with lower resolution for more boundary pixels
    boundary_pixels = generate_mandelbrot_boundary(width=1024, height=1024, max_iter=256)
    
    if len(boundary_pixels) < 1000:
        print("Warning: Too few boundary pixels, using full iteration grid instead")
        # Fallback: use all pixels with iteration count between 50 and 200
        boundary_pixels = []
        x_min, x_max = -2.5, 1.0
        y_min, y_max = -1.5, 1.5
        width, height = 1024, 1024
        for py in range(height):
            for px in range(width):
                x = x_min + (px / width) * (x_max - x_min)
                y = y_min + (py / height) * (y_max - y_min)
                c = complex(x, y)
                iterations = mandelbrot(c, 256)
                if 50 < iterations < 200:
                    boundary_pixels.append((px, py))
        print(f"Using {len(boundary_pixels)} pixels from iteration range 50-200")
    
    # Sort in Hilbert curve order
    sorted_pixels = hilbert_curve_order(boundary_pixels, order=10)
    
    # Convert to audio
    pcm_data = points_to_audio(sorted_pixels, sample_rate=48000)
    
    # Save as WAV
    save_wav(pcm_data, output_path, sample_rate=48000, channels=2)
    
    print(f"\nMandelbrot boundary audio generated successfully!")
    print(f"Output: {output_path}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
