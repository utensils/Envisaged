{ pkgs, ... }:
{
  projectRootFile = "flake.nix";

  programs = {
    nixfmt.enable = true;
    ruff-format.enable = true;
    ruff-check.enable = true;
  };

  settings.formatter.ruff-check.options = ["--fix"];
}
