# AGENTS.md

## Project

Envisaged is now a Nix-first CLI for generating Gource-based repository timeline videos.

## Engineering conventions

- Keep the project Docker-free.
- Prefer simple, portable Bash over heavy framework rewrites unless requested.
- Preserve deterministic behavior for `nix run .`.
- Validate new CLI options with at least one real render.

## CLI expectations

- `nix run . -- --help` must always work.
- Keep `scripts/envisaged` self-contained and readable.
- Supported template values should be documented in `README.md`.

## Release hygiene

- Do not commit generated MP4 artifacts.
- Keep `.gitignore` updated for local outputs.
- Keep README examples executable as written.
