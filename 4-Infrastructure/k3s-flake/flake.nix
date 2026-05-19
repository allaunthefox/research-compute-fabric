{
  description = "Unified NixOS k3s topology — Research Stack. Zero embedded IPs or secrets.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    sops-nix.url = "github:Mic92/sops-nix";
  };

  outputs = { self, nixpkgs, sops-nix }:
    let
      lib = nixpkgs.lib;
      system = "x86_64-linux";

      mkNode = { hostName, extraModules ? [ ], serverAddr ? null, domain ? null }:
        assert hostName != "";
        nixpkgs.lib.nixosSystem {
          inherit system;
          specialArgs = { inherit hostName serverAddr domain; };
          modules = [
            sops-nix.nixosModules.sops
            ./k3s-configuration.nix
          ] ++ extraModules;
        };
    in {
      # ─────────────────────────────────────────────────────────────────
      # Topology configurations
      # Fill in hostName, serverAddr, and domain below
      # ─────────────────────────────────────────────────────────────────
      nixosConfigurations = {
        k3s-server = mkNode {
          hostName = "";          # e.g. "k3s-server"
          domain = "";            # e.g. "researchstack.info"
          extraModules = [ ./k3s-server.nix ];
        };

        k3s-core = mkNode {
          hostName = "";          # e.g. "k3s-core"
          serverAddr = "";        # e.g. "https://k3s-server.tail-XXXXX.ts.net:6443"
          extraModules = [ ./roles/core.nix ];
        };

        k3s-judge = mkNode {
          hostName = "";          # e.g. "k3s-judge"
          serverAddr = "";
          extraModules = [ ./roles/judge.nix ];
        };

        k3s-mirror = mkNode {
          hostName = "";          # e.g. "k3s-mirror"
          serverAddr = "";
          extraModules = [ ./roles/mirror.nix ];
        };

        k3s-edge = mkNode {
          hostName = "";          # e.g. "k3s-edge"
          serverAddr = "";
          extraModules = [ ./roles/edge.nix ];
        };

        k3s-foxtop = mkNode {
          hostName = "";          # e.g. "k3s-foxtop"
          serverAddr = "";
          extraModules = [ ./roles/foxtop.nix ];
        };
      };
    };
}
