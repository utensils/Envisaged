from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateDef:
    name: str
    kind: str  # core | compare | split | relation
    simple_filter: str | None = None


DEFAULT_TEMPLATE = "urandom"

OMARCHY_PALETTES: dict[str, dict[str, str]] = {
    "catppuccin": {"background": "#1e1e2e", "accent": "#89b4fa", "alt": "#f5c2e7"},
    "catppuccin-latte": {"background": "#eff1f5", "accent": "#1e66f5", "alt": "#ea76cb"},
    "ethereal": {"background": "#060b1e", "accent": "#7d82d9", "alt": "#c89dc1"},
    "everforest": {"background": "#2d353b", "accent": "#7fbbb3", "alt": "#d699b6"},
    "flexoki-light": {"background": "#fffcf0", "accent": "#205ea6", "alt": "#ce5d97"},
    "gruvbox": {"background": "#282828", "accent": "#7daea3", "alt": "#d3869b"},
    "hackerman": {"background": "#0b0c16", "accent": "#82fb9c", "alt": "#7cf8f7"},
    "kanagawa": {"background": "#1f1f28", "accent": "#7e9cd8", "alt": "#957fb8"},
    "matte-black": {"background": "#121212", "accent": "#e68e0d", "alt": "#d35f5f"},
    "miasma": {"background": "#222222", "accent": "#78824b", "alt": "#bb7744"},
    "nord": {"background": "#2e3440", "accent": "#81a1c1", "alt": "#b48ead"},
    "osaka-jade": {"background": "#111c18", "accent": "#509475", "alt": "#d2689c"},
    "ristretto": {"background": "#2c2525", "accent": "#f38d70", "alt": "#a8a9eb"},
    "rose-pine": {"background": "#faf4ed", "accent": "#56949f", "alt": "#907aa9"},
    "tokyo-night": {"background": "#1a1b26", "accent": "#7aa2f7", "alt": "#ad8ee6"},
    "vantablack": {"background": "#0d0d0d", "accent": "#8d8d8d", "alt": "#b0b0b0"},
    "white": {"background": "#ffffff", "accent": "#1a1a1a", "alt": "#3e3e3e"},
}


def build_omarchy_filter(*, background: str, accent: str, alt: str) -> str:
    return (
        "pad={{w}}:{{h}}:{{frame}}:{{frame}}:{background},eq=saturation=1.12:contrast=1.1:brightness=-0.01,"
        "drawgrid=w=72:h=72:t=1:c={accent}@0.1,"
        "drawbox=x=0:y=0:w=iw:h=ih:color={accent}@0.34:t=4,"
        "drawbox=x=10:y=10:w=iw-20:h=ih-20:color={alt}@0.22:t=2"
    ).format(background=background, accent=accent, alt=alt)


TEMPLATES: dict[str, TemplateDef] = {
    "none": TemplateDef("none", "core", ""),
    "urandom": TemplateDef(
        "urandom",
        "core",
        "pad={w}:{h}:{frame}:{frame}:#05070b,eq=saturation=1.18:contrast=1.12:brightness=-0.01,"
        "curves=all='0/0 0.28/0.18 0.72/0.9 1/1',"
        "drawgrid=w=72:h=72:t=1:c=#00ffd0@0.08,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#00ffd0@0.36:t=4,"
        "drawbox=x=10:y=10:w=iw-20:h=ih-20:color=#7c3aed@0.22:t=2",
    ),
    "border": TemplateDef(
        "border",
        "core",
        "pad={w}:{h}:{frame}:{frame}:#222226,drawbox=x=0:y=0:w=iw:h=ih:color=#4d4d54@0.85:t=5",
    ),
    "neon": TemplateDef(
        "neon",
        "core",
        "pad={w}:{h}:{frame}:{frame}:#05030d,eq=saturation=1.45:contrast=1.20:brightness=-0.02,"
        "curves=all='0/0 0.35/0.22 0.7/0.88 1/1',drawgrid=w=80:h=80:t=1:c=#00ffd0@0.12,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#00ffd0@0.55:t=6",
    ),
    "sunset": TemplateDef(
        "sunset",
        "core",
        "colorbalance=rs=.12:gs=-.02:bs=-.10,eq=saturation=1.30:contrast=1.08:brightness=0.01,"
        "vignette=PI/7",
    ),
    "matrix": TemplateDef(
        "matrix",
        "core",
        "hue=s=0,curves=all='0/0 1/0.95',"
        "colorchannelmixer=rr=0:rg=0:rb=0:gr=0.15:gg=1.0:gb=0.05:br=0:bg=0:bb=0,"
        "noise=alls=8:allf=t,drawgrid=w=64:h=28:t=1:c=#00ff66@0.09",
    ),
    "blueprint": TemplateDef(
        "blueprint",
        "core",
        "pad={w}:{h}:{frame}:{frame}:#0b1e3f,"
        "colorchannelmixer=rr=0.10:rg=0.12:rb=0.30:gr=0.12:gg=0.50:gb=0.75:br=0.35:bg=0.55:bb=1.00,"
        "eq=saturation=0.75:contrast=1.12,drawgrid=w=90:h=90:t=1:c=#9fd0ff@0.16,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#9fd0ff@0.45:t=5",
    ),
    "noir": TemplateDef(
        "noir",
        "core",
        "hue=s=0,eq=contrast=1.25:brightness=-0.04,gblur=sigma=0.45,vignette=PI/5,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#ffffff@0.12:t=2",
    ),
    "compare-panel": TemplateDef(
        "compare-panel",
        "compare",
        "pad={w}:{h}:{frame}:{frame}:#1a1a21,eq=saturation=1.05:contrast=1.06,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#90b4ff@0.35:t=4",
    ),
    "compare-neon": TemplateDef(
        "compare-neon",
        "compare",
        "pad={w}:{h}:{frame}:{frame}:#03060c,eq=saturation=1.4:contrast=1.2,"
        "drawgrid=w=70:h=70:t=1:c=#00ffd0@0.1,drawbox=x=0:y=0:w=iw:h=ih:color=#00ffd0@0.45:t=5",
    ),
    "compare-blueprint": TemplateDef(
        "compare-blueprint",
        "compare",
        "pad={w}:{h}:{frame}:{frame}:#0b1e3f,"
        "colorchannelmixer=rr=0.10:rg=0.12:rb=0.30:gr=0.12:gg=0.50:gb=0.75:br=0.35:bg=0.55:bb=1.00,"
        "eq=saturation=0.8:contrast=1.12,drawgrid=w=84:h=84:t=1:c=#9fd0ff@0.16,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#9fd0ff@0.45:t=5",
    ),
    "compare-matrix": TemplateDef(
        "compare-matrix",
        "compare",
        "hue=s=0,colorchannelmixer=rr=0:rg=0:rb=0:gr=0.17:gg=1.0:gb=0.05:br=0:bg=0:bb=0,"
        "noise=alls=6:allf=t,drawgrid=w=64:h=28:t=1:c=#00ff66@0.09,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#00ff66@0.28:t=4",
    ),
    "compare-noir": TemplateDef(
        "compare-noir",
        "compare",
        "hue=s=0,eq=contrast=1.25:brightness=-0.04,gblur=sigma=0.45,vignette=PI/5,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#ffffff@0.22:t=3",
    ),
    "relation-panel": TemplateDef(
        "relation-panel",
        "relation",
        "pad={w}:{h}:{frame}:{frame}:#1a1a21,eq=saturation=1.08:contrast=1.08,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#90b4ff@0.35:t=4",
    ),
    "relation-neon": TemplateDef(
        "relation-neon",
        "relation",
        "pad={w}:{h}:{frame}:{frame}:#03060c,eq=saturation=1.4:contrast=1.2,"
        "drawgrid=w=70:h=70:t=1:c=#00ffd0@0.1,drawbox=x=0:y=0:w=iw:h=ih:color=#00ffd0@0.45:t=5",
    ),
    "relation-blueprint": TemplateDef(
        "relation-blueprint",
        "relation",
        "pad={w}:{h}:{frame}:{frame}:#0b1e3f,"
        "colorchannelmixer=rr=0.10:rg=0.12:rb=0.30:gr=0.12:gg=0.50:gb=0.75:br=0.35:bg=0.55:bb=1.00,"
        "eq=saturation=0.8:contrast=1.12,drawgrid=w=84:h=84:t=1:c=#9fd0ff@0.16,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#9fd0ff@0.45:t=5",
    ),
    "relation-noir": TemplateDef(
        "relation-noir",
        "relation",
        "pad={w}:{h}:{frame}:{frame}:#151515,hue=s=0,eq=contrast=1.22:brightness=-0.03,"
        "vignette=PI/6,drawbox=x=0:y=0:w=iw:h=ih:color=#e6e6e6@0.28:t=4",
    ),
    "relation-sunset": TemplateDef(
        "relation-sunset",
        "relation",
        "pad={w}:{h}:{frame}:{frame}:#24121a,colorbalance=rs=.15:gs=-.03:bs=-.10,"
        "eq=saturation=1.26:contrast=1.08,vignette=PI/7,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#ffb06a@0.35:t=4",
    ),
    "split-quad": TemplateDef("split-quad", "split"),
    "split-vertical": TemplateDef("split-vertical", "split"),
    "split-triple": TemplateDef("split-triple", "split"),
    "split-focus": TemplateDef("split-focus", "split"),
    "split-matrix": TemplateDef("split-matrix", "split"),
}

for omarchy_name, palette in OMARCHY_PALETTES.items():
    TEMPLATES[omarchy_name] = TemplateDef(
        omarchy_name,
        "core",
        build_omarchy_filter(
            background=palette["background"],
            accent=palette["accent"],
            alt=palette["alt"],
        ),
    )


def is_compare(name: str) -> bool:
    return TEMPLATES[name].kind == "compare"


def is_split(name: str) -> bool:
    return TEMPLATES[name].kind == "split"


def is_relation(name: str) -> bool:
    return TEMPLATES[name].kind == "relation"
