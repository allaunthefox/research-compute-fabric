# Post-Quantum Cryptography Posture — Research Stack

## Status: 2026-05-20

This document tracks the post-quantum (PQ) readiness of every encryption boundary in the Research Stack infrastructure.

## Component Matrix

| Component | Algorithm / Mechanism | PQ Status | Notes |
|-----------|---------------------|-----------|-------|
| **SSH (VPS)** | `mlkem768x25519-sha256` (hybrid) | **ENABLED** | OpenSSH 10.0 default KEX; `mlkem768x25519-sha256` is preferred |
| **Tailscale** | Noise + Kyber hybrid | **ENABLED** | Tailscale 1.58+ uses X25519Kyber768 automatically for all connections |
| **Secrets at rest (SOPS)** | age (X25519 + ChaCha20-Poly1305) | **NOT PQ** | No mature PQC age plugin in nixpkgs. Tracked: Mic92/sops-nix#885 |
| **TLS / HTTPS (Caddy)** | ECDHE + X25519 or P-256 | **NOT PQ** | Go 1.24+ has experimental X25519Kyber768; requires Caddy rebuild. Blocked by upstream port filtering anyway |
| **PostgreSQL (LXC 100)** | TLS 1.3 via OpenSSL 3.5.6 | **PARTIAL** | OpenSSL 3.5.6 supports `X25519Kyber768` but PostgreSQL 17 must be compiled with it |
| **Restic backups** | AES-256-GCM + Poly1305 | **NOT PQ** | Restic uses standard symmetric crypto; snapshot integrity is MAC-based, not signature-based |
| **Garage S3** | TLS 1.3 (if enabled) | **NOT PQ** | Garage v2.3.0 uses Rustls; PQ support pending in rustls |
| **Proxmox VE** | TLS 1.3 via OpenSSL 3.5.6 | **PARTIAL** | Proxmox Web UI uses OpenSSL 3.5.6 which supports PQ KEX, but not configured explicitly |

## What "Enabled" Means

- **SSH**: Every new SSH session to/from the VPS uses `mlkem768x25519-sha256`, a NIST FIPS 203-compliant hybrid key exchange. Even if X25519 is broken by a quantum computer, the ML-KEM-768 component remains secure.
- **Tailscale**: All tailnet traffic uses the Noise Framework with `X25519Kyber768`. This is automatic and requires no configuration.

## What Is NOT Post-Quantum

- **Age / SOPS**: The `age` format uses X25519 for file encryption. A sufficiently capable quantum computer could recover the private key from the public key and decrypt historical files. There is no production-ready PQC age plugin available in nixpkgs as of 2026-05-20. Candidates:
  - `age-plugin-keystore` (supports `mlkem768x25519` but requires Secret Service / D-Bus keyring)
  - Awaiting native `age` PQC support or a stable nixpkgs plugin.

- **Browser-facing TLS**: Caddy serves HTTPS with standard X25519 or P-256 ECDHE. Go 1.24 adds `X25519Kyber768` experimentally, but the deployed Caddy binary is built with an older toolchain and does not expose it.

## Remediation Roadmap

1. **Short term**: Continue using SOPS + age for secrets. When a PQC age plugin lands in nixpkgs, rotate all SOPS keys to the hybrid recipient format.
2. **Medium term**: Rebuild Caddy with Go 1.24+ and enable `X25519Kyber768` for TLS 1.3. Requires netcup to unblock ports 80/443 or switch to Tailscale Funnel.
3. **Long term**: Monitor NIST standardization of PQ signatures (ML-DSA / SLH-DSA). Once widely supported in OpenSSL / Go / Rustls, enable PQ certificates and signatures.

## Verification Commands

```bash
# Verify SSH server uses PQ KEX
ssh -vvv root@46.232.249.226 2>&1 | grep "kex"
# Expected: "kex: algorithm: mlkem768x25519-sha256"

# Verify Tailscale PQ
sudo tailscale debug derp
# Check: "using Kyber768X25519"
```

## References

- [NIST FIPS 203 — ML-KEM](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [OpenSSH PQ KEX](https://www.openssh.com/txt/release-9.7)
- [Tailscale PQ](https://tailscale.com/blog/post-quantum-cryptography)
- [sops-nix PQ issue](https://github.com/Mic92/sops-nix/issues/885)
- [Go PQ TLS](https://go.dev/doc/security/postquantum)
