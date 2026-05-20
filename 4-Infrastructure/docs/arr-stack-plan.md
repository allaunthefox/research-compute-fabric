# ARR Stack Deployment Plan — Research Stack

## Overview

The *ARR stack is a suite of media management tools for TV, movies, music, books, and subtitles. All services will run in LXC 100 (or a new LXC) behind Authentik + Caddy.

## Architecture

```
User -> Caddy (TLS) -> Authentik (forward auth) -> ARR Service
                                      |
                                      v
                              LXC 100 Docker Network
```

All services connect through the existing `authentik_default` Docker network in LXC 100.

## Service Matrix

| Service | Port | Image | Purpose |
|---------|------|-------|---------|
| **Sonarr** | 8989 | `linuxserver/sonarr:latest` | TV series management |
| **Radarr** | 7878 | `linuxserver/radarr:latest` | Movie management |
| **Lidarr** | 8686 | `linuxserver/lidarr:latest` | Music management |
| **Readarr** | 8787 | `linuxserver/readarr:develop` | Ebook/audiobook management |
| **Prowlarr** | 9696 | `linuxserver/prowlarr:latest` | Indexer manager (feeds the *arrs) |
| **Bazarr** | 6767 | `linuxserver/bazarr:latest` | Subtitle management |
| **Jellyfin** (optional) | 8096 | `jellyfin/jellyfin:latest` | Media server (frontend) |

## Docker Compose Fragment

Add to a new file `/opt/arr-stack/docker-compose.yml` in LXC 100:

```yaml
services:
  sonarr:
    image: linuxserver/sonarr:latest
    container_name: sonarr
    environment:
      PUID: 1000
      PGID: 1000
      TZ: America/Chicago
    volumes:
      - sonarr-config:/config
      - /mnt/media/tv:/tv
      - /mnt/media/downloads:/downloads
    ports:
      - "8989:8989"
    networks:
      - authentik_default
    restart: unless-stopped

  radarr:
    image: linuxserver/radarr:latest
    container_name: radarr
    environment:
      PUID: 1000
      PGID: 1000
      TZ: America/Chicago
    volumes:
      - radarr-config:/config
      - /mnt/media/movies:/movies
      - /mnt/media/downloads:/downloads
    ports:
      - "7878:7878"
    networks:
      - authentik_default
    restart: unless-stopped

  lidarr:
    image: linuxserver/lidarr:latest
    container_name: lidarr
    environment:
      PUID: 1000
      PGID: 1000
      TZ: America/Chicago
    volumes:
      - lidarr-config:/config
      - /mnt/media/music:/music
      - /mnt/media/downloads:/downloads
    ports:
      - "8686:8686"
    networks:
      - authentik_default
    restart: unless-stopped

  readarr:
    image: linuxserver/readarr:develop
    container_name: readarr
    environment:
      PUID: 1000
      PGID: 1000
      TZ: America/Chicago
    volumes:
      - readarr-config:/config
      - /mnt/media/books:/books
      - /mnt/media/downloads:/downloads
    ports:
      - "8787:8787"
    networks:
      - authentik_default
    restart: unless-stopped

  prowlarr:
    image: linuxserver/prowlarr:latest
    container_name: prowlarr
    environment:
      PUID: 1000
      PGID: 1000
      TZ: America/Chicago
    volumes:
      - prowlarr-config:/config
    ports:
      - "9696:9696"
    networks:
      - authentik_default
    restart: unless-stopped

  bazarr:
    image: linuxserver/bazarr:latest
    container_name: bazarr
    environment:
      PUID: 1000
      PGID: 1000
      TZ: America/Chicago
    volumes:
      - bazarr-config:/config
      - /mnt/media/movies:/movies
      - /mnt/media/tv:/tv
    ports:
      - "6767:6767"
    networks:
      - authentik_default
    restart: unless-stopped

  # Optional: Jellyfin media server
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin
    environment:
      PUID: 1000
      PGID: 1000
      TZ: America/Chicago
    volumes:
      - jellyfin-config:/config
      - jellyfin-cache:/cache
      - /mnt/media:/media:ro
    ports:
      - "8096:8096"
    networks:
      - authentik_default
    restart: unless-stopped

volumes:
  sonarr-config:
  radarr-config:
  lidarr-config:
  readarr-config:
  prowlarr-config:
  bazarr-config:
  jellyfin-config:
  jellyfin-cache:

networks:
  authentik_default:
    external: true
```

## Storage Layout

Create on the host (or in LXC 100 with a bind mount):

```
/mnt/media/
├── tv/
├── movies/
├── music/
├── books/
└── downloads/
```

The Proxmox host has 104GB free on `/dev/vda3`. For a media library, you may want to:
- Add a secondary disk to LXC 100
- Use the existing Garage S3 mesh for cold storage
- Or keep it minimal given the 120GB VPS constraint

## Caddy Additions

Add to `/opt/caddy/Caddyfile` on the VPS:

```caddy
sonarr.researchstack.info {
    tls { dns porkbun { ... } }
    forward_auth 192.168.100.100:9000 {
        uri /outpost.goauthentik.io/auth/caddy
        copy_headers X-Authentik-Username X-Authentik-Groups X-Authentik-Email X-Authentik-Name
    }
    reverse_proxy 192.168.100.100:8989
}

radarr.researchstack.info {
    tls { dns porkbun { ... } }
    forward_auth 192.168.100.100:9000 { ... }
    reverse_proxy 192.168.100.100:7878
}

# Repeat for lidarr, readarr, prowlarr, bazarr, jellyfin
```

## DNS Records Needed

Create A records in Porkbun pointing `46.232.249.226`:

- `sonarr.researchstack.info`
- `radarr.researchstack.info`
- `lidarr.researchstack.info`
- `readarr.researchstack.info`
- `prowlarr.researchstack.info`
- `bazarr.researchstack.info`
- `jellyfin.researchstack.info` (optional)

## Resource Estimate

With all services running in LXC 100 alongside Authentik:

| Service | RAM (typical) |
|---------|--------------|
| Authentik | 512MB |
| PostgreSQL | 256MB |
| Redis | 64MB |
| Vault | 64MB |
| Sonarr | 256MB |
| Radarr | 256MB |
| Lidarr | 256MB |
| Readarr | 256MB |
| Prowlarr | 256MB |
| Bazarr | 256MB |
| Jellyfin | 512MB |
| **Total** | **~3GB** |

The VPS has 4GB RAM. This is tight but workable if:
- Jellyfin is skipped (use direct file access or a separate media server)
- LXC 100 memory limits are tuned
- swap is available (but BTRFS + swap = bad, use zram instead)

## Deployment Order

1. **Storage**: Create `/mnt/media` and set correct permissions
2. **Prowlarr** first (other *arrs need it for indexers)
3. **Sonarr + Radarr** (the core pair)
4. **Bazarr** (needs Sonarr/Radarr for subtitle matching)
5. **Lidarr + Readarr** (optional, lower priority)
6. **Jellyfin** (optional, only if memory allows)
7. **Authentik providers** for each service
8. **Caddy + DNS** for each service

## Security Notes

- All ARR services have **no built-in auth** — they rely entirely on Authentik forward auth
- Ensure the Authentik provider mode is set to `Forward domain` with proper URL matching
- Never expose ARR ports directly; always route through Caddy + Authentik
- Disable ARR external access / API keys where possible (let Authentik handle auth)

## Next Steps

1. Configure Authentik forward auth (see `authentik-setup.md`)
2. Decide on media storage strategy (local vs Garage S3)
3. Create `docker-compose.yml` in LXC 100
4. Deploy Prowlarr first, then Sonarr/Radarr
