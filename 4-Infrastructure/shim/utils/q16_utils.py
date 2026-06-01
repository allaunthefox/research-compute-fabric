Q16_SCALE = 65536
Q16_ONE = 0x00010000
Q16_MIN = -32768
Q16_MAX = 32767


def q16_from_int(val: int) -> int:
    return val << 16


def q16_to_float(val: int) -> float:
    return val / Q16_SCALE


def q16_from_float(val: float) -> int:
    return max(Q16_MIN, min(Q16_MAX, int(val * Q16_SCALE)))


def q16_from_ratio(num: int, den: int) -> int:
    return (num << 16) // den if den != 0 else 0


def q16_add(a: int, b: int) -> int:
    return max(Q16_MIN, min(Q16_MAX, a + b))


def q16_sub(a: int, b: int) -> int:
    return max(Q16_MIN, min(Q16_MAX, a - b))


def q16_mul(a: int, b: int) -> int:
    return max(Q16_MIN, min(Q16_MAX, (a * b) >> 16))


def q16_div(a: int, b: int) -> int:
    return max(Q16_MIN, min(Q16_MAX, ((a << 16) // b) if b != 0 else 0))


def q16_neg(a: int) -> int:
    return max(Q16_MIN, min(Q16_MAX, -a))


def q16_abs(a: int) -> int:
    return a if a >= 0 else q16_neg(a)
