# AGENTS.md

## Project

Envisaged is now a Nix-first CLI for generating Gource-based repository timeline videos.

## Engineering conventions

- Keep the project Docker-free.
- Python app layout lives in `src/envisaged/`.
- Dependency management is `uv` (`pyproject.toml` + `uv.lock`).
- Nix packaging is `uv2nix`-backed (`flake.nix`).
- Preserve deterministic behavior for `nix run .`.
- Validate new CLI options with at least one real render.

## CLI expectations

- `nix run . -- --help` must always work.
- `uv run envisaged --help` must work in a synced dev environment.
- `scripts/envisaged` is a compatibility shim that delegates to the Python CLI.
- Supported template values should be documented in `README.md`.

## Quality gates

- `uv run ruff check .`
- `uv run pyright`
- `nix fmt` (treefmt)

## Release hygiene

- Do not commit generated MP4 artifacts.
- Keep `.gitignore` updated for local outputs.
- Keep README examples executable as written.
