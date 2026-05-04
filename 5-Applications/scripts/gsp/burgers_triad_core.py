import numpy as np

# Phase 1 — Build BurgersTriadCore
# Q16.16 in the AVM hot path

# Q16.16 Constants
Q16_SHIFT = 16
Q16_ONE = 1 << Q16_SHIFT
Q16_MAX = (1 << 31) - 1
Q16_MIN = -(1 << 31)

def float_to_q16(f: float) -> int:
    return q16_sat(int(f * Q16_ONE))

def q16_to_float(q: int) -> float:
    return q / Q16_ONE

_sat_count = 0

def get_sat_count() -> int:
    global _sat_count
    return _sat_count

def reset_sat_count():
    global _sat_count
    _sat_count = 0

def q16_sat(x: int) -> int:
    """Saturate to 32-bit signed integer."""
    global _sat_count
    if x > Q16_MAX:
        _sat_count += 1
        return Q16_MAX
    if x < Q16_MIN:
        _sat_count += 1
        return Q16_MIN
    return x

def q16_mul(x: int, y: int) -> int:
    """Q16.16 Multiplication with saturation."""
    # Multiply raw integers, then shift back by 16
    res = (x * y) >> Q16_SHIFT
    return q16_sat(res)

def triad_rhs(a: tuple[int, int, int], nu_eff: int) -> tuple[int, int, int]:
    """
    Triad equations (Burgers):
    da1/dt = -nu_eff a1 + 1/2(a1a2 + a2a3)
    da2/dt = -4nu_eff a2 - 1/2 a1^2 + a1a3
    da3/dt = -9nu_eff a3 - 3/2 a1a2
    """
    a1, a2, a3 = a
    
    # Precompute products
    a1_a2 = q16_mul(a1, a2)
    a2_a3 = q16_mul(a2, a3)
    a1_a3 = q16_mul(a1, a3)
    a1_a1 = q16_mul(a1, a1)
    
    # 1/2 is (1 << 15), 3/2 is (3 << 15), etc. Or just multiply and divide by 2
    # To maintain Q16 semantics, we can multiply by Q16 constants:
    HALF = 1 << 15
    THREE_HALVES = 3 << 15
    
    # da1/dt = -nu_eff * a1 + 1/2 * (a1a2 + a2a3)
    t1_1 = -q16_mul(nu_eff, a1)
    t1_2 = q16_mul(HALF, q16_sat(a1_a2 + a2_a3))
    da1 = q16_sat(t1_1 + t1_2)
    
    # da2/dt = -4 * nu_eff * a2 - 1/2 * a1^2 + a1a3
    FOUR = 4 << Q16_SHIFT
    t2_1 = -q16_mul(q16_mul(FOUR, nu_eff), a2)
    t2_2 = -q16_mul(HALF, a1_a1)
    t2_3 = a1_a3
    da2 = q16_sat(q16_sat(t2_1 + t2_2) + t2_3)
    
    # da3/dt = -9 * nu_eff * a3 - 3/2 * a1a2
    NINE = 9 << Q16_SHIFT
    t3_1 = -q16_mul(q16_mul(NINE, nu_eff), a3)
    t3_2 = -q16_mul(THREE_HALVES, a1_a2)
    da3 = q16_sat(t3_1 + t3_2)
    
    return (da1, da2, da3)

def rk2_step(a: tuple[int, int, int], nu_eff: int, dt: int) -> tuple[int, int, int]:
    """Midpoint RK2 step in Q16.16."""
    a1, a2, a3 = a
    
    k1 = triad_rhs(a, nu_eff)
    
    # Midpoint
    half_dt = dt >> 1
    a_mid = (
        q16_sat(a1 + q16_mul(k1[0], half_dt)),
        q16_sat(a2 + q16_mul(k1[1], half_dt)),
        q16_sat(a3 + q16_mul(k1[2], half_dt))
    )
    
    k2 = triad_rhs(a_mid, nu_eff)
    
    # Full step
    a_next = (
        q16_sat(a1 + q16_mul(k2[0], dt)),
        q16_sat(a2 + q16_mul(k2[1], dt)),
        q16_sat(a3 + q16_mul(k2[2], dt))
    )
    
    return a_next

def energy3(a: tuple[int, int, int]) -> int:
    """E = 1/2 (a1^2 + a2^2 + a3^2) in Q16.16."""
    a1, a2, a3 = a
    sum_sq = q16_sat(q16_sat(q16_mul(a1, a1) + q16_mul(a2, a2)) + q16_mul(a3, a3))
    HALF = 1 << 15
    return q16_mul(HALF, sum_sq)
