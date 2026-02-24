{
  description = "Envisaged - Nix-first Git history renderer (Python + uv + uv2nix)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
    };

    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    pyproject-nix,
    uv2nix,
    pyproject-build-systems,
    treefmt-nix,
  }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        lib = pkgs.lib;

        workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
        python = pkgs.python311;

        pythonBase = pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        };

        overlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };

        pythonSet = pythonBase.overrideScope (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.wheel
            overlay
          ]
        );

        virtualenv = pythonSet.mkVirtualEnv "envisaged-env" workspace.deps.default;

        envisaged = pkgs.writeShellApplication {
          name = "envisaged";
          runtimeInputs = [
            virtualenv
            pkgs.ffmpeg
            pkgs.git
            pkgs.gource
            pkgs.xvfb-run
            pkgs.bash
            pkgs.coreutils
            pkgs.curl
          ];
          text = ''
            exec ${virtualenv}/bin/envisaged "$@"
          '';
        };

        treefmtEval = treefmt-nix.lib.evalModule pkgs ./treefmt.nix;
      in
      {
        packages = {
          default = envisaged;
          envisaged = envisaged;
          venv = virtualenv;
        };

        apps.default = {
          type = "app";
          program = "${envisaged}/bin/envisaged";
        };

        formatter = treefmtEval.config.build.wrapper;

        checks = {
          formatting = treefmtEval.config.build.check self;
        };

        devShells.default = pkgs.mkShell {
          packages = [
            virtualenv
            pkgs.uv
            pkgs.ruff
            pkgs.pyright
            pkgs.treefmt
            pkgs.ffmpeg
            pkgs.git
            pkgs.gource
            pkgs.xvfb-run
          ];

          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = "${python.interpreter}";
            UV_PYTHON_DOWNLOADS = "never";
          };

          shellHook = ''
            unset PYTHONPATH
            echo "Envisaged dev shell"
            echo "Commands: uv run envisaged --help | ruff check . | pyright"
          '';
        };
      }
    );
}
