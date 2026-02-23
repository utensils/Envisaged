{
  description = "Envisaged - Nix-first Gource video renderer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        envisaged = pkgs.writeShellApplication {
          name = "envisaged";
          runtimeInputs = with pkgs; [
            bash
            coreutils
            ffmpeg
            git
            gource
            xvfb-run
          ];
          text = builtins.readFile ./scripts/envisaged;
        };
      in {
        packages = {
          default = envisaged;
          envisaged = envisaged;
        };

        apps.default = {
          type = "app";
          program = "${envisaged}/bin/envisaged";
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            bash
            ffmpeg
            git
            gource
            xvfb-run
          ];

          shellHook = ''
            echo "Envisaged dev shell"
            echo "Run: envisaged --help"
          '';
        };
      });
}
