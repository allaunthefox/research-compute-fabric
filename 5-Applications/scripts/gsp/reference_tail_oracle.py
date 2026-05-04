import numpy as np

# Phase 2 — Build reference tail oracle
# Allowed to use float64. Uses pseudo-spectral method for 1D Burgers.

class ReferenceTailOracle:
    def __init__(self, N=256, L=2*np.pi, nu=0.01):
        self.N = N
        self.L = L
        self.nu = nu
        self.x = np.linspace(0, L, N, endpoint=False)
        # Wavenumbers
        self.k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        
        # Dealiasing mask (2/3 rule)
        self.mask = np.abs(self.k) < (2.0/3.0) * (N/2)

    def initialize(self, a1: float, a2: float, a3: float):
        """u(x,0) = a1*sin(x) + a2*sin(2x) + a3*sin(3x)"""
        self.u = a1 * np.sin(self.x) + a2 * np.sin(2*self.x) + a3 * np.sin(3*self.x)
        self.u_hat = np.fft.fft(self.u)
        
    def step(self, dt: float):
        """RK4 step for u_t + u u_x = nu u_xx"""
        def rhs(u_h):
            u_real = np.fft.ifft(u_h).real
            ux_real = np.fft.ifft(1j * self.k * u_h).real
            # Non-linear term (u * u_x) in physical space, back to spectral
            nl_hat = np.fft.fft(u_real * ux_real)
            # Dealiasing
            nl_hat = nl_hat * self.mask
            # Diffusion term
            diff_hat = -self.nu * (self.k**2) * u_h
            return -nl_hat + diff_hat

        k1 = rhs(self.u_hat)
        k2 = rhs(self.u_hat + 0.5 * dt * k1)
        k3 = rhs(self.u_hat + 0.5 * dt * k2)
        k4 = rhs(self.u_hat + dt * k3)
        
        self.u_hat = self.u_hat + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        self.u = np.fft.ifft(self.u_hat).real

    def u_ref(self):
        return self.u
        
    def u_hat_k(self):
        # Return Fourier coefficients normalized (for sin(kx) components)
        # Note: sin(kx) = (e^{ikx} - e^{-ikx})/2i
        # So a_k sin(kx) maps to u_hat[k] = -i a_k (N/2)
        return self.u_hat / (self.N / 2)
        
    def a_k_extracted(self):
        """Extract triad amplitudes from high-res simulation."""
        uh = self.u_hat_k()
        # k=1, k=2, k=3
        # We know sin(kx) component is -Im(uh[k])
        a1 = -uh[1].imag
        a2 = -uh[2].imag
        a3 = -uh[3].imag
        return (a1, a2, a3)

    def E_tail(self):
        """E_tail(t) = Σ_{k>3} |û_k(t)|²"""
        # Sum energy in k > 3
        uh = self.u_hat_k()
        # Only take positive frequencies > 3
        idx = (self.k > 3)
        return 0.5 * np.sum(np.abs(uh[idx])**2)

    def L2_error(self, a_triad: tuple[float, float, float]):
        """Compare triad (a1, a2, a3) to high-res reference solution."""
        a1, a2, a3 = a_triad
        u_triad = a1 * np.sin(self.x) + a2 * np.sin(2*self.x) + a3 * np.sin(3*self.x)
        return np.sqrt(np.mean((self.u - u_triad)**2))

    def shock_indicator(self):
        """max_x |u_x| / max_x |u| or similar to indicate shock steepness."""
        ux = np.fft.ifft(1j * self.k * self.u_hat).real
        max_ux = np.max(np.abs(ux))
        # Large gradient indicates shock
        return max_ux
