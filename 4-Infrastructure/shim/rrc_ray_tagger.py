#!/usr/bin/env python3
"""
RRC Ray Layer Tagger — Generic shape classification for math payloads.

Classifies equations, receipts, and compute kernels into RRC shapes,
then assigns a ray-layer transport for each shape. The ray layer
(virtio-net, WGSL/SPIR-V, Lean, ARM64) becomes the interconnect
that lets tagged pieces snap together.

Ray layer abstraction:
  ╔════════════════════════════════════════════════════╗
  ║              RAY LAYER (transport bus)            ║
  ║  ┌──────────┐  ┌──────────┐  ┌──────────┐       ║
  ║  │  WGSL    │  │  SPIR-V  │  │ virtio   │  ...  ║
  ║  │ (GPU)    │  │ (driver) │  │ (NIC)    │       ║
  ║  └────┬─────┘  └────┬─────┘  └────┬─────┘       ║
  ║       └─────────────┼──────────────┘             ║
  ║                     ▼                            ║
  ║            Swappable Compute Slots               ║
  ╚════════════════════════════════════════════════════╝

Each shape declares its ray-layer transport requirements.
The tagger matches shapes to available transports.
"""

import hashlib
import json
import time
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any

# ── RRC Shape Taxonomy ──────────────────────────────────────

class RRCShape(Enum):
    LOGOGRAM = "LogogramProjection"         # symbolic rewrite
    GEOMETRY = "ProjectableGeometryTopology" # spatial/manifold
    SIGNAL = "SignalShapedRouteCompiler"    # signal processing
    CAD = "CadForceProbeReceipt"            # physical/cad
    COGNITIVE = "CognitiveLoadField"        # semantic/linguistic
    COMPUTE = "ComputeKernelReceipt"        # GPU/compute kernel
    LEAN = "LeanTheoremReceipt"             # formal proof
    NIC = "NetworkRayReceipt"               # virtio-net hardware
    BURGERS = "BurgersRGSolver"             # fluid dynamics
    SINEGORDON = "SineGordonPrediction"     # QFT prediction
    ERDOS = "ErdosBoundConjecture"          # combinatorics

class RayLayer(Enum):
    WGSL = "wgsl"           # GPU compute shader
    SPIRV = "spirv"         # GPU driver (copy-if optimized)
    VIRTIO = "virtio"       # NIC hardware pipeline
    LEAN = "lean"           # formal verification
    PYTHON = "python"       # CPU orchestration
    PYTORCH = "pytorch"     # GPU tensor compute
    ARM64 = "arm64"         # CPU scalar (CSEL)

class RRCStatus(Enum):
    ACCEPT = "ACCEPT"       # has receipt + can replay
    HOLD = "HOLD"           # missing evidence
    QUARANTINE = "QUARANTINE"  # unstable/destructive

# ── Shape Registry ──────────────────────────────────────────

SHAPE_REGISTRY = {
    RRCShape.BURGERS: {
        'full_solver': {
            'layer': RayLayer.PYTORCH,
            'cost_us': 500,
            'needs_fft': True,
            'needs_gpu': True,
            'swappable_with': ['scar_filter', 'hopf_cole'],
        },
        'scar_filter': {
            'layer': [RayLayer.WGSL, RayLayer.SPIRV],
            'cost_us': 21,
            'needs_fft': False,
            'needs_gpu': True,
            'swappable_with': ['full_solver', 'hopf_cole'],
        },
        'phase_update': {
            'layer': RayLayer.PYTORCH,
            'cost_us': 34,
            'needs_fft': False,
            'needs_gpu': True,
            'swappable_with': ['scar_filter', 'analytic'],
        },
        'analytic': {
            'layer': RayLayer.LEAN,
            'cost_us': 0,
            'needs_fft': False,
            'needs_gpu': False,
            'swappable_with': [],
        },
        'hopf_cole': {
            'layer': [RayLayer.PYTHON, RayLayer.WGSL],
            'cost_us': 100,
            'needs_fft': True,
            'needs_gpu': False,
            'swappable_with': ['full_solver', 'scar_filter'],
        },
    },
    RRCShape.SINEGORDON: {
        'lattice_mc': {
            'layer': [RayLayer.PYTORCH, RayLayer.VIRTIO],
            'cost_us': 100000,
            'needs_fft': False,
            'needs_gpu': True,
            'swappable_with': [],
        },
    },
    RRCShape.NIC: {
        'virtio_pipeline': {
            'layer': RayLayer.VIRTIO,
            'cost_us': 67,
            'needs_fft': False,
            'needs_gpu': False,
            'swappable_with': ['copy_if_opt', 'copy_if_nic'],
        },
        'copy_if_opt': {
            'layer': RayLayer.SPIRV,
            'cost_us': 67,
            'needs_fft': False,
            'needs_gpu': False,
            'swappable_with': ['virtio_pipeline', 'copy_if_nic'],
        },
        'copy_if_nic': {
            'layer': RayLayer.VIRTIO,
            'cost_us': 67,
            'needs_fft': False,
            'needs_gpu': False,
            'swappable_with': ['virtio_pipeline', 'copy_if_opt'],
        },
    },
    RRCShape.LEAN: {
        'nine_pow_alpha': {
            'layer': RayLayer.LEAN,
            'cost_us': 0,
            'needs_fft': False,
            'needs_gpu': False,
            'swappable_with': [],
        },
    },
    RRCShape.ERDOS: {
        'rg_bound': {
            'layer': RayLayer.LEAN,
            'cost_us': 0,
            'needs_fft': False,
            'needs_gpu': False,
            'swappable_with': [],
        },
    },
}

# ── Tagged Payload ──────────────────────────────────────────

@dataclass
class TaggedPayload:
    """An equation/compute kernel tagged with RRC shape + ray transport."""

    equation_id: str
    equation_text: str
    shape: RRCShape
    status: RRCStatus
    ray_layers: list[RayLayer]
    witnesses: list[str] = field(default_factory=list)
    missing_axes: list[str] = field(default_factory=list)
    swappable_with: list[str] = field(default_factory=list)
    cost_us: int = 0
    receipt_hash: str = ""

    def tag(self) -> dict[str, Any]:
        return {
            'equation_id': self.equation_id,
            'shape': self.shape.value,
            'status': self.status.value,
            'ray_layers': [l.value for l in self.ray_layers],
            'witnesses': self.witnesses,
            'missing_axes': self.missing_axes,
            'swappable_with': self.swappable_with,
            'cost_us': self.cost_us,
            'receipt_hash': self.receipt_hash,
        }

# ── Helper Function ─────────────────────────────────────────

def normalize_str(s: str) -> str:
    """Helper to normalize strings for robust keyword/variant matching."""
    return s.lower().replace('_', '').replace('-', '').replace(' ', '')

# ── The Tagger ──────────────────────────────────────────────

class RRCRayTagger:
    """Generically tag any equation/payload with RRC shape + ray transport.

    The tagger:
      1. Accepts any equation text or receipt JSON
      2. Classifies it into one of the RRC shapes
      3. Assigns ray-layer transport(s)
      4. Identifies swappable alternatives
      5. Emits a tag with status and missing axes
    """

    def tag_equation(self, text: str, source: str = "") -> TaggedPayload:
        """Tag an equation by its text content and source name."""
        text_lower = text.lower()
        source_lower = source.lower()
        eq_id = hashlib.sha256(text.encode()).hexdigest()[:16]

        # 1. Classify RRC Shape based on source and text keywords
        if ('burgers' in source_lower or 'burgers' in text_lower or
            '∂u/∂t' in text_lower or
            'hopf' in source_lower or 'hopf' in text_lower or
            'phase' in source_lower or
            'analytic' in source_lower):
            shape = RRCShape.BURGERS
        elif 'sine-gordon' in source_lower or 'sine-gordon' in text_lower or 'β̂²' in text_lower or 'superconformal' in text_lower:
            shape = RRCShape.SINEGORDON
        elif ('virtio' in source_lower or 'virtio' in text_lower or
              'rss' in text_lower or 'tso' in text_lower or
              'nic' in source_lower or 'nic' in text_lower or
              'spir-v opt' in source_lower or 'copy-if nic' in source_lower):
              shape = RRCShape.NIC
        elif '9^α' in text or 'log₃4' in text or 'c/7' in text:
            shape = RRCShape.LEAN
        elif 'erdős' in source_lower or 'erdős' in text_lower or 'unit distance' in text_lower or 'u(n) ≥' in text:
            shape = RRCShape.ERDOS
        elif 'spir-v' in text_lower or 'opselect' in text_lower or 'copy-if' in text_lower:
            shape = RRCShape.NIC
        elif '.wgsl' in text or 'compute shader' in text_lower:
            shape = RRCShape.COMPUTE
        else:
            shape = RRCShape.LOGOGRAM

        # 2. Match best variant in registry
        variants = SHAPE_REGISTRY.get(shape, {})
        best_variant_name = None
        best_variant = None

        if variants:
            text_clean = normalize_str(text)
            source_clean = normalize_str(source)

            # First pass: try matching by source name (most reliable)
            for vname, vinfo in variants.items():
                vname_clean = normalize_str(vname)
                if vname_clean in source_clean:
                    best_variant = vinfo
                    best_variant_name = vname
                    break
                elif vname == 'full_solver' and 'burgers' in source_clean:
                    best_variant = vinfo
                    best_variant_name = vname
                    break
                elif vname == 'copy_if_opt' and 'spirvopt' in source_clean:
                    best_variant = vinfo
                    best_variant_name = vname
                    break
                elif vname == 'copy_if_nic' and 'copyifnic' in source_clean:
                    best_variant = vinfo
                    best_variant_name = vname
                    break

            # Second pass: if no source match, check text
            if best_variant is None:
                for vname, vinfo in variants.items():
                    vname_clean = normalize_str(vname)
                    if vname_clean in text_clean:
                        best_variant = vinfo
                        best_variant_name = vname
                        break
                    elif vname == 'copy_if_opt' and 'copyif' in text_clean:
                        best_variant = vinfo
                        best_variant_name = vname
                        break
                    elif vname == 'copy_if_nic' and 'copyif' in text_clean:
                        best_variant = vinfo
                        best_variant_name = vname
                        break

            # Default fallback to first variant
            if best_variant is None:
                best_variant_name = list(variants.keys())[0]
                best_variant = list(variants.values())[0]

            layers = best_variant['layer']
            if not isinstance(layers, list):
                layers = [layers]

            swappable = best_variant.get('swappable_with', [])
            cost = best_variant.get('cost_us', 0)
        else:
            layers = [RayLayer.PYTHON]
            swappable = []
            cost = 0

        # 3. Assess witnesses and identify missing axes
        witnesses = []
        missing = []

        if cost == 0 and shape != RRCShape.LEAN:
            missing.append('cost_estimate')
        if not swappable:
            missing.append('swappable_alternative')
        if layers == [RayLayer.PYTHON]:
            missing.append('hardware_acceleration')

        has_scale = any(w in text_lower for w in ['μm', 'nm', 'km', 'hz', 'gb', 'μs'])
        has_control = any(w in text_lower for w in ['threshold', 'limit', '>', '<', 'bound'])

        if has_scale:
            witnesses.append('scale_witness')
        if has_control:
            witnesses.append('negative_control_witness')

        # 4. Determine status
        if best_variant_name == 'phase_update':
            # Phase update quarantined because adversarial review disproved the model assumption
            status = RRCStatus.QUARANTINE
            missing.append('adversarial_review_falsification')
        elif not missing:
            status = RRCStatus.ACCEPT
        elif len(missing) <= 2:
            status = RRCStatus.HOLD
        else:
            status = RRCStatus.QUARANTINE

        receipt_data = f"{shape.value}:{eq_id}:{time.time()}"
        receipt_hash = hashlib.sha256(receipt_data.encode()).hexdigest()[:16]

        return TaggedPayload(
            equation_id=f"rrc_{eq_id}",
            equation_text=text[:80],
            shape=shape,
            status=status,
            ray_layers=layers,
            witnesses=witnesses,
            missing_axes=missing,
            swappable_with=swappable,
            cost_us=cost,
            receipt_hash=receipt_hash,
        )

    def tag_receipt(self, receipt: dict) -> TaggedPayload:
        """Tag a receipt JSON (has its own witnesses)."""
        text = json.dumps(receipt)
        eq = receipt.get('schema', 'unknown')
        return self.tag_equation(eq + " " + text)

# ── Swappable Slot Map ──────────────────────────────────────

class SwappableSlotMap:
    """Maps RRC shapes to available ray-layer transports."""

    def __init__(self):
        self.slots: dict[str, list[TaggedPayload]] = {}

    def add(self, payload: TaggedPayload):
        slot_name = payload.shape.value
        if slot_name not in self.slots:
            self.slots[slot_name] = []
        self.slots[slot_name].append(payload)

    def show_swappable(self):
        """Print the swappable slot map."""
        print(f"\n{'='*65}")
        print(f"SWAPPABLE COMPUTE SLOTS")
        print(f"{'='*65}")

        for slot, payloads in sorted(self.slots.items()):
            variants = [p for p in payloads]
            if not variants:
                continue

            print(f"\n  ┌─ {slot}")

            for impl in variants:
                swap_str = ", ".join(impl.swappable_with) if impl.swappable_with else "—"
                layers_str = ", ".join(l.value for l in impl.ray_layers)
                print(f"  ├─ {impl.equation_id[:20]:>20s}")
                print(f"  │  layer: {layers_str}")
                print(f"  │  cost:  {impl.cost_us:>8d} μs")
                print(f"  │  swap:  {swap_str}")
                print(f"  │  status: {impl.status.value}")

            print(f"  └─ {'─'*40}")

# ── Main ────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("RRC RAY LAYER TAGGER — Generic Math Shape Classification")
    print("=" * 65)

    tagger = RRCRayTagger()
    slot_map = SwappableSlotMap()

    # Tag all the equations from our RG work
    equations = [
        ("Burgers", "∂u/∂t + u·∇u = ν∇²u — 2D pseudospectral solver with FAMM scar filter at 2048²"),
        ("Scar filter", "burgers_scar_filter.wgsl — spectral scar pressure P(k) = (k/k_cut)⁴/(1 + (k/k_cut)⁴)"),
        ("Phase update", "φ(k, t+1) = φ(k, t) + ν·k²·Δt — RG fixed point, 34μs/step"),
        ("Analytic", "E(k) = A/k^α with A = c/7, α = log₃4 — no FFT needed"),
        ("Hopf-Cole", "u = -2ν·∂(ln ψ)/∂x — exact 1D Burgers solution via heat equation"),
        ("Sine-Gordon", "β̂² = log₃4 predicted for N=2 superconformal point, 14% soliton mass shift"),
        ("Erdős", "u(n) ≤ O(n^{log₃4}) — Szemerédi–Trotter bound improvement from 4/3 to 1.262"),
        ("Lean proof", "9^α = 16 proven in Lean — RGUnitDistance.lean, A = c/7"),
        ("SPIR-V opt", "OpBranchConditional + OpPhi → OpSelect — copy-if, 3 blocks → 1"),
        ("virtio pipeline", "RSS Toeplitz hash + TSO segmentation + RSC coalescing at 10GbE line rate"),
        ("Copy-if NIC", "virtio ring depth → scar pressure — queue backpressure damping"),
    ]

    for name, text in equations:
        tag = tagger.tag_equation(text, name)
        slot_map.add(tag)

        print(f"\n  [{tag.status.value:>10s}] {name:>15s} → {tag.shape.value:<30s}")
        print(f"         layers: {', '.join(l.value for l in tag.ray_layers)}")
        if tag.witnesses:
            print(f"         witnesses: {', '.join(tag.witnesses)}")
        if tag.missing_axes:
            print(f"         MISSING: {', '.join(tag.missing_axes)}")
        if tag.swappable_with:
            print(f"         swappable: {', '.join(tag.swappable_with)}")
        print(f"         cost: {tag.cost_us:>8d} μs — receipt: {tag.receipt_hash}")

    # Show the swappable slot map
    slot_map.show_swappable()

    # Determine the repository root dynamically based on script file path
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    receipt_dir = os.path.join(repo_root, "desi_model_projection_receipt_2026-05-13")
    os.makedirs(receipt_dir, exist_ok=True)
    receipt_path = os.path.join(receipt_dir, "rrc_ray_tag_receipt.json")

    # Calculate accept status count
    accepted = 0
    for name, text in equations:
        t = tagger.tag_equation(text, name)
        if t.status == RRCStatus.ACCEPT:
            accepted += 1

    # Save receipt
    receipt = {
        'schema': 'rrc_ray_tagger_v1',
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'n_equations': len(equations),
        'n_accepted': accepted,
    }

    with open(receipt_path, 'w') as f:
        json.dump(receipt, f, indent=2)

    print(f"\n  Receipt saved: {receipt_path}")
    print(f"  Shown: {accepted}/{len(equations)} with ACCEPT status")


if __name__ == "__main__":
    main()
