#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
import time
from typing import List

try:
    from scripts.gpgpu_surface import get_surface
except ImportError:
    from gpgpu_surface import get_surface


def main() -> int:
    surface = get_surface()
    vec: List[float] = [float(i) / 1000.0 for i in range(200000)]

    t0 = time.perf_counter()
    mu = surface.mean(vec)
    sigma = surface.std(vec)
    zs = surface.zscores(vec)
    probs = surface.softmax(vec[:1024], temperature=0.5)
    t1 = time.perf_counter()

    print(
        json.dumps(
            {
                "backend": surface.backend,
                "vector_size": len(vec),
                "mean": mu,
                "std": sigma,
                "zsample": zs[:5],
                "softmax_sample": probs[:5],
                "elapsed_ms": round((t1 - t0) * 1000.0, 3),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
