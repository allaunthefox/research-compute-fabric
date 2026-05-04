import numpy as np
import math

# Constants in Q16.16
Q_ONE = 0x00010000
DRAKE_CONST = 196
DRIFT_CONST = 65
LAMBDA = Q_ONE
M_STAR = 32768

def get_ne_log(bin_val):
    n = bin_val + 1
    return int(math.log2(n) * Q_ONE)

def is_locally_lawful(mu_bin, rho_bin, c_bin, m_bin, ne_bin, sig_bin):
    uq   = 0x41 * (mu_bin + 1)
    rhoq  = 0x2000 * (rho_bin + 1)
    cfac  = 0x2000 * (c_bin + 1)
    mfac  = 0x2000 * (m_bin + 1)
    sigq  = Q_ONE + (0x4000 * (sig_bin + 1))
    Ne    = get_ne_log(ne_bin)

    l1 = uq <= (DRAKE_CONST * Q_ONE) // cfac
    phi = Q_ONE - abs(mfac - M_STAR)
    drift_val = ((rhoq * Ne) // Q_ONE * phi) // Q_ONE
    l2 = drift_val >= DRIFT_CONST
    l3 = sigq > Q_ONE + (LAMBDA * uq) // Q_ONE
    
    mask = (1 if not l1 else 0) | (2 if not l2 else 0) | (4 if not l3 else 0)
    return (l1 and l2 and l3), mask

def solve_trajectory(mu_bin, rho_bin, c_bin, m_bin, ne_bin, sig_bin):
    curr = (mu_bin, rho_bin, c_bin, m_bin, ne_bin, sig_bin)
    states = [curr]
    lawful_trajectory = True
    
    for s in range(3):
        m, r, c, mo, n, s_val = states[-1]
        ok, _ = is_locally_lawful(m, r, c, mo, n, s_val)
        if not ok:
            lawful_trajectory = False
        
        # Beta Function: Coarse-graining
        new_mu = max(0, m - 1)
        new_ne = min(7, n + 1)
        states.append((new_mu, r, c, mo, new_ne, s_val))
        
    return lawful_trajectory, states[-1]

def generate_lut():
    dt = np.dtype([
        ('bits', 'u1'),     # L_now|L_flow|L_att|Noise|Sab
        ('failure', 'u1'),  # Mask: 1|2|4|8
        ('cost', 'u4'),
        ('margin', 'u1'),
        ('depth', 'u1'),
        ('attr_id', 'u1'),
        ('p1', 'u1'), ('p2', 'u1'), ('p3', 'u1'), ('p4', 'u1'), ('p5', 'u1'), ('p6', 'u1'), ('p7', 'u1')
    ])
    lut = np.zeros(262144, dtype=dt)

    for addr in range(262144):
        mu_bin  = (addr >> 0)  & 0x7
        rho_bin = (addr >> 3)  & 0x7
        c_bin   = (addr >> 6)  & 0x7
        m_bin   = (addr >> 9)  & 0x7
        ne_bin  = (addr >> 12) & 0x7
        sig_bin = (addr >> 15) & 0x7

        l_now, mask = is_locally_lawful(mu_bin, rho_bin, c_bin, m_bin, ne_bin, sig_bin)
        l_flow, attractor = solve_trajectory(mu_bin, rho_bin, c_bin, m_bin, ne_bin, sig_bin)
        
        bits = (1 if l_now else 0) | (2 if l_flow else 0)
        final_mask = mask | (8 if l_now and not l_flow else 0)
        
        lut[addr] = (bits, final_mask, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0)
    
    return lut

if __name__ == "__main__":
    lut_data = generate_lut()
    output_path = "/home/allaun/Documents/Research Stack/data/swarm/adaptation_surface.bin"
    lut_data.tofile(output_path)
    print(f"SUCCESS: Precomputed RGFlow Trajectories (16-byte Master Entry)")
