{
  description = "Unified NixOS k3s topology — Research Stack. Zero embedded IPs or secrets.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
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
      nixosConfigurations = {
        k3s-server = mkNode {
          hostName = "nixos-laptop";
          domain = "researchstack.info";
          extraModules = [ ./k3s-server.nix ];
        };

        k3s-foxtop = mkNode {
          hostName = "qfox-1";
          serverAddr = "https://100.102.173.61:6443";
          extraModules = [ ./roles/foxtop.nix ];
        };

        k3s-mirror = mkNode {
          hostName = "361395-1";
          serverAddr = "https://100.102.173.61:6443";
          extraModules = [ ./roles/mirror.nix ];
        };

        k3s-edge = mkNode {
          hostName = "microvm-racknerd";
          domain = "researchstack.info";
          serverAddr = "https://100.102.173.61:6443";
          extraModules = [ ./k3s-edge.nix ];
        };

        k3s-core = mkNode {
          hostName = "nixos-steamdeck-1";
          serverAddr = "https://100.102.173.61:6443";
          extraModules = [ ./roles/core.nix ];
        };

        k3s-judge = mkNode {
          hostName = "";
          serverAddr = "";
          extraModules = [ ./roles/judge.nix ];
        };
      };

      packages.${system} = {
        nixos-anywhere = nixpkgs.legacyPackages.${system}.nixos-anywhere;
      };

      apps.${system}.install-edge = {
        type = "app";
        program = "${nixpkgs.legacyPackages.${system}.writeShellScript "install-edge" ''
          set -euo pipefail
          TARGET="''${1:-}"
          if [ -z "$TARGET" ]; then
            echo "Usage: nix run .#install-edge -- root@172.245.19.182"
            exit 1
          fi
          exec nix run github:nix-community/nixos-anywhere -- \
            --flake .#k3s-edge "$TARGET"
        ''}";
      };
    };
}
