from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateDef:
    name: str
    kind: str  # core | compare | split | relation
    simple_filter: str | None = None


DEFAULT_TEMPLATE = "urandom"


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


def is_compare(name: str) -> bool:
    return TEMPLATES[name].kind == "compare"


def is_split(name: str) -> bool:
    return TEMPLATES[name].kind == "split"


def is_relation(name: str) -> bool:
    return TEMPLATES[name].kind == "relation"
