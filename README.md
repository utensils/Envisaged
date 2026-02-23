# Envisaged

Nix-first Git history visualizations powered by **Gource + FFmpeg**.

No Docker required.

## Features

- Headless rendering via `xvfb-run`
- Local repo path or remote git URL input
- Multi-repo mode (`--multi-dir`)
- Built-in visual templates:
  - `none`
  - `border`
  - `neon`
  - `sunset`
  - `matrix`
  - `blueprint`
  - `noir`
- Compare templates with legends + unified timing support:
  - `compare-panel`
  - `compare-neon`
  - `compare-blueprint`
  - `compare-matrix`
  - `compare-noir`
- Optional logo overlay (`--logo`)

## Quick start

```bash
# Show CLI help
nix run . -- --help

# Render current repo
nix run . -- -o output.mp4 -t "Repo History" .

# Render a remote repo
nix run . -- -o kubernetes.mp4 -t "Kubernetes" https://github.com/kubernetes/kubernetes.git

# Render all repos inside a directory
nix run . -- --multi-dir ~/Projects -o org-history.mp4 -t "Org History"

# Compare similar repos with unified timing + legend
nix run . -- --multi-dir ~/Projects/utensils \
  --template compare-panel \
  --sync-timing auto \
  -o compare.mp4 \
  -t "Repo Family Comparison"
```

## Template showcase examples

```bash
nix run . -- -o neon.mp4 --template neon -r 720p -f 30 -t "Neon" .
nix run . -- -o sunset.mp4 --template sunset -r 720p -f 30 -t "Sunset" .
nix run . -- -o matrix.mp4 --template matrix -r 720p -f 30 -t "Matrix" .
nix run . -- -o blueprint.mp4 --template blueprint -r 720p -f 30 -t "Blueprint" .
nix run . -- -o noir.mp4 --template noir -r 720p -f 30 -t "Noir" .
```

## Dev shell

```bash
nix develop
envisaged --help
```

## Notes

- Supported FPS values are constrained by Gource: `25`, `30`, `60`.
- For best turnaround during iteration, use `-r 720p -f 30`.

## License

MIT
