{ config, pkgs, lib, hostName, serverAddr, domain, ... }:

{
  ##########################################################################
  # k3s-server.nix — NixOS storage + k3s SERVER node
  #
  # Changed from agent to server to run Traefik for path-based routing.
  # Host Caddy remains as stable fallback on :80, forwards to Traefik.
  #
  # Architecture:
  #   cupfox (Debian, control-plane) — historical, may be migrated
  #   nixos (NixOS, server) — primary control plane with Traefik
  #   qfox-1 (CachyOS, agent) — foxtop compute, runs VCN/LUPINE daemons
  #   steamdeck (NixOS, agent) — GPU node
  #   racknerd (Debian, edge) — Caddy TLS termination
  #
  # Traffic flow:
  #   edge Caddy (racknerd:443) → host Caddy (nixos:80) → Traefik (nixos:30080) → Services
  #
  # Ray integration:
  #   Ray cluster runs in ray-system namespace (deployed separately via KubeRay)
  #   Ray dashboard exposed via IngressRoute at /server/ray
  #
  # VCN/LUPINE integration:
  #   Runs as separate daemons on GPU nodes (qfox-1, steamdeck)
  #   Not managed by k3s — uses LD_PRELOAD shim + IPC socket
  #
  # Deployment order:
  #   1. Deploy this config (enables Traefik on nixos-laptop)
  #   2. Apply Ingress + Middleware manifests (including ray-ingress.yaml)
  #   3. Deploy new pods (hermes, credential-server, etc.)
  #   4. Verify internally (curl -H Host:... http://100.102.173.61/...)
  #   5. Deploy k3s-edge (last)
  ##########################################################################

  sops.secrets.k3s-token = {
    sopsFile = ./secrets/k3s-token.age;
    format = "yaml";
  };

  systemd.services.k3s.serviceConfig.EnvironmentFile = [
    config.sops.secrets.k3s-token.path
  ];

  # ── k3s as SERVER (not agent) to run Traefik ─────────────────────────────
  services.k3s = {
    enable = true;
    role = "server";  # CHANGED from agent to server
    # Traefik is ENABLED by default (no --disable=traefik)
    # ServiceLB is ENABLED by default (no --disable-servicelb)
    extraFlags = toString [
      "--node-ip=100.102.173.61"
      "--node-external-ip=100.102.173.61"
      "--flannel-iface=tailscale0"
      "--node-label=topology.researchstack.info/role=storage"
      "--node-label=topology.researchstack.io/gpu=false"
      "--node-label=topology.researchstack.io/storage-tier=nvme-ssd"
      # k3s API on 30443 to avoid conflict with potential future host-level 6443
      "--https-listen-port=30443"
      # ServiceLB is ENABLED by default for NodePort assignment
    ];
  };

  # ── Namespace for Ray cluster (created if not exists) ──────────────────────
  # Ray operator will create ray-system namespace, but we declare it here for clarity
  systemd.services.create-ray-namespace = {
    description = "Create ray-system namespace";
    wantedBy = [ "multi-user.target" ];
    after = [ "k3s.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = false;
    };
    script = ''
      set -euo pipefail
      ${pkgs.kubectl}/bin/kubectl --kubeconfig=/etc/rancher/k3s/k3s.yaml \
        create namespace ray-system --dry-run=client -o yaml | \
        ${pkgs.kubectl}/bin/kubectl --kubeconfig=/etc/rancher/k3s/k3s.yaml apply -f -
    '';
  };

  # ── Host Caddy — Stable fallback + forwarder to Traefik ──────────────────
  # Caddy terminates TLS for researchstack.info + subdomains at the edge.
  # For this node (nixos-laptop), host Caddy listens on :80 (HTTP only, no TLS)
  # and forwards to Traefik which handles path-based routing.
  #
  # Ray dashboard path: /server/ray → forwarded to Traefik → IngressRoute → ray-system
  # VCN/LUPINE: Not handled by Caddy (uses LD_PRELOAD + IPC socket on GPU nodes)
  services.caddy = {
    enable = true;
    package = pkgs.caddy;
    
    user = "root";
    group = "root";
    
    extraConfig = ''
      # Default global settings
      {
        admin 127.0.0.1:2019
        log {
          output stdout
          format single_field common_log
        }
      }
      
      # Primary domain — forward everything to Traefik
      # Traefik's web entrypoint is exposed via NodePort 30080
      researchstack.info {
        # Forward all paths to Traefik (handles path routing)
        # Ray dashboard at /server/ray will be routed by Traefik IngressRoute
        reverse_proxy 127.0.0.1:30080 {
          header_up Host {host}
          header_up X-Real-IP {remote}
          header_up X-Forwarded-For {remote}
          header_up X-Forwarded-Proto {scheme}
          header_up X-Forwarded-Host {host}
        }
      }
      
      # Auth subdomain — stable OIDC issuer
      auth.researchstack.info {
        reverse_proxy 127.0.0.1:30080 {
          header_up Host auth.researchstack.info
          header_up X-Real-IP {remote}
          header_up X-Forwarded-For {remote}
          header_up X-Forwarded-Proto {scheme}
          header_up X-Forwarded-Host auth.researchstack.info
        }
      }
      
      # Mail subdomains — forward to Traefik (future mail Ingress)
      mail.${domain}, webmail.${domain} {
        reverse_proxy 127.0.0.1:30080 {
          header_up Host {host}
          header_up X-Real-IP {remote}
          header_up X-Forwarded-For {remote}
          header_up X-Forwarded-Proto {scheme}
          header_up X-Forwarded-Host {host}
        }
      }
      
      # Legacy subdomain redirects (for migration compatibility)
      # These are also defined at the edge, but we keep them here too
      status.${domain} {
        redir https://${domain}/server/status{uri} 301
      }
      
      dash.${domain}, home.${domain} {
        redir https://${domain}/ 301
      }
      
      media.${domain} {
        redir https://${domain}/apps/jellyfin{uri} 301
      }
      
      books.${domain} {
        redir https://${domain}/apps/books{uri} 301
      }
      
      music.${domain} {
        redir https://${domain}/apps/music{uri} 301
      }
      
      vault.${domain} {
        redir https://${domain}/server/vault{uri} 301
      }
      
      pulse.${domain} {
        redir https://${domain}/api/registry{uri} 301
      }
      
      apps.${domain} {
        redir https://${domain}/apps{uri} 301
      }
      
      chat.${domain} {
        redir https://${domain}/apps/chat{uri} 301
      }
      
      budget.${domain} {
        redir https://${domain}/apps/budget{uri} 301
      }
      
      www.${domain} {
        redir https://${domain}{uri} 301
      }
      
      # Ray subdomain (if needed for direct access)
      ray.${domain} {
        redir https://${domain}/server/ray{uri} 301
      }
      
      # Wildcard fallback
      *.${domain} {
        redir https://${domain}{uri} 301
      }
    '';
  };

  # ── Firewall — allow Caddy, Traefik, and Ray/VCN ports ────────────────────
  networking.firewall.allowedTCPPorts = [
    80      # host Caddy HTTP
    30080  # Traefik web entrypoint (NodePort)
    30443  # k3s API (moved from 6443)
    2379   # etcd client
    2380   # etcd client
    10250  # kubelet API
    10257  # kube-controller-manager
    10259  # kube-scheduler
    # Ray ports
    8265   # Ray dashboard
    6379   # Redis (used by Ray)
    # VCN/LUPINE ports
    14834  # VCN-LUPINE daemon UDP
  ];

  networking.firewall.allowedUDPPorts = [
    51820  # Tailscale
    8472   # Flannel VXLAN
    14834  # VCN-LUPINE daemon
  ];

  # ── Traefik NodePort assignment ────────────────────────────────────────────
  # We use a systemd service to ensure Traefik gets a predictable NodePort
  # This runs after k3s starts and patches the traefik service
  systemd.services.traefik-nodeport-fix = {
    description = "Ensure Traefik uses NodePort 30080 for web";
    wantedBy = [ "multi-user.target" ];
    after = [ "k3s.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = false;
      # Retry on failure
      RestartForceExitStatus = [ "1" "2" ];
      StartLimitIntervalSec = "60";
      StartLimitBurst = "3";
    };
    script = ''
      set -euo pipefail
      
      KUBECONFIG=/etc/rancher/k3s/k3s.yaml
      KCTL=${pkgs.kubectl}/bin/kubectl
      
      # Wait for k3s to be ready
      echo "Waiting for k3s API..."
      until $KCTL --kubeconfig=$$KUBECONFIG get nodes &>/dev/null; do
        sleep 2
      done
      
      echo "Waiting for Traefik service..."
      until $KCTL --kubeconfig=$$KUBECONFIG -n kube-system get svc traefik &>/dev/null; do
        sleep 2
      done
      
      # Patch Traefik service to use NodePort 30080 for web
      echo "Patching Traefik web port to 30080..."
      $KCTL --kubeconfig=$$KUBECONFIG -n kube-system patch svc traefik \
        --type=json \
        -p '[{"op": "replace", "path": "/spec/ports/0/nodePort", "value": 30080}]'
      
      # Also ensure websecure uses 30443
      echo "Patching Traefik websecure port to 30443..."
      $KCTL --kubeconfig=$$KUBECONFIG -n kube-system patch svc traefik \
        --type=json \
        -p '[{"op": "replace", "path": "/spec/ports/1/nodePort", "value": 30443}]'
      
      echo "Traefik NodePorts configured: web=30080, websecure=30443"
    '';
  };

  # ── Deploy manifests via systemd oneshot ──────────────────────────────────
  systemd.services.deploy-k3s-services = {
    description = "Deploy k3s services via kubectl apply";
    wantedBy = [ "multi-user.target" ];
    after = [ "k3s.service" "traefik-nodeport-fix.service" "create-ray-namespace.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = false;
    };
    script = ''
      set -euo pipefail
      
      KUBECONFIG=/etc/rancher/k3s/k3s.yaml
      KCTL=${pkgs.kubectl}/bin/kubectl
      MANIFEST_DIR=/etc/nixos/k3s-flake/manifests
      
      echo "Deploying manifests from $$MANIFEST_DIR..."
      $KCTL --kubeconfig=$$KUBECONFIG apply -k $$MANIFEST_DIR
      
      echo "Manifests deployed successfully"
    '';
  };

  services.tailscale.enable = true;
}
