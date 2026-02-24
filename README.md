# Envisaged

Nix-first Git history visualizations powered by **Gource + FFmpeg**.

This project is now a proper Python application with:

- `src/envisaged` package layout
- Rich + Typer CLI
- template system for core/compare/split/relation families
- `uv` project management (`pyproject.toml` + `uv.lock`)
- `uv2nix` packaging in `flake.nix`
- linting/type-checking via Ruff + Pyright
- repo-wide formatting via treefmt

## Quick start

### Nix

```bash
# CLI (default app)
nix run . -- --help

# Explicit app targets
nix run .#cli -- --help
nix run .#web

# Render current repo
nix run . -- -o output.mp4 -t "Repo History" .

# Render multi-repo compare
nix run . -- --multi-dir ~/Projects/utensils --template compare-panel --sync-timing auto -o compare.mp4
```

### Nix build targets

```bash
# Native package builds
nix build .#cli
nix build .#web

# Docker image builds
nix build .#docker-cli
nix build .#docker-web
```

### GitHub Actions container publishing

On every push to `main`, GitHub Actions builds and publishes both Nix Docker images to GHCR:

- `ghcr.io/<owner>/envisaged-cli:latest`
- `ghcr.io/<owner>/envisaged-web:latest`
- immutable SHA tags are also published: `:sha-<12-char-commit>`

### uv (local dev)

```bash
uv sync
uv run envisaged --help
```

### Web UI (Tailwind 4.1)

```bash
uv run envisaged-web
# open http://127.0.0.1:8787
```

Nix shell launch:

```bash
nix develop -c uv run envisaged-web
```

Network access:
- local: `http://127.0.0.1:8787`
- LAN/Tailscale: `http://<host-ip>:8787`

The web interface uses the same urandom-style visual language (zinc dark base, JetBrains Mono, gradient accents, subtle noise overlay) and is mobile-first.

Web UI extras:
- defaults to **single-repo** mode for fast one-off renders
- GitHub-like repo search (`owner/repo` picker)
- selected GitHub repos are cloned/updated locally under `/tmp/envisaged-web-repos`
- POST/redirect/GET flow avoids browser “submit form again” prompts

## CLI usage

```bash
envisaged [OPTIONS] [REPO]
```

- `REPO`: local git repo path or remote git URL
- `--multi-dir <path>`: render all git repos under a directory

### Template families

- **Core:** `none`, `urandom` *(default)*, `border`, `neon`, `sunset`, `matrix`, `blueprint`, `noir`
- **Omarchy core palettes:**
  - `omarchy-catppuccin`, `omarchy-catppuccin-latte`, `omarchy-ethereal`, `omarchy-everforest`
  - `omarchy-flexoki-light`, `omarchy-gruvbox`, `omarchy-hackerman`, `omarchy-kanagawa`
  - `omarchy-matte-black`, `omarchy-miasma`, `omarchy-nord`, `omarchy-osaka-jade`
  - `omarchy-ristretto`, `omarchy-rose-pine`, `omarchy-tokyo-night`, `omarchy-vantablack`, `omarchy-white`
- **Compare:** `compare-panel`, `compare-neon`, `compare-blueprint`, `compare-matrix`, `compare-noir`
- **Split:** `split-quad`, `split-vertical`, `split-triple`, `split-focus`, `split-matrix`
- **Relationship:** `relation-panel`, `relation-neon`, `relation-blueprint`, `relation-noir`, `relation-sunset`

### Sync modes

- `--sync-timing false`: original log timing
- `--sync-timing true`: normalized unified timeline
- `--sync-timing smart`: normalized timeline + blank-log pulse anchors
- `--sync-timing auto`: smart mode for compare/split/relation templates in multi-repo mode

### Legend modes

- `--legend auto`: repo legend for compare/split/relation templates, none otherwise
- `--legend none`: disable overlays
- `--legend repos`: show repo legend (best for multi-repo renders)
- `--legend files`: show top file types (`--legend-limit` controls count)
- `--legend actions`: show add/modify/delete totals
- `--legend all`: show repos + file types + actions

## Example videos

Legacy showcase renders from the original Envisaged project:

| Repo | Video |
|---|---|
| Elixir School | [![Elixir School Visualization](http://img.youtube.com/vi/twpR-opLrZU/0.jpg)](http://www.youtube.com/watch?feature=player_embedded&v=twpR-opLrZU) |
| Kubernetes | [![Kubernetes Visualization](http://img.youtube.com/vi/UTwxiwF7Zac/0.jpg)](http://www.youtube.com/watch?feature=player_embedded&v=UTwxiwF7Zac) |
| Elixir Lang | [![Elixir Lang Visualization](http://img.youtube.com/vi/wl5uuvDK3ao/0.jpg)](http://www.youtube.com/watch?feature=player_embedded&v=wl5uuvDK3ao) |

## Project structure

```text
src/envisaged/
  cli.py        # Rich/Typer CLI and render orchestration
  templates.py  # template family definitions
scripts/envisaged  # compatibility shim -> Python CLI
pyproject.toml
uv.lock
flake.nix       # uv2nix packaging + dev shell
treefmt.nix
```

## Linting & formatting

```bash
uv run ruff check .
uv run ruff format .
uv run pyright
nix fmt
```

## Notes

- Supported FPS values are constrained by Gource: `25`, `30`, `60`.
- Multi-repo overlays (legend/relationship) are rendered line-by-line via drawtext for broad font compatibility.
- `split-quad` in `--multi-dir` mode uses the first 4 repos as distinct panes.
- Web repo search clones/updates GitHub repos in `/tmp/envisaged-web-repos` for local rendering.
- Render outputs from web mode are written to `~/.openclaw/workspace/out/web/`.
- Docker images are built via Nix (`docker-cli` / `docker-web`) and stamped with the flake commit timestamp as image creation time.

## License

MIT
