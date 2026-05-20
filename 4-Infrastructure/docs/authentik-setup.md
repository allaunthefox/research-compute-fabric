# Authentik Setup Guide — Research Stack

## Status: 2026-05-21

Authentik is deployed in LXC 100 with local PostgreSQL 16 and Redis.

### Current State

- **URL**: `https://auth.researchstack.info` (Caddy reverse proxy -> `192.168.100.100:9000`)
- **Default admin**: `akadmin` / `authentik` (CHANGE THIS IMMEDIATELY)
- **Backend**: PostgreSQL 16 in Docker (`authentik-postgresql`)

### Step 1: First Login & Bootstrap

1. Open `https://auth.researchstack.info` (use SSH tunnel if netcup ports blocked)
2. Login with `akadmin` / `authentik`
3. Go to **Admin Interface** (top right)
4. Navigate to **Directory -> Users -> akadmin**
5. Change password to a strong unique password
6. (Optional) Add your email for recovery

### Step 2: Create Forward Auth Provider (for Caddy)

This protects `vault.researchstack.info` and future ARR services.

1. In Admin Interface, go to **Applications -> Providers**
2. Click **Create**
3. Select **Proxy Provider**
4. Fill in:
   - **Name**: `caddy-forward-auth`
   - **Authorization flow**: `default-provider-authorization-implicit-consent`
   - **Internal host**: `http://192.168.100.100:9100` (vault service)
   - **External host**: `https://vault.researchstack.info`
   - **Mode**: `Forward domain`
5. Save

### Step 3: Create Application

1. Go to **Applications -> Applications**
2. Click **Create**
3. Fill in:
   - **Name**: `Credential Vault`
   - **Slug**: `vault`
   - **Provider**: `caddy-forward-auth`
4. Save

### Step 4: Configure Outpost

1. Go to **Applications -> Outposts**
2. The **authentik Embedded Outpost** is already running
3. Edit it, add `Credential Vault` to the list of applications
4. Save

The outpost listens on `192.168.100.100:9000` (same as Authentik).

### Step 5: Update Caddy Forward Auth

On the VPS, edit `/opt/caddy/Caddyfile`:

```caddy
vault.researchstack.info {
    tls {
        dns porkbun { ... }
    }
    forward_auth 192.168.100.100:9000 {
        uri /outpost.goauthentik.io/auth/caddy
        copy_headers X-Authentik-Username X-Authentik-Groups X-Authentik-Email X-Authentik-Name
    }
    reverse_proxy 192.168.100.100:9100
}
```

Then reload:
```bash
/opt/caddy/caddy reload --config /opt/caddy/Caddyfile
```

### Step 6: Test

1. Open `https://vault.researchstack.info` in an incognito window
2. You should be redirected to Authentik login
3. After logging in, you should see the credential vault JSON response

### Step 7: Add Users

1. Go to **Directory -> Users**
2. Create users for anyone who needs access
3. (Optional) Add users to **Directory -> Groups** for role-based access

### Next: ARR Stack Apps

For each ARR service, repeat Steps 2-5:

| Service | Internal Host | External Host | Provider Name |
|---------|--------------|---------------|---------------|
| Sonarr  | `http://192.168.100.100:8989` | `https://sonarr.researchstack.info` | `sonarr-forward-auth` |
| Radarr  | `http://192.168.100.100:7878` | `https://radarr.researchstack.info` | `radarr-forward-auth` |
| Lidarr  | `http://192.168.100.100:8686` | `https://lidarr.researchstack.info` | `lidarr-forward-auth` |
| Readarr | `http://192.168.100.100:8787` | `https://readarr.researchstack.info` | `readarr-forward-auth` |
| Prowlarr| `http://192.168.100.100:9696` | `https://prowlarr.researchstack.info` | `prowlarr-forward-auth` |
| Bazarr  | `http://192.168.100.100:6767` | `https://bazarr.researchstack.info` | `bazarr-forward-auth` |

All can use the same embedded outpost.

### Troubleshooting

**Certificate errors?**
- Check `journalctl -u caddy` on the VPS

**Authentik not reachable?**
- Verify Docker containers in LXC 100: `pct exec 100 -- docker ps`
- Check Authentik logs: `pct exec 100 -- docker logs authentik-server`

**Forward auth not working?**
- Verify outpost application assignment
- Check Caddy logs for `forward_auth` errors
- Ensure `auth.researchstack.info` is accessible (the outpost needs to redirect there)
