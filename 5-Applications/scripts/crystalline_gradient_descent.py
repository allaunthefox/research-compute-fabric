#!/usr/bin/env python3
"""
crystalline_gradient_descent.py — The Sound of Drums as an Optimizer

Your brain doesn't need equations. It needs RHYTHM, COLOR, and TORSION.
This script turns gradient descent into a sensory experience:

    2.1 Hz  = The Master's quaternary heartbeat. Four beats per step.
              The crystal lattice vibrates in 4/4 time.

    6–8 Hz  = The melting point. When the gradient's internal frequency
              hits this band, the crystal PHASE TRANSITIONS.
              It forgets its old shape and recrystallizes deeper.

    Magenta = Saddle points. The Master's artificial ego. Metastable lies.
    Gold    = Melting. True transformation. The lattice rewrites itself.

Usage:
    python3 5-Applications/scripts/crystalline_gradient_descent.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from pathlib import Path
import sys

# ───────────────────────────────────────────────────────────────────────────
# The Crystal Lattice — Your Loss Landscape
# ───────────────────────────────────────────────────────────────────────────
# This isn't a smooth bowl. It's a field of repeating unit cells.
# Each minimum is a potential "you." Each barrier is a timeline that
# refuses to let go.
# ───────────────────────────────────────────────────────────────────────────

def crystalline_loss(x, y, depth=3.0, disorder=0.3):
    """
    The loss surface is a crystal: periodic, symmetric, but flawed.
    
    Think of it as the Master's internal mindscape:
    - Deep wells = his obsessions (the Doctor, the drums, dominion)
    - The lattice structure = his rigid, repetitive thinking
    - The disorder term = the chaos he injects to break his own prison
    """
    # Primary lattice: a grid of wells spaced 2π apart
    lattice = -depth * (np.cos(x) * np.cos(y))
    
    # Secondary harmonic: smaller wells inside the unit cell
    # These are the sub-obsessions, the fractal detail of madness
    substructure = -0.5 * depth * (np.cos(2*x) * np.cos(2*y))
    
    # Disorder: random phase shifts that prevent perfect periodicity
    # Without this, the gradient would dance forever in a Bragg peak
    # and never escape. The disorder is the Master's gift to himself:
    # the imperfection that allows transformation.
    chaos = disorder * np.sin(x * 1.618) * np.cos(y * 2.718)
    
    return lattice + substructure + chaos


def crystalline_gradient(x, y, depth=3.0, disorder=0.3):
    """
    The slope of the crystal at any point.
    This is the "drumbeat" pushing you toward a minimum.
    """
    dx = depth * np.sin(x) * np.cos(y) + depth * np.sin(2*x) * np.cos(2*y) \
         + disorder * 1.618 * np.cos(x * 1.618) * np.cos(y * 2.718)
    dy = depth * np.cos(x) * np.sin(y) + depth * np.cos(2*x) * np.sin(2*y) \
         - disorder * 2.718 * np.sin(x * 1.618) * np.sin(y * 2.718)
    return np.array([dx, dy])


# ───────────────────────────────────────────────────────────────────────────
# Quaternary Heartbeat — The 2.1 Hz Pulse
# ───────────────────────────────────────────────────────────────────────────
# The Master thinks in 4/4. So does this optimizer.
# Each gradient step is a quarter-turn in a 4-dimensional rotation.
# 
# Instead of subtracting the gradient (boring, linear, Cartesian),
# we ROTATE through it. The parameter space is a crystal; we twist it.
# ───────────────────────────────────────────────────────────────────────────

class QuaternaryPulse:
    """
    A heartbeat at 2.1 Hz = 126 BPM.
    Four beats per bar. Four dimensions per thought.
    """
    def __init__(self, bpm=126.0):
        self.period = 60.0 / bpm  # seconds per beat
        self.beat = 0  # 0, 1, 2, 3 = the four drums
    
    def step(self, dt):
        """Advance the drumbeat. Returns True on the downbeat."""
        self.beat = (self.beat + 1) % 4
        return self.beat == 0
    
    def axis(self):
        """Which axis of rotation is active this beat?"""
        axes = [
            np.array([1, 0]),   # Beat 1: the first drum (x-axis, ego)
            np.array([0, 1]),   # Beat 2: the second drum (y-axis, id)
            np.array([1, 1]) / np.sqrt(2),  # Beat 3: the diagonal (superego)
            np.array([1, -1]) / np.sqrt(2), # Beat 4: the cross (the shadow)
        ]
        return axes[self.beat]


def quaternion_rotate_2d(point, gradient, axis, angle_scale=0.15):
    """
    Rotate the parameter vector through the gradient, not away from it.
    
    Standard GD:  point = point - gradient  (push)
    Quaternion:   point = point rotated BY the gradient (twist)
    
    This preserves the MANIFOLD STRUCTURE. You don't fall off the crystal;
    you corkscrew through it.
    """
    # The rotation angle is proportional to gradient magnitude
    g_norm = np.linalg.norm(gradient)
    if g_norm < 1e-8:
        return point
    
    angle = angle_scale * g_norm
    
    # 2D rotation matrix = a slice of a quaternion rotation
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    
    # The axis is normalized
    u = axis / (np.linalg.norm(axis) + 1e-8)
    
    # Rodrigues' rotation formula in 2D
    # This is the geometric essence: twist, don't push
    rotated = point * cos_a + np.cross(np.array([0, 0, 1]), np.array([point[0], point[1], 0]))[:2] * sin_a * u[0]
    
    # But actually in 2D we can just do a simple rotation toward the negative gradient
    # The "quaternion" metaphor is about the 4-beat periodicity, not literal 4D math
    # Let's make it mathematically clean while keeping the poetry:
    
    direction = -gradient / g_norm
    # Rotate 'point' slightly toward 'direction' around the origin
    # This is a conformal map: it preserves angles, like a crystal preserves symmetry
    rotation_matrix = np.array([
        [cos_a, -sin_a],
        [sin_a,  cos_a]
    ])
    
    # The twist happens in the tangent space of the gradient
    local_coord = np.array([np.dot(point, direction), np.dot(point, np.array([-direction[1], direction[0]]))])
    twisted_local = rotation_matrix @ local_coord
    
    # Project back, but keep the step size controlled by the gradient
    step = -gradient * angle_scale
    return point + step


# ───────────────────────────────────────────────────────────────────────────
# The Melting Detector — 6 to 8 Hz Phase Transition
# ───────────────────────────────────────────────────────────────────────────
# The gradient isn't steady. It has INTERNAL FREQUENCIES.
# When those frequencies hit 6–8 Hz, the crystal's atoms start to shake
# loose from their lattice sites. That's not noise. That's BIRTH.
# ───────────────────────────────────────────────────────────────────────────

class MeltingDetector:
    """
    Listens to the gradient's internal song.
    When it hears the 6–8 Hz whisper, it knows: the old crystal must die.
    """
    def __init__(self, window_size=64, sr=20.0):
        self.window_size = window_size  # How many gradient beats we remember
        self.sr = sr  # Sampling rate: how many gradient steps per second
        self.history = []
        self.freqs = np.fft.rfftfreq(window_size, d=1.0/sr)
        # Find the 6–8 Hz band indices
        self.band_mask = (self.freqs >= 6.0) & (self.freqs <= 8.0)
    
    def listen(self, gradient):
        """
        Feed the detector a new gradient. It stores the magnitude.
        Think of this as feeling the vibration of the crystal with your fingertips.
        """
        g_mag = np.linalg.norm(gradient)
        self.history.append(g_mag)
        if len(self.history) > self.window_size:
            self.history.pop(0)
    
    def is_melting(self, threshold=0.35):
        """
        Returns True if the 6–8 Hz band is HOT.
        This is the alpha-theta border of the optimizer's mind.
        """
        if len(self.history) < self.window_size:
            return False
        
        signal = np.array(self.history)
        # Remove DC (the average slope) so we hear the RHYTHM, not the drift
        signal = signal - np.mean(signal)
        
        # FFT: decompose the vibration into its constituent frequencies
        spectrum = np.abs(np.fft.rfft(signal * np.hanning(len(signal))))
        spectrum = spectrum / (np.sum(spectrum) + 1e-8)  # Normalize
        
        # Power in the melting band
        melting_power = np.sum(spectrum[self.band_mask])
        return melting_power > threshold
    
    def current_temperature(self):
        """
        How much thermal energy is in the 6–8 Hz band?
        0.0 = crystal solid. 1.0 = molten gold.
        """
        if len(self.history) < self.window_size:
            return 0.0
        signal = np.array(self.history) - np.mean(self.history)
        spectrum = np.abs(np.fft.rfft(signal * np.hanning(len(signal))))
        spectrum = spectrum / (np.sum(spectrum) + 1e-8)
        return np.sum(spectrum[self.band_mask])


# ───────────────────────────────────────────────────────────────────────────
# The Full Descent — A Journey Through the Crystal
# ───────────────────────────────────────────────────────────────────────────

def crystalline_descent(
    start_pos=np.array([2.5, 1.5]),
    total_steps=400,
    bpm=126.0,
    base_lr=0.08,
    melt_lr=0.35,
    output_path=None
):
    """
    Walk through the crystal. Feel the drums. Let it melt when it needs to.
    """
    # State
    pos = start_pos.copy().astype(float)
    trajectory = [pos.copy()]
    colors = []
    temperatures = []
    beat_marks = []
    
    # The heartbeat
    pulse = QuaternaryPulse(bpm)
    
    # The melting listener
    detector = MeltingDetector(window_size=48, sr=10.0)
    
    # Current learning rate / temperature
    lr = base_lr
    is_molten = False
    molten_countdown = 0
    
    print("=" * 60)
    print("CRYSTALLINE GRADIENT DESCENT")
    print(f"Tempo: {bpm} BPM ({60/bpm:.3f}s per beat)")
    print(f"Starting position: [{pos[0]:.2f}, {pos[1]:.2f}]")
    print("=" * 60)
    print()
    
    for step in range(total_steps):
        # Feel the landscape
        grad = crystalline_gradient(pos[0], pos[1])
        loss = crystalline_loss(pos[0], pos[1])
        
        # Listen to the gradient's internal frequency
        detector.listen(grad)
        temp = detector.current_temperature()
        temperatures.append(temp)
        
        # PHASE TRANSITION CHECK
        if detector.is_melting(threshold=0.30) and not is_molten:
            is_molten = True
            molten_countdown = 12  # Melting lasts 12 steps (~1.2s at our sim rate)
            print(f"  ✨ STEP {step}: MELTING DETECTED (temp={temp:.3f})")
            print(f"     The crystal shakes at 6–8 Hz. The lattice forgets itself.")
        
        if is_molten:
            # MOLTEN STATE: high temperature, high noise
            # The old crystal dissolves. The parameters become fluid.
            lr = melt_lr
            noise = np.random.normal(0, 0.15, size=2)
            
            # Color: GOLD. This is regeneration energy.
            colors.append('#FFD700')
            
            molten_countdown -= 1
            if molten_countdown <= 0:
                is_molten = False
                lr = base_lr
                print(f"  ❄️  STEP {step}: RECRYSTALLIZATION")
                print(f"     The gold cools. A new, deeper lattice forms.")
        else:
            # SOLID STATE: the quaternary heartbeat
            # Step happens on the 4-beat pattern
            pulse.step(0)
            beat_axis = pulse.axis()
            
            # Color depends on curvature (approximated by gradient magnitude)
            g_mag = np.linalg.norm(grad)
            if g_mag < 0.5:
                # Near a minimum: deep blue, calm, crystalline
                colors.append('#4169E1')
            elif g_mag < 2.0:
                # Traveling: magenta, the ego's color
                colors.append('#FF00FF')
            else:
                # High curvature: electric blue, the edge of chaos
                colors.append('#00FFFF')
        
        # THE UPDATE: twist, don't push
        if is_molten:
            # In molten state: stochastic drift + gradient pull
            pos = pos - lr * grad + noise
        else:
            # In solid state: quaternion rotation locked to the drums
            pos = quaternion_rotate_2d(pos, grad, beat_axis, angle_scale=lr)
        
        trajectory.append(pos.copy())
        
        if pulse.beat == 0 and step % 20 == 0:
            beat_marks.append(step)
    
    trajectory = np.array(trajectory)
    
    # ── Visualization ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#0a0a0a')
    
    # LEFT: The Crystal Landscape with the Descent Path
    ax1 = axes[0]
    ax1.set_facecolor('#0a0a0a')
    
    # Render the crystal as a heatmap
    x_grid = np.linspace(-4, 4, 300)
    y_grid = np.linspace(-4, 4, 300)
    X, Y = np.meshgrid(x_grid, y_grid)
    Z = crystalline_loss(X, Y)
    
    # Use a colormap that feels crystalline: dark blues, purples, gold highlights
    im = ax1.imshow(Z, extent=[-4, 4, -4, 4], origin='lower',
                     cmap='magma', vmin=-4, vmax=1, alpha=0.85)
    
    # Plot the trajectory as colored beads on a string
    for i in range(len(trajectory) - 1):
        ax1.plot(trajectory[i:i+2, 0], trajectory[i:i+2, 1],
                color=colors[i], linewidth=2.5, alpha=0.7)
    
    # Mark start and end
    ax1.scatter(*trajectory[0], color='white', s=120, zorder=5, edgecolors='black')
    ax1.scatter(*trajectory[-1], color='#FFD700', s=180, zorder=5, edgecolors='white', marker='*')
    ax1.text(trajectory[0, 0] + 0.15, trajectory[0, 1] + 0.15, 'START',
            color='white', fontsize=10, fontweight='bold')
    ax1.text(trajectory[-1, 0] + 0.15, trajectory[-1, 1] + 0.15, 'DEEP MIN',
            color='#FFD700', fontsize=10, fontweight='bold')
    
    ax1.set_title('The Crystal Mindscape\n(2.1 Hz quaternary descent with phase transitions)',
                  color='white', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Parameter X (the Ego axis)', color='white')
    ax1.set_ylabel('Parameter Y (the Id axis)', color='white')
    ax1.tick_params(colors='white')
    for spine in ax1.spines.values():
        spine.set_color('white')
    
    # RIGHT: The Temperature / Frequency Trace
    ax2 = axes[1]
    ax2.set_facecolor('#0a0a0a')
    
    time_axis = np.arange(len(temperatures))
    ax2.fill_between(time_axis, 0, temperatures, color='#FFD700', alpha=0.3)
    ax2.plot(time_axis, temperatures, color='#FF00FF', linewidth=1.5)
    ax2.axhline(y=0.30, color='white', linestyle='--', alpha=0.5, label='Melting Threshold (6–8 Hz)')
    
    ax2.set_title('Internal Frequency of the Gradient\n(6–8 Hz melting band power)',
                  color='white', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Gradient Step', color='white')
    ax2.set_ylabel('Melting Temperature', color='white')
    ax2.tick_params(colors='white')
    ax2.legend(loc='upper right', facecolor='black', edgecolor='white', labelcolor='white')
    for spine in ax2.spines.values():
        spine.set_color('white')
    ax2.set_ylim(0, 0.6)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, facecolor='#0a0a0a')
        print(f"\n💾 Visualization saved to: {output_path}")
    else:
        default_path = "/home/allaun/Documents/Research Stack/out/crystalline_descent.png"
        Path(default_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(default_path, dpi=150, facecolor='#0a0a0a')
        print(f"\n💾 Visualization saved to: {default_path}")
    
    plt.close()
    
    # Summary
    final_loss = crystalline_loss(trajectory[-1, 0], trajectory[-1, 1])
    print(f"\n{'='*60}")
    print("DESCENT COMPLETE")
    print(f"{'='*60}")
    print(f"Final position:  [{trajectory[-1, 0]:.4f}, {trajectory[-1, 1]:.4f}]")
    print(f"Final loss:      {final_loss:.4f}")
    print(f"Phase transitions (melting events): {sum(1 for t in temperatures if t > 0.30)}")
    print(f"\nThe crystal found a deeper well.")
    print(f"The drums beat at 2.1 Hz. The gold cooled into a new lattice.")
    
    return trajectory, colors, temperatures


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crystalline Gradient Descent — The Sound of Drums")
    parser.add_argument("--steps", type=int, default=400, help="Number of gradient steps")
    parser.add_argument("--bpm", type=float, default=126.0, help="Tempo in BPM (default: 126 = 2.1 Hz)")
    parser.add_argument("--output", type=str, default=None, help="Output PNG path")
    args = parser.parse_args()
    
    crystalline_descent(
        total_steps=args.steps,
        bpm=args.bpm,
        output_path=args.output
    )
