# Recovery Guide

If EC2 server aws-nixos-node-1 (100.69.1.43) dies, rebuild from these files.

## Critical Files (committed to repo)
- `ec2-configuration.nix` — Full NixOS config (Caddy routes, AppFlowy, Forgejo, credential server)
- `docker-compose.minimal.yml` — Custom AppFlowy Cloud compose (in 5-Applications/AppFlowy-Cloud/)
- `nixos-setup-cred-server.sh` — Credential server bootstrap
- `credential_provider.py` — Credential resolution chain
- `credential_server.py` — Webhook handler
- `.env.example` — Sanitized AppFlowy Cloud env template

## Critical Files (NOT committed — in `secrets/` dir, gitignored)
- `credentials.json` — All 8 API provider keys
- `appflowy.env` — AppFlowy Cloud env (RDS host, JWT, encryption key)
- `tailscale-auth.key` — Tailscale auth key

## Recovery Flow
1. Launch new NixOS EC2 → copy `ec2-configuration.nix` to `/etc/nixos/`
2. Restore secrets from gitignored backup
3. `nixos-rebuild switch` — brings up Caddy, credential server, Forgejo, Heimdall
4. Deploy AppFlowy: copy compose + `.env` to `/var/lib/AppFlowy-Cloud/`, start stack
5. RDS (2,685 records) survives independently — reconnect AppFlowy to it
6. Forgejo repos lost unless backed up separately
7. Heimdall tiles lost unless backed up separately
