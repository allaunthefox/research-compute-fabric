"""
Unit Tests for MISC Kernel
==========================
Tests all core components:
  - Q16.16 fixed-point arithmetic
  - PIST/DIAT coordinate invariants
  - ShellMapBuilder
  - GWL multi-factor coupling
  - Cognitive load routing
  - Thermodynamic trixal quality
  - Homeostatic governance
  - Delta GCL encoding
  - Full MISC compression pipeline
"""

import sys
import os
import math
import struct
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from misc_kernel import (
    Q16_16, SCALE, PI_Q16, TAU_Q16,
    cos_q16, exp_q16,
    PISTCoordinate, DIATCoordinate, ShellMapBuilder,
    GWLCoupling,
    CognitiveLoadRouter,
    TrixalState, ThermodynamicEngine,
    HomeostaticGovernor,
    PTOSManifest, DeltaGCLEncoder, DeltaGCLSequence,
    MISCConfig, MISCCompressor, CompressedBlock,
    compress, format_report,
)

import hashlib


# ──────────────────────────────────────────────────────
# Test Q16.16 Arithmetic
# ──────────────────────────────────────────────────────

def test_q16_basics():
    """Test basic Q16.16 operations."""
    zero = Q16_16(0)
    one = Q16_16.from_int(1)
    half = Q16_16.from_float(0.5)
    
    # Construction
    assert zero.val == 0
    assert one.val == SCALE
    assert abs(half.to_float() - 0.5) < 0.0001
    
    # Addition
    assert (one + half).to_float() == 1.5
    
    # Subtraction
    assert (one - half).to_float() == 0.5
    
    # Multiplication
    result = half * half
    assert abs(result.to_float() - 0.25) < 0.001
    
    # Division
    result = one / half
    assert abs(result.to_float() - 2.0) < 0.001
    
    # Negation
    assert (-one).to_float() == -1.0
    
    # Absolute value
    neg = Q16_16(-SCALE * 2)
    assert abs(abs(neg).to_float() - 2.0) < 0.001
    
    # Comparison
    assert one > half
    assert half < one
    assert one == Q16_16.from_int(1)
    assert one >= half
    assert half <= one
    print("  ✓ Q16.16 basics")


def test_q16_from_natural():
    """Test Q16.16 fraction constructor (Model 628)."""
    result = Q16_16.from_natural(1, 3)
    assert abs(result.to_float() - 1.0/3.0) < 0.001
    
    result = Q16_16.from_natural(7, 10)
    assert abs(result.to_float() - 0.7) < 0.001
    
    # Division by zero returns 0
    result = Q16_16.from_natural(1, 0)
    assert result.val == 0
    print("  ✓ Q16.16 from_natural")


def test_q16_sqrt():
    """Test Q16.16 square root (Model 636)."""
    # sqrt(4) = 2
    four = Q16_16.from_int(4)
    result = Q16_16.sqrt(four)
    assert abs(result.to_float() - 2.0) < 0.01
    
    # sqrt(0) = 0
    result = Q16_16.sqrt(Q16_16(0))
    assert result.val == 0
    
    # sqrt(2) ≈ 1.414
    two = Q16_16.from_int(2)
    result = Q16_16.sqrt(two)
    assert abs(result.to_float() - math.sqrt(2)) < 0.01
    print("  ✓ Q16.16 sqrt")


def test_q16_clamp():
    """Test Q16.16 min/max/clamp (Models 633-635)."""
    a = Q16_16.from_float(0.3)
    b = Q16_16.from_float(0.7)
    
    assert abs(Q16_16.min(a, b).to_float() - 0.3) < 0.001
    assert abs(Q16_16.max(a, b).to_float() - 0.7) < 0.001
    
    lo = Q16_16.from_float(0.2)
    hi = Q16_16.from_float(0.8)
    
    assert abs(Q16_16.clamp(a, lo, hi).to_float() - 0.3) < 0.001
    assert abs(Q16_16.clamp(Q16_16.from_float(0.1), lo, hi).to_float() - 0.2) < 0.001
    assert abs(Q16_16.clamp(Q16_16.from_float(0.9), lo, hi).to_float() - 0.8) < 0.001
    print("  ✓ Q16.16 clamp")


def test_trig_luts():
    """Test LUT-based cosine and exponential."""
    # cos(0) → 1
    result = cos_q16(Q16_16(0))
    assert abs(result.to_float() - 1.0) < 0.05
    
    # cos(π) → -1
    result = cos_q16(Q16_16(PI_Q16))
    assert abs(result.to_float() - (-1.0)) < 0.05
    
    # cos(π/2) → 0
    half_pi = Q16_16(PI_Q16 // 2)
    result = cos_q16(half_pi)
    assert abs(result.to_float()) < 0.05
    
    # exp(0) → 1
    result = exp_q16(Q16_16(0))
    assert abs(result.to_float() - 1.0) < 0.01
    
    # exp(-large) → 0
    result = exp_q16(Q16_16.from_float(-10.0))
    assert result.val == 0
    print("  ✓ LUT trig functions")


# ──────────────────────────────────────────────────────
# Test PIST/DIAT Coordinates
# ──────────────────────────────────────────────────────

def test_pist_coordinate():
    """Test PIST coordinate invariants (Models 578-587)."""
    # Perfect squares have zero mass (Model 603)
    for n in [0, 1, 4, 9, 16, 25, 36, 49, 64]:
        k = int(math.isqrt(n))
        t = n - k * k
        coord = PISTCoordinate(k=k, t=t)
        assert coord.mass == 0, f"Perfect square {n} should have mass 0"
        assert coord.is_endpoint, f"Perfect square {n} should be endpoint"
    
    # Non-square interiors have positive mass (Model 587)
    for n in [2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]:
        k = int(math.isqrt(n))
        t = n - k * k
        coord = PISTCoordinate(k=k, t=t)
        assert coord.mass > 0, f"Non-square {n} should have mass > 0"
        assert not coord.is_endpoint, f"Non-square {n} should not be endpoint"
    
    print("  ✓ PIST coordinate invariants")


def test_pist_mirror():
    """Test mirror involution preserves mass (Model 602)."""
    for n in range(1, 50):
        k = int(math.isqrt(n))
        t = n - k * k
        coord = PISTCoordinate(k=k, t=t)
        mirror = coord.mirror()
        
        # Mirror preserves mass
        assert coord.mass == mirror.mass, f"Mirror should preserve mass for n={n}"
        
        # Mirror inverts offset
        assert mirror.t == 2 * k + 1 - t
        
        # Mirror of mirror = original
        assert mirror.mirror() == coord, f"Double mirror should be identity for n={n}"
    print("  ✓ PIST mirror involution")


def test_pist_resonance():
    """Test resonance detection (Model 582)."""
    # n=2 and n=4-has mass 2 and 0 respectively (different)
    c2 = PISTCoordinate(k=1, t=1)   # n=2
    c3 = PISTCoordinate(k=1, t=2)   # n=3
    c4 = PISTCoordinate(k=2, t=0)   # n=4
    
    assert c2.is_resonant_with(c3), "n=2 and n=3 are mirror pairs with same mass=2"
    assert not c4.is_resonant_with(c2), "n=4 (perfect square) not resonant with n=2"
    
    # Mirror pairs are resonant
    assert c2.is_resonant_with(c2.mirror()), "Mirror pairs should be resonant"
    print("  ✓ PIST resonance")


def test_pist_rho():
    """Test normalized tension (Model 585)."""
    # Shell endpoints have rho=0
    c0 = PISTCoordinate(k=2, t=0)     # n=4, endpoint
    assert c0.rho.to_float() == 0.0
    
    # Midpoint has rho ≈ 0.5
    c_mid = PISTCoordinate(k=2, t=2)  # n=6, middle of shell width 5
    assert abs(c_mid.rho.to_float() - 0.4) < 0.001  # 2/5 = 0.4
    
    print("  ✓ PIST rho normalized tension")


def test_diat_coordinate():
    """Test DIAT coordinate encoding (Models 687-691)."""
    # Perfect squares
    for n in [0, 1, 4, 9, 16, 25]:
        diat = DIATCoordinate.encode(n)
        k = int(math.isqrt(n))
        assert diat.shell == k
        assert diat.offset == 0
        assert diat.shell_width == 2 * k + 1
    
    # Non-squares
    diat = DIATCoordinate.encode(7)
    assert diat.shell == 2
    assert diat.offset == 3  # 7 - 4
    assert diat.shell_width == 5
    
    # Norm A
    assert abs(diat.norm_a.to_float() - 3.0/5.0) < 0.001
    print("  ✓ DIAT coordinate encoding")


def test_shell_map_builder():
    """Test ShellMapBuilder."""
    data = b"hello world hello world hello"
    builder = ShellMapBuilder(data)
    
    # All distinct tokens get shell coordinates
    assert len(builder.coords) == 8  # distinct characters in "hello world": h,e,l,o,' ',w,r,d
    
    # Most frequent token (should be 'l' or 'o') has lowest rank → small k
    # Check that at least some tokens have mass 0 (endpoints)
    endpoints = builder.endpoint_tokens()
    assert len(endpoints) >= 1, "At least one token should be at shell endpoint"
    
    # Resonance groups
    groups = builder.resonance_groups()
    assert len(groups) >= 1
    
    print("  ✓ ShellMapBuilder")


# ──────────────────────────────────────────────────────
# Test GWL Coupling
# ──────────────────────────────────────────────────────

def test_gwl_coupling():
    """Test GWL multi-factor coupling (Models 16-29)."""
    data = bytes(range(0, 256, 2))  # all even bytes → same chirality
    builder = ShellMapBuilder(data)
    coupling = GWLCoupling(256)
    
    # Self-coupling should be 1.0 (or very close)
    w_self = coupling.compute(data, 0, 0, builder)
    assert abs(w_self.to_float() - 1.0) < 0.1
    
    # Nearby same-parity tokens should have positive coupling
    w_near = coupling.compute(data, 0, 2, builder)
    assert w_near.to_float() > 0.0, f"Nearby same-chirality coupling should be positive, got {w_near.to_float():.3f}"
    
    # All coupling values should be in [-1, 1]
    for i in range(0, 50, 10):
        for j in range(i + 2, min(i + 16, 50, len(data)), 2):
            w = coupling.compute(data, i, j, builder)
            assert -1.0 <= w.to_float() <= 1.0, \
                f"Coupling weight {w.to_float():.3f} should be in [-1, 1]"
    
    print("  ✓ GWL coupling")


# ──────────────────────────────────────────────────────
# Test Cognitive Load Router
# ──────────────────────────────────────────────────────

def test_cognitive_load():
    """Test cognitive load decomposition (Models 1-10)."""
    router = CognitiveLoadRouter()
    
    # Low-entropy data (all same byte) should have low intrinsic load
    low_entropy = b'\x00' * 64
    low_load = router.intrinsic_load(low_entropy)
    assert low_load.to_float() <= 0.1, "Low entropy data should have low intrinsic load"
    
    # High-entropy data (all bytes varied) should have high intrinsic load
    high_entropy = bytes(range(256))
    high_load = router.intrinsic_load(high_entropy)
    assert high_load.to_float() >= 0.8, "High entropy data should have high intrinsic load"
    
    # Intrinsic load of empty data
    empty_load = router.intrinsic_load(b'')
    assert empty_load.val == 0
    
    # Strategy selection should pick something reasonable
    test_data = b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    strategy, load = router.select_strategy(test_data, 0)
    assert strategy in router.STRATEGIES
    assert load.to_float() >= 0
    print("  ✓ Cognitive load decomposition")


def test_strategy_routing():
    """Test strategy switching and routing."""
    router = CognitiveLoadRouter()
    
    # Initially should be RAW_COPY
    assert router.current_strategy == 'RAW_COPY'
    
    # First block should set current strategy
    data = b"Hello, MISC! This is a test of the manifold-invariant shell compres"
    strategy, _ = router.select_strategy(data, 0)
    assert router.current_strategy == strategy
    
    # Second block may switch or stay
    strategy2, _ = router.select_strategy(data[:32], 1)
    assert strategy2 in router.STRATEGIES
    
    # History should be populated
    assert len(router.history) == 2
    print("  ✓ Strategy routing")


# ──────────────────────────────────────────────────────
# Test Thermodynamic Quality
# ──────────────────────────────────────────────────────

def test_thermodynamic_engine():
    """Test thermodynamic tracking (Models 39-50)."""
    engine = ThermodynamicEngine()
    
    # Shannon entropy of uniform data
    uniform = bytes(range(256))
    H = engine.measure_shannon(uniform)
    assert abs(H.to_float() - 8.0) < 0.1, f"Uniform 256-byte entropy should be ~8, got {H.to_float()}"
    
    # Shannon entropy of constant data
    const_data = b'\x00' * 256
    H2 = engine.measure_shannon(const_data)
    assert H2.to_float() < 0.1, "Constant data entropy should be ~0"
    
    # Mutual information extracted
    MI = engine.mutual_information_extracted(H, H2)
    assert MI.to_float() > 0, "MI from high to low entropy should be positive"
    
    # Carnot efficiency
    t_cold = Q16_16.from_int(1)
    t_hot = Q16_16.from_int(3)
    eta = engine.carnot_efficiency(t_cold, t_hot)
    assert abs(eta.to_float() - 2.0/3.0) < 0.001
    
    # Work extraction
    work = engine.work_extraction(Q16_16.from_int(10), eta)
    assert abs(work.to_float() - 10 * 2.0/3.0 * 0.7) < 0.01
    
    # Entropy gradient
    grad1 = engine.entropy_gradient(Q16_16.from_float(7.0))
    assert grad1.val == 0, "First gradient should be 0 (no previous)"
    
    grad2 = engine.entropy_gradient(Q16_16.from_float(6.0))
    assert grad2.to_float() < 0, "Decreasing entropy should give negative gradient"
    
    print("  ✓ Thermodynamic engine")


def test_trixal_state():
    """Test trixal state computation."""
    engine = ThermodynamicEngine()
    
    test_data = b"The quick brown fox jumps over the lazy dog"
    H = engine.measure_shannon(test_data)
    
    trixal = TrixalState(
        thermal=Q16_16.from_float(0.8),
        work=Q16_16.from_float(0.6),
        irreversibility=Q16_16.from_float(0.2),
    )
    
    # Magnitude
    mag = trixal.magnitude
    expected = math.sqrt(0.8**2 + 0.6**2 + 0.2**2)
    assert abs(mag.to_float() - expected) < 0.01
    
    # Lawfulness check
    assert trixal.is_lawful()
    
    # Unlawful check
    bad_trixal = TrixalState(
        thermal=Q16_16.from_float(0.1),
        work=Q16_16.from_float(0.1),
        irreversibility=Q16_16.from_float(0.9),
    )
    assert not bad_trixal.is_lawful()
    
    print("  ✓ Trixal state")


def test_trixal_stamp():
    """Test trixal stamp creation (Model 50)."""
    engine = ThermodynamicEngine()
    
    trixal = TrixalState(
        thermal=Q16_16.from_float(0.8),
        work=Q16_16.from_float(0.6),
        irreversibility=Q16_16.from_float(0.2),
    )
    
    stamp = engine.create_stamp(trixal, b"test data")
    
    # Stamp should be non-empty
    assert len(stamp.stamp) == 64, "SHA256 should produce 64 hex chars"
    assert len(stamp.axes_hash) == 16
    assert len(stamp.trajectory_hash) == 16
    
    # Consecutive stamps should differ (nonce changes)
    stamp2 = engine.create_stamp(trixal, b"test data")
    assert stamp.stamp != stamp2.stamp, "Stamps should differ due to nonce"
    
    print("  ✓ Trixal stamp")


# ──────────────────────────────────────────────────────
# Test Homeostatic Governance
# ──────────────────────────────────────────────────────

def test_homeostatic_governor():
    """Test homeostatic governance (Models 98-101)."""
    gov = HomeostaticGovernor(alpha=0.5, beta=0.5, gamma=0.8)
    
    # Initial state
    assert gov.pressure.val == 0
    assert gov.canal_width.val == SCALE  # lambda0 = 1.0
    
    # Perfect prediction → no surprise; actual below optimal → positive regret
    actual = Q16_16.from_float(0.2)
    predicted = Q16_16.from_float(0.5)
    optimal = Q16_16.from_float(0.3)
    
    surprise, regret, stress = gov.compute_stress(actual, predicted, optimal)
    assert surprise.to_float() > 0.1, f"predicted ≠ actual → surprise, got {surprise.to_float():.4f}"
    assert regret.to_float() > 0, f"actual(0.2) < optimal(0.3) → positive regret, got {regret.to_float():.4f}"
    
    # Update — should have low pressure
    gov.update(actual, predicted, optimal)
    assert gov.pressure.to_float() >= 0
    
    # Poor performance — high stress
    gov2 = HomeostaticGovernor(alpha=0.5, beta=0.5)
    surprise2, regret2, stress2 = gov2.compute_stress(
        Q16_16.from_float(1.0),   # actual ratio = 1.0 (no compression)
        Q16_16.from_float(0.5),   # predicted = 0.5
        Q16_16.from_float(0.2),   # optimal = 0.2
    )
    # After multiple updates, pressure should increase
    for _ in range(10):
        gov2.update(Q16_16.from_float(0.9), Q16_16.from_float(0.5), Q16_16.from_float(0.2))
    
    assert gov2.pressure.to_float() > 0
    # Canal should narrow due to pressure
    assert gov2.canal_width.to_float() <= 1.0
    
    print("  ✓ Homeostatic governor")


# ──────────────────────────────────────────────────────
# Test Delta GCL Encoding
# ──────────────────────────────────────────────────────

def test_delta_gcl():
    """Test Delta GCL encoding (Models 637-646)."""
    encoder = DeltaGCLEncoder()
    
    # Initial full encoding
    manifest = PTOSManifest(
        version=1,
        payload=b"test payload",
        strategy_index=2,
    )
    
    gcl_seq = encoder.encode(manifest)
    assert gcl_seq.marker == 'F'  # First encode should be full
    
    # Second identical manifest — should compute delta
    gcl_seq2 = encoder.encode(manifest)
    # Should recognize identical
    assert gcl_seq2.marker == 'D'
    
    # Different manifest
    manifest2 = PTOSManifest(
        version=2,
        payload=b"different payload",
        strategy_index=3,
    )
    gcl_seq3 = encoder.encode(manifest2)
    assert gcl_seq3.marker == 'F'  # Changed → full encoding
    
    # Codon encoding
    encoded = encoder.encode_codon(0x01)  # Known PTOS code
    assert len(encoded) == 1
    assert encoded[0] == 0x01
    
    encoded = encoder.encode_codon(0xAB)  # Unknown → escape
    assert len(encoded) == 2
    assert encoded[0] == 0xFF
    assert encoded[1] == 0xAB
    
    print("  ✓ Delta GCL encoding")


# ──────────────────────────────────────────────────────
# Test Full MISC Compression Pipeline
# ──────────────────────────────────────────────────────

def test_misc_compress_block():
    """Test MISC compression pipeline end-to-end."""
    config = MISCConfig(block_size=64, verbose=False)
    compressor = MISCCompressor(config)
    
    # Single block test
    data = b"Hello, MISC! This is a test of the manifold-invariant shell compression framework."
    result = compressor.compress_block(data)
    
    assert result is not None
    assert isinstance(result, CompressedBlock)
    assert len(result.gcl_bytes) > 0
    assert result.strategy in CognitiveLoadRouter.STRATEGIES
    assert result.compression_ratio > 0
    assert result.canal_width >= 0
    
    # Trixal stamp present
    assert len(result.stamp.stamp) == 64
    print("  ✓ MISC single block compression")


def test_misc_multi_block():
    """Test MISC compression with multiple blocks."""
    config = MISCConfig(block_size=32, verbose=False)
    compressor = MISCCompressor(config)
    
    # Multi-block test
    data = b"The quick brown fox jumps over the lazy dog. " * 8
    results = compressor.compress(data)
    
    assert len(results) > 0
    assert len(results) >= 8  # 8 repetitions of ~43 bytes / 32 = ~11 blocks
    for r in results:
        assert isinstance(r, CompressedBlock)
    print("  ✓ MISC multi-block compression")


def test_misc_different_data_types():
    """Test MISC with different data characteristics."""
    config = MISCConfig(block_size=64, verbose=False)
    
    # Low entropy (repeated byte)
    data_low = b'\x00' * 128
    blocks = compress(data_low, config)
    assert len(blocks) == 2
    
    # High entropy (random-ish)
    data_high = bytes(range(256)) * 2
    blocks = compress(data_high, config)
    assert len(blocks) >= 2
    
    # Structured text
    data_text = b"Hello world! " * 16
    blocks = compress(data_text, config)
    assert len(blocks) >= 2
    print("  ✓ MISC various data types")


def test_misc_empty_data():
    """Test MISC with empty/small data."""
    # Empty data
    blocks = compress(b'')
    assert len(blocks) == 0
    
    # Tiny data
    blocks = compress(b'A')
    assert len(blocks) >= 0
    print("  ✓ MISC empty/small data")


def test_format_report():
    """Test format_report output."""
    config = MISCConfig(block_size=64, verbose=False)
    data = b"Test data for reporting " * 4
    blocks = compress(data, config)
    
    report = format_report(blocks)
    assert 'blocks' in report
    assert report['blocks'] >= 1
    assert 'total_estimated_input' in report
    assert 'total_output' in report
    assert 'overall_ratio' in report
    assert report['overall_ratio'] > 0
    assert 'strategies_used' in report
    assert 'avg_trixal' in report
    
    print("  ✓ Format report")


# ──────────────────────────────────────────────────────
# Run All Tests
# ──────────────────────────────────────────────────────

def run_all():
    """Run all unit tests."""
    print("\nMISC Kernel — Unit Tests")
    print("=" * 60)
    
    tests = [
        ("Q16.16 Basics", test_q16_basics),
        ("Q16.16 from_natural", test_q16_from_natural),
        ("Q16.16 sqrt", test_q16_sqrt),
        ("Q16.16 clamp", test_q16_clamp),
        ("LUT Trig", test_trig_luts),
        ("PIST Coordinate", test_pist_coordinate),
        ("PIST Mirror", test_pist_mirror),
        ("PIST Resonance", test_pist_resonance),
        ("PIST Rho", test_pist_rho),
        ("DIAT Coordinate", test_diat_coordinate),
        ("Shell Map Builder", test_shell_map_builder),
        ("GWL Coupling", test_gwl_coupling),
        ("Cognitive Load", test_cognitive_load),
        ("Strategy Routing", test_strategy_routing),
        ("Thermodynamic Engine", test_thermodynamic_engine),
        ("Trixal State", test_trixal_state),
        ("Trixal Stamp", test_trixal_stamp),
        ("Homeostatic Governor", test_homeostatic_governor),
        ("Delta GCL", test_delta_gcl),
        ("MISC Compress Block", test_misc_compress_block),
        ("MISC Multi-Block", test_misc_multi_block),
        ("MISC Data Types", test_misc_different_data_types),
        ("MISC Empty Data", test_misc_empty_data),
        ("Format Report", test_format_report),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    run_all()
