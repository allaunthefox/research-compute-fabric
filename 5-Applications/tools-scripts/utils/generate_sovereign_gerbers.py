# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray

REPO_ROOT = Path(os.getenv("RESEARCH_STACK_ROOT") or Path(__file__).resolve().parents[1])

def hilbert(x0, y0, xi, xj, yi, yj, n):
    if n <= 0:
        return [(x0 + (xi + yi)/2, y0 + (xj + yj)/2)]
    else:
        pts = []
        pts.extend(hilbert(x0,               y0,               yi/2, yj/2, xi/2, xj/2, n-1))
        pts.extend(hilbert(x0 + xi/2,        y0 + xj/2,        xi/2, xj/2, yi/2, yj/2, n-1))
        pts.extend(hilbert(x0 + xi/2 + yi/2, y0 + xj/2 + yj/2, xi/2, xj/2, yi/2, yj/2, n-1))
        pts.extend(hilbert(x0 + xi/2 + yi - 1, y0 + xj/2 + yj - 1, -yi/2, -yj/2, -xi/2, -xj/2, n-1))
        return pts

def generate_resonant_gerbers(output_dir=None):
    output_dir = Path(output_dir or (REPO_ROOT / "manufacturing"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # RS-274X Header
    header = "G04 Resonant v5-N Power Bridge Platform Gerber Export*\n%FSLAX24Y24*%\n%MOMM*%\n%ADD10C,0.150*%G54D10*\n"
    
    # 1. GENERATE TOP COPPER (6th-Order Hilbert Connectome)
    # Increased density for v5-N Rayleigh heterodyne stability
    points = hilbert(5, 5, 90, 0, 0, 90, 6) 
    
    with open(output_dir / "Resonant_v5N_TopCopper.GTL", "w") as f:
        f.write(header)
        f.write("G01*\n")
        p_start = points[0]
        f.write(f"X{int(p_start[0]*1000):06d}Y{int(p_start[1]*1000):06d}D02*\n")
        for i in range(1, len(points)):
            p = points[i]
            f.write(f"X{int(p[0]*1000):06d}Y{int(p[1]*1000):06d}D01*\n")
            
        # 2. ADD IR SENSING APERTURES (Rayleigh/Mie)
        f.write("G04 IR SENSING APERTURE (940nm LED & PD)*\n")
        f.write("X010000Y010000D02*X015000Y010000D01*X015000Y015000D01*X010000Y015000D01*X010000Y010000D01*\n")
        
        # 3. ADD AEM20940 HARVESTING STAGE (Cold Start 60mV)
        f.write("G04 AEM20940 ALCHEMY STAGE*\n")
        f.write("X080000Y080000D02*X095000Y080000D01*X095000Y095000D01*X080000Y095000D01*X080000Y080000D01*\n")
        
        # 4. ADD PENTAGONAL RF ARRAY (Power Bridge Phased Matrix)
        f.write("G04 PENTAGONAL RF ARRAY*\n")
        centers = [(50+30*xp.cos(a), 50+30*xp.sin(a)) for a in [0, 1.256, 2.513, 3.769, 5.026]]
        for cx, cy in centers:
            f.write(f"X{int(cx*1000):06d}Y{int(cy*1000):06d}D02*")
            f.write(f"X{int((cx+4)*1000):06d}Y{int(cy*1000):06d}D01*")
            f.write(f"X{int((cx+4)*1000):06d}Y{int((cy+4)*1000):06d}D01*")
            f.write(f"X{int(cx*1000):06d}Y{int((cy+4)*1000):06d}D01*")
            f.write(f"X{int(cx*1000):06d}Y{int(cy*1000):06d}D01*\n")
            
        f.write("M02*\n")

    # 5. BOTTOM COPPER (Faraday Shield & Precision Waveguide)
    with open(output_dir / "Resonant_v5N_BottomCopper.GBL", "w") as f:
        f.write(header)
        f.write("G01*\n")
        f.write("X000000Y000000D02*X100000Y000000D01*X100000Y100000D01*X000000Y100000D01*X000000Y000000D01*\n")
        f.write("M02*\n")

    print(f"Gerber v5-N SPARKGAP Export Complete: {output_dir}")

if __name__ == "__main__":
    generate_resonant_gerbers()
