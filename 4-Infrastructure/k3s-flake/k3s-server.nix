{ config, pkgs, lib, hostName, serverAddr, domain, ... }:

{
  ##########################################################################
  # k3s-server.nix — Control plane + Traefik Ingress
  #
  # This node runs k3s in server mode. Traefik (k3s built-in) handles all
  # path-based routing inside the cluster via Ingress resources defined in
  # manifests/ingress/.
  #
  # Port layout:
  #   :80    — host Caddy pass-through (owns the port, Traefik cannot)
  #   :30080 — Traefik web NodePort (ServiceLB, bound by k3s)
  #
  # Traffic flow (internal leg):
  #   Edge Caddy (TLS, Porkbun, subdomain redirects) → Tailscale
  #     → host Caddy :80 → Traefik :30080 → k3s services (via Ingress)
  #
  # All TLS, Porkbun DNS-01, subdomain 301s, and wildcard catch-alls are
  # handled exclusively by the edge Caddy in k3s-edge.nix. Nothing here
  # does TLS or subdomain routing — this is a plain HTTP bridge.
  #
  # Traefik NodePort is configured via HelmChartConfig so it does not race
  # with the host Caddy for port 80.
  #
  # URL contract (defined in manifests/ingress/ingress.yaml):
  #   /                    → Homer directory
  #   /apps/chat/*         → Hermes (chat/orchestrator)
  #   /apps/budget/*       → Actual Budget
  #   /server/status/*     → Uptime Kuma
  #   /server/dash/*       → Homarr
  #   /server/vault/*      → Vaultwarden
  #   /api/cred/*          → Credential Server
  #   /api/registry/*      → Registry API (worker join/heartbeat)
  #   /api/jobs/*          → Job Router
  #   /api/blobs/*         → Blob Plane
  #   auth.researchstack.info → Authentik (stable OIDC issuer, via rs-auth Ingress)
  ##########################################################################

  sops.secrets.authentik-secrets = {
    sopsFile = ./secrets/authentik-secrets.age;
    format = "yaml";
  };

  services.k3s = {
    enable = true;
    role = "server";
    clusterInit = true;
    extraFlags = [
      "--tls-san=100.102.173.61"
      "--tls-san=researchstack.info"
      "--tls-san=nixos-laptop"
      "--advertise-address=100.102.173.61"
      "--node-ip=100.102.173.61"
      "--flannel-iface=tailscale0"
    ];
  };

  # ── Traefik entrypoint config (HelmChartConfig CRD) ────────────────────
  # k3s ships Traefik as a HelmChart. We override via HelmChartConfig to
  # bind the web entrypoint to NodePort 30080 instead of the default :80,
  # so the host Caddy can own :80 without a port conflict.
  #
  # k3s reads files placed under /var/lib/rancher/k3s/server/manifests/ and
  # reconciles them against the live cluster on startup.
  environment.etc."rancher/k3s/server/manifests/traefik-config.yaml".text = ''
    apiVersion: helm.cattle.io/v1
    kind: HelmChartConfig
    metadata:
      name: traefik
      namespace: kube-system
    spec:
      valuesContent: |-
        ports:
          web:
            port: 8000
            nodePort: 30080
            expose:
              default: true
            exposedPort: 30080
            protocol: TCP
          websecure:
            port: 8443
            nodePort: 30443
            expose:
              default: false
            protocol: TCP
        service:
          type: NodePort
        ingressRoute:
          dashboard:
            enabled: false
  '';

  # ── Host Caddy — plain HTTP pass-through (:80 → Traefik :30080) ────────
  # Owns port 80 on the Tailscale interface. All routing logic lives in
  # Traefik Ingress resources (manifests/ingress/). This Caddy instance is
  # intentionally minimal — no TLS, no subdomain logic, no Porkbun.
  services.caddy = {
    enable = true;
    package = pkgs.caddy;
    extraConfig = ''
      :80 {
        reverse_proxy 127.0.0.1:30080 {
          header_up Host {host}
          header_up X-Real-IP {remote}
          header_up X-Forwarded-For {remote}
          header_up X-Forwarded-Proto https
          header_up X-Forwarded-Host {host}
        }
      }
    '';
  };

  # Caddy starts after k3s so Traefik NodePort is ready before we proxy to it.
  systemd.services.caddy = {
    after = [ "k3s.service" "network-online.target" ];
    wants = [ "k3s.service" "network-online.target" ];
  };

  networking.firewall.allowedTCPPorts = [ 80 ];

  # ── Service deployment ──────────────────────────────────────────────────
  systemd.services.deploy-k3s-services = {
    description = "Deploy k3s topology services";
    after = [ "k3s.service" "tailscaled.service" "network-online.target" ];
    wants = [ "k3s.service" "tailscaled.service" "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ kubectl ];
    environment = {
      KUBECONFIG = "/etc/rancher/k3s/k3s.yaml";
      AUTHENTIK_SECRETS = "${config.sops.secrets.authentik-secrets.path}";
    };
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      Restart = "on-failure";
      RestartSec = 10;
      ExecStart = "${pkgs.bash}/bin/bash ${./scripts/deploy-services.sh}";
    };
  };
}
