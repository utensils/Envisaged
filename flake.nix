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

        runtimeDeps = [
          virtualenv
          pkgs.ffmpeg
          pkgs.git
          pkgs.gource
          pkgs.xvfb-run
          pkgs.bash
          pkgs.coreutils
          pkgs.curl
        ];

        envisaged-cli = pkgs.writeShellApplication {
          name = "envisaged";
          runtimeInputs = runtimeDeps;
          text = ''
            exec ${virtualenv}/bin/envisaged "$@"
          '';
        };

        envisaged-web = pkgs.writeShellApplication {
          name = "envisaged-web";
          runtimeInputs = runtimeDeps;
          text = ''
            exec ${virtualenv}/bin/envisaged-web "$@"
          '';
        };

        lastModified = self.lastModifiedDate or "19700101000000";
        dockerCreated =
          "${builtins.substring 0 4 lastModified}-${builtins.substring 4 2 lastModified}-${builtins.substring 6 2 lastModified}"
          + "T${builtins.substring 8 2 lastModified}:${builtins.substring 10 2 lastModified}:${builtins.substring 12 2 lastModified}Z";

        dockerRoot = pkgs.buildEnv {
          name = "envisaged-docker-root";
          paths = runtimeDeps ++ [ envisaged-cli envisaged-web ];
          pathsToLink = [ "/bin" ];
        };

        docker-cli = pkgs.dockerTools.buildImage {
          name = "envisaged-cli";
          tag = "latest";
          created = dockerCreated;
          copyToRoot = dockerRoot;
          config = {
            Cmd = [ "/bin/envisaged" ];
            WorkingDir = "/work";
            Env = [ "PATH=/bin" ];
          };
        };

        docker-web = pkgs.dockerTools.buildImage {
          name = "envisaged-web";
          tag = "latest";
          created = dockerCreated;
          copyToRoot = dockerRoot;
          config = {
            Cmd = [ "/bin/envisaged-web" ];
            ExposedPorts = { "8787/tcp" = { }; };
            WorkingDir = "/work";
            Env = [ "PATH=/bin" ];
          };
        };

        treefmtEval = treefmt-nix.lib.evalModule pkgs ./treefmt.nix;
      in
      {
        packages = {
          default = envisaged-cli;
          cli = envisaged-cli;
          web = envisaged-web;
          envisaged = envisaged-cli;
          envisaged-web = envisaged-web;
          docker-cli = docker-cli;
          docker-web = docker-web;
          venv = virtualenv;
        };

        apps = {
          default = {
            type = "app";
            program = "${envisaged-cli}/bin/envisaged";
          };
          cli = {
            type = "app";
            program = "${envisaged-cli}/bin/envisaged";
          };
          web = {
            type = "app";
            program = "${envisaged-web}/bin/envisaged-web";
          };
        };

        formatter = treefmtEval.config.build.wrapper;

        checks = {
          formatting = treefmtEval.config.build.check self;
        };

        devShells.default = pkgs.mkShell {
          packages = runtimeDeps ++ [
            pkgs.uv
            pkgs.ruff
            pkgs.pyright
            pkgs.treefmt
          ];

          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = "${python.interpreter}";
            UV_PYTHON_DOWNLOADS = "never";
          };

          shellHook = ''
            unset PYTHONPATH
            echo "Envisaged dev shell"
            echo "Commands: uv run envisaged --help | uv run envisaged-web | ruff check . | pyright"
          '';
        };
      }
    );
}
