from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from .templates import DEFAULT_TEMPLATE, TEMPLATES, is_compare, is_relation, is_split

app = typer.Typer(add_completion=False, rich_markup_mode="rich")
console = Console()

Resolution = Literal["2160p", "1440p", "1080p", "720p"]
SyncMode = Literal["auto", "true", "false", "smart"]
LegendMode = Literal["auto", "none", "repos", "files", "actions", "all"]

RESOLUTION_MAP: dict[str, tuple[int, int]] = {
    "2160p": (3840, 2160),
    "1440p": (2560, 1440),
    "1080p": (1920, 1080),
    "720p": (1280, 720),
}

ALLOWED_FPS = {25, 30, 60}


@dataclass
class RenderConfig:
    output: Path
    resolution: Resolution
    fps: int
    title: str
    template: str
    logo: str | None
    multi_dir: Path | None
    input_repo: str | None
    sync_timing: SyncMode
    sync_span: int
    legend: LegendMode
    legend_limit: int
    seconds_per_day: float
    time_scale: float
    user_scale: float
    auto_skip: float
    crf: int
    preset: str


def require_bin(name: str) -> None:
    if shutil.which(name) is None:
        raise typer.BadParameter(f"Required binary not found in PATH: {name}")


def run(cmd: list[str], *, cwd: Path | None = None, stdout=None) -> None:
    subprocess.run(cmd, check=True, cwd=cwd, stdout=stdout)


def sh(cmd: str, *, cwd: Path | None = None) -> str:
    proc = subprocess.run(["bash", "-lc", cmd], check=True, capture_output=True, text=True, cwd=cwd)
    return proc.stdout.strip()


def ffmpeg_escape(text: str) -> str:
    value = text
    for a, b in [
        ("\\", "\\\\"),
        (":", "\\:"),
        (",", "\\,"),
        ("'", "\\\\'"),
        ("[", "\\["),
        ("]", "\\]"),
        ("%", "\\%"),
    ]:
        value = value.replace(a, b)
    return value


def normalize_log_timestamps(in_log: Path, out_log: Path, sync_span: int) -> None:
    cmd = (
        f"min=$(awk -F'|' 'NR==1{{m=$1}} $1<m{{m=$1}} END{{print m+0}}' {in_log});"
        f"max=$(awk -F'|' 'NR==1{{m=$1}} $1>m{{m=$1}} END{{print m+0}}' {in_log});"
        f"awk -F'|' -v OFS='|' -v min=\"$min\" -v max=\"$max\" -v target={sync_span} -v base=946684800 "
        f"'{{span=max-min; if(span<=0)span=1; t=int(((($1-min)/span)*target)+base); print t,$2,$3,$4;}}' {in_log} > {out_log}"
    )
    sh(cmd)


def inject_sync_blanks(in_log: Path, out_log: Path, sync_span: int, repo_name: str) -> None:
    start_ts = int(sh(f"awk -F'|' 'NR==1{{m=$1}} $1<m{{m=$1}} END{{print m+0}}' {in_log}"))
    end_ts = int(sh(f"awk -F'|' 'NR==1{{m=$1}} $1>m{{m=$1}} END{{print m+0}}' {in_log}"))

    interval = max(sync_span // 8, 1)
    tmp = out_log.with_suffix(".tmp")
    shutil.copy(in_log, tmp)
    with tmp.open("a", encoding="utf-8") as fh:
        fh.write(f"{start_ts}|_sync_|M|/{repo_name}/.sync/anchor\n")
        fh.write(f"{end_ts}|_sync_|M|/{repo_name}/.sync/anchor\n")
        t = start_ts + interval
        while t < end_ts:
            fh.write(f"{t}|_sync_|M|/{repo_name}/.sync/pulse\n")
            t += interval

    sh(f"sort -n {tmp} > {out_log}")
    tmp.unlink(missing_ok=True)


def build_relationship_lines(repo_names: list[str], max_rel: int = 8) -> list[str]:
    lines = ["RELATIONSHIPS", ""]
    count = 0

    for i in range(len(repo_names)):
        for j in range(i + 1, len(repo_names)):
            a = repo_names[i]
            b = repo_names[j]
            abase = a.removesuffix("-nix")
            bbase = b.removesuffix("-nix")

            if abase in bbase or bbase in abase:
                lines.append(f"- {a} <-> {b} (variant line)")
                count += 1
            else:
                shared = ""
                for tok in abase.split("-"):
                    if len(tok) >= 4 and tok in bbase:
                        shared = tok
                        break
                if shared:
                    lines.append(f"- {a} <-> {b} (shared: {shared})")
                    count += 1

            if count >= max_rel:
                return lines

    if count == 0:
        lines.append("- Similar stack family inferred from naming and cadence")

    return lines


def gource_log(repo_dir: Path, out_log: Path) -> None:
    run(["gource", "--output-custom-log", str(out_log), str(repo_dir)], stdout=subprocess.DEVNULL)


def _extension_label(path_text: str) -> str:
    name = Path(path_text).name
    if name.startswith(".") and name.count(".") == 1:
        return name.lower()
    suffix = Path(name).suffix.lower()
    return suffix if suffix else "[no-ext]"


def summarize_log_for_legend(log_path: Path, *, limit: int) -> tuple[list[str], list[str]]:
    ext_counts: dict[str, int] = {}
    action_counts: dict[str, int] = {"A": 0, "M": 0, "D": 0}

    with log_path.open("r", encoding="utf-8", errors="ignore") as fh:
        for raw in fh:
            parts = raw.rstrip("\n").split("|", 3)
            if len(parts) != 4:
                continue
            action = parts[2].strip().upper() or "?"
            path_text = parts[3].strip()

            action_counts[action] = action_counts.get(action, 0) + 1
            ext = _extension_label(path_text)
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

    top_ext = sorted(ext_counts.items(), key=lambda kv: (-kv[1], kv[0]))[: max(1, limit)]
    ext_lines = [f"- {ext}: {count}" for ext, count in top_ext]

    action_map = {"A": "added", "M": "modified", "D": "deleted"}
    action_lines = [
        f"- {action_map.get(key, key)}: {count}"
        for key, count in sorted(action_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if count > 0
    ]

    return ext_lines, action_lines


def build_multi_logs(
    base_dir: Path,
    log_dir: Path,
    sync_timing: SyncMode,
    sync_span: int,
) -> tuple[list[str], list[Path], Path]:
    repo_names: list[str] = []
    repo_logs: list[Path] = []

    for d in sorted(base_dir.iterdir()):
        if not (d / ".git").is_dir():
            continue

        name = d.name
        console.print(f"Collecting: [cyan]{name}[/cyan]")
        raw = log_dir / f"{name}.raw.log"
        prepared = log_dir / f"{name}.log"
        gource_log(d, raw)

        if sync_timing in {"true", "smart"}:
            normalize_log_timestamps(raw, prepared, sync_span)
            if sync_timing == "smart":
                smart = log_dir / f"{name}.smart.log"
                inject_sync_blanks(prepared, smart, sync_span, name)
                prepared = smart
        else:
            shutil.copy(raw, prepared)

        prefixed = log_dir / f"{name}.prefixed.log"
        sh(
            "sed -E 's#^([0-9]+\\|[^|]+\\|[^|]+\\|)#\\1/{name}#' {inp} > {out}".format(
                name=name, inp=prepared, out=prefixed
            )
        )

        repo_names.append(name)
        repo_logs.append(prefixed)

    if not repo_logs:
        raise typer.BadParameter(f"No git repos found in {base_dir}")

    merged = log_dir / "development.log"
    cat_cmd = "cat {files} | sort -n > {out}".format(
        files=" ".join(str(p) for p in repo_logs),
        out=merged,
    )
    sh(cat_cmd)
    return repo_names, repo_logs, merged


def clone_or_use_repo(src: str, workdir: Path) -> Path:
    if src.startswith("http://") or src.startswith("https://") or src.startswith("git@"):
        repo = workdir / "repo"
        console.print(f"Cloning [cyan]{src}[/cyan]")
        run(["git", "clone", "--quiet", src, str(repo)])
        return repo

    repo = Path(src).expanduser().resolve()
    if not (repo / ".git").is_dir():
        raise typer.BadParameter(f"Not a git repository: {repo}")
    return repo


def frame_for_template(template: str) -> int:
    if (
        template in {"border", "neon", "blueprint", "urandom"}
        or is_compare(template)
        or is_split(template)
        or is_relation(template)
    ):
        return 26
    return 0


def split_filter(template: str, quad_multi: bool) -> str:
    if template == "split-quad":
        if quad_multi:
            return (
                "[0:v]scale=iw/2:ih/2,eq=saturation=1.25:contrast=1.1[a1];"
                "[1:v]scale=iw/2:ih/2,hue=s=0,eq=contrast=1.2[b1];"
                "[2:v]scale=iw/2:ih/2,colorbalance=rs=.12:gs=-.02:bs=-.08[c1];"
                "[3:v]scale=iw/2:ih/2,colorchannelmixer=rr=0:rg=0:rb=0:gr=0.2:gg=1.0:gb=0.05:br=0:bg=0:bb=0[d1];"
                "[a1][b1][c1][d1]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[outv]"
            )
        return (
            "[0:v]split=4[a][b][c][d];"
            "[a]scale=iw/2:ih/2,eq=saturation=1.25:contrast=1.1[a1];"
            "[b]scale=iw/2:ih/2,hue=s=0,eq=contrast=1.2[b1];"
            "[c]scale=iw/2:ih/2,colorbalance=rs=.12:gs=-.02:bs=-.08[c1];"
            "[d]scale=iw/2:ih/2,colorchannelmixer=rr=0:rg=0:rb=0:gr=0.2:gg=1.0:gb=0.05:br=0:bg=0:bb=0[d1];"
            "[a1][b1][c1][d1]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[outv]"
        )

    if template == "split-vertical":
        return (
            "[0:v]split=2[a][b];"
            "[a]eq=saturation=1.3:contrast=1.12[a1];"
            "[b]hue=s=0,eq=contrast=1.25[b1];"
            "[a1][b1]hstack=inputs=2[outv]"
        )

    if template == "split-triple":
        return (
            "[0:v]split=3[a][b][c];"
            "[a]crop=iw/2:ih:0:0,eq=saturation=1.22:contrast=1.08[a1];"
            "[b]crop=iw/4:ih:iw/4:0,hue=s=0,eq=contrast=1.2[b1];"
            "[c]crop=iw/4:ih:3*iw/4:0,colorchannelmixer=rr=0:rg=0:rb=0:gr=0.18:gg=1.0:gb=0.05:br=0:bg=0:bb=0[c1];"
            "[a1][b1][c1]hstack=inputs=3[outv]"
        )

    if template == "split-focus":
        return (
            "[0:v]split=2[a][b];"
            "[a]scale=iw:ih,eq=saturation=1.18:contrast=1.1,drawbox=x=8:y=8:w=iw-16:h=ih-16:color=#87b7ff@0.35:t=3[base];"
            "[b]scale=iw/3:ih/3,hue=s=0,eq=contrast=1.24[mini];"
            "[base][mini]overlay=W-w-28:28[outv]"
        )

    if template == "split-matrix":
        return (
            "[0:v]split=4[a][b][c][d];"
            "[a]scale=iw/2:ih/2,colorchannelmixer=rr=0:rg=0:rb=0:gr=0.2:gg=1.0:gb=0.05:br=0:bg=0:bb=0[a1];"
            "[b]scale=iw/2:ih/2,colorchannelmixer=rr=0:rg=0:rb=0:gr=0.15:gg=0.9:gb=0.03:br=0:bg=0:bb=0[b1];"
            "[c]scale=iw/2:ih/2,colorchannelmixer=rr=0:rg=0:rb=0:gr=0.22:gg=1.05:gb=0.07:br=0:bg=0:bb=0[c1];"
            "[d]scale=iw/2:ih/2,colorchannelmixer=rr=0:rg=0:rb=0:gr=0.18:gg=0.95:gb=0.05:br=0:bg=0:bb=0[d1];"
            "[a1][b1][c1][d1]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0,drawgrid=w=64:h=28:t=1:c=#00ff66@0.12[outv]"
        )

    raise RuntimeError(f"Unhandled split template: {template}")


def overlay_lines_filter(
    *,
    box_x: int,
    box_y: int,
    box_w: int,
    box_h: int,
    border_color: str,
    lines: list[str],
    font_size: int,
    line_spacing: int,
    text_x: int,
    text_y: int,
) -> str:
    filt = (
        f"drawbox=x={box_x}:y={box_y}:w={box_w}:h={box_h}:color=#000000@0.42:t=fill,"
        f"drawbox=x={box_x}:y={box_y}:w={box_w}:h={box_h}:color={border_color}:t=2"
    )
    y = text_y
    for line in lines:
        if line:
            esc = ffmpeg_escape(line)
            filt += (
                f",drawtext=font='DejaVu Sans':text='{esc}':x={text_x}:y={y}:"
                f"fontsize={font_size}:fontcolor=white:text_shaping=0"
            )
        y += font_size + line_spacing
    return filt


def render(config: RenderConfig) -> None:
    for bin_name in ["git", "gource", "ffmpeg", "xvfb-run", "bash"]:
        require_bin(bin_name)

    width, height = RESOLUTION_MAP[config.resolution]
    if config.fps not in ALLOWED_FPS:
        raise typer.BadParameter("Unsupported fps (supported: 25, 30, 60)")

    if config.template not in TEMPLATES:
        raise typer.BadParameter(f"Unsupported template: {config.template}")

    is_compare_template = is_compare(config.template)
    is_split_template = is_split(config.template)
    is_relation_template = is_relation(config.template)

    sync_timing = config.sync_timing
    if sync_timing == "auto":
        if config.multi_dir and (is_compare_template or is_split_template or is_relation_template):
            sync_timing = "smart"
        else:
            sync_timing = "false"

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        log_dir = workdir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        repo_names: list[str] = []
        repo_logs: list[Path] = []

        if config.multi_dir:
            repo_names, repo_logs, devlog = build_multi_logs(
                config.multi_dir, log_dir, sync_timing, config.sync_span
            )
        else:
            repo = clone_or_use_repo(config.input_repo or "", workdir)
            devlog = workdir / "development.log"
            gource_log(repo, devlog)

        frame = frame_for_template(config.template)
        inner_w = width - (frame * 2)
        inner_h = height - (frame * 2)

        use_quad_multi = (
            config.template == "split-quad" and config.multi_dir is not None and len(repo_logs) >= 4
        )
        quad_repo_names = repo_names[:4] if use_quad_multi else []
        if use_quad_multi:
            repo_names = quad_repo_names

        base_filter = ""
        use_complex = False
        complex_filter = ""
        final_label = ""

        if is_split_template:
            use_complex = True
            complex_filter = split_filter(config.template, use_quad_multi)
            final_label = "outv"
        else:
            simple = TEMPLATES[config.template].simple_filter or ""
            base_filter = simple.format(w=width, h=height, frame=frame)

        resolved_legend = config.legend
        if resolved_legend == "auto":
            if is_compare_template or is_split_template or is_relation_template:
                resolved_legend = "repos"
            else:
                resolved_legend = "none"

        legend_lines: list[str] = []
        if resolved_legend in {"repos", "all"} and repo_names:
            legend_lines += ["REPOS", "", *[f"- {r}" for r in repo_names]]
            if sync_timing in {"true", "smart"}:
                legend_lines += ["", "timing: unified"]
                if sync_timing == "smart":
                    legend_lines += ["sync: smart blank-log pulses"]

        include_file_legend = resolved_legend in {"files", "all"}
        include_action_legend = resolved_legend in {"actions", "all"}
        if include_file_legend or include_action_legend:
            ext_lines, action_lines = summarize_log_for_legend(devlog, limit=config.legend_limit)
            if include_file_legend:
                if legend_lines:
                    legend_lines += [""]
                legend_lines += ["FILE TYPES", "", *ext_lines]
            if include_action_legend:
                if legend_lines:
                    legend_lines += [""]
                legend_lines += ["ACTIONS", "", *action_lines]

        if legend_lines:
            font = 24 if height >= 1080 else 18
            spacing = 10 if height >= 1080 else 8
            max_chars = max(len(x) for x in legend_lines) if legend_lines else 0
            box_w = max(360, min(width - 36, 90 + (max_chars * (font // 2 + 4))))
            box_h = min(height - 36, 24 + (len(legend_lines) * (font + spacing)) + 24)
            legend_filter = overlay_lines_filter(
                box_x=18,
                box_y=18,
                box_w=box_w,
                box_h=box_h,
                border_color="#d8e7ff@0.24",
                lines=legend_lines,
                font_size=font,
                line_spacing=spacing,
                text_x=34,
                text_y=34,
            )

            if use_complex:
                complex_filter = f"{complex_filter};[{final_label}]{legend_filter}[outleg]"
                final_label = "outleg"
            else:
                base_filter = f"{base_filter},{legend_filter}" if base_filter else legend_filter

        if is_relation_template and len(repo_names) > 1:
            lines = build_relationship_lines(repo_names)
            font = 20 if height >= 1080 else 16
            spacing = 8 if height >= 1080 else 6
            max_chars = max(len(x) for x in lines) if lines else 0
            box_w = max(420, min(width - 36, 90 + (max_chars * (font // 2 + 4))))
            box_h = min(height - 36, 24 + (len(lines) * (font + spacing)) + 24)
            box_x = width - box_w - 18
            rel_filter = overlay_lines_filter(
                box_x=box_x,
                box_y=18,
                box_w=box_w,
                box_h=box_h,
                border_color="#ffd28a@0.24",
                lines=lines,
                font_size=font,
                line_spacing=spacing,
                text_x=box_x + 18,
                text_y=36,
            )

            if use_complex:
                complex_filter = f"{complex_filter};[{final_label}]{rel_filter}[outrel]"
                final_label = "outrel"
            else:
                base_filter = f"{base_filter},{rel_filter}" if base_filter else rel_filter

        logo_file: Path | None = None
        if config.logo:
            if config.logo.startswith("http://") or config.logo.startswith("https://"):
                logo_file = workdir / "logo"
                run(["curl", "-fsSL", config.logo, "-o", str(logo_file)])
            else:
                logo_file = Path(config.logo).expanduser().resolve()
                if not logo_file.exists():
                    raise typer.BadParameter(f"Logo not found: {logo_file}")

        base_input_count = 4 if use_quad_multi else 1
        if logo_file:
            logo_idx = base_input_count
            if use_complex:
                complex_filter = (
                    f"{complex_filter};[{logo_idx}:v]scale=-1:{height}/8[logo];"
                    f"[{final_label}][logo]overlay=W-w-40:H-h-40[outlogo]"
                )
                final_label = "outlogo"
            else:
                use_complex = True
                if base_filter:
                    complex_filter = (
                        f"[0:v]{base_filter}[base];[{logo_idx}:v]scale=-1:{height}/8[logo];"
                        "[base][logo]overlay=W-w-40:H-h-40[outlogo]"
                    )
                else:
                    complex_filter = f"[{logo_idx}:v]scale=-1:{height}/8[logo];[0:v][logo]overlay=W-w-40:H-h-40[outlogo]"
                final_label = "outlogo"

        console.print(f"Rendering: [green]{config.output}[/green]")
        console.print(
            f"Resolution: {width}x{height} ({config.resolution}), fps={config.fps}, "
            f"template={config.template}, sync={sync_timing}"
        )

        if use_quad_multi:
            console.print(f"Quad mode: using 4 distinct repos ({' '.join(quad_repo_names)})")
            tmp_videos: list[Path] = []
            for i in range(4):
                qv = workdir / f"quad-src-{i}.mp4"
                tmp_videos.append(qv)

                gource_cmd = (
                    "SDL_VIDEODRIVER=x11 xvfb-run -a -s '-screen 0 {w}x{h}x24' gource "
                    "--seconds-per-day {spd} --user-scale {us} --time-scale {ts} --auto-skip-seconds {as_} "
                    "--title '{title} — {repo}' --background-colour 000000 --font-colour FFFFFF "
                    "--camera-mode overview --hide usernames,mouse,date,filenames --font-size 42 "
                    "--dir-name-depth 3 --filename-time 2 --max-user-speed 500 --bloom-multiplier 1.2 "
                    "--{iw}x{ih} --stop-at-end '{log}' -r {fps} -o -"
                ).format(
                    w=width,
                    h=height,
                    spd=config.seconds_per_day,
                    us=config.user_scale,
                    ts=config.time_scale,
                    as_=config.auto_skip,
                    title=config.title,
                    repo=quad_repo_names[i],
                    iw=inner_w,
                    ih=inner_h,
                    log=repo_logs[i],
                    fps=config.fps,
                )
                ffmpeg_cmd = (
                    "ffmpeg -y -r {fps} -f image2pipe -probesize 100M -i - "
                    "-vcodec libx264 -pix_fmt yuv420p -crf {crf} -preset {preset} -bf 0 '{out}'"
                ).format(fps=config.fps, crf=config.crf, preset=config.preset, out=qv)
                sh(f"{gource_cmd} | {ffmpeg_cmd}")

            cmd = ["ffmpeg", "-y"]
            for qv in tmp_videos:
                cmd += ["-i", str(qv)]
            if logo_file:
                cmd += ["-i", str(logo_file)]
            cmd += [
                "-filter_complex",
                complex_filter,
                "-map",
                f"[{final_label or 'outv'}]",
                "-vcodec",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                str(config.crf),
                "-preset",
                config.preset,
                "-bf",
                "0",
                str(config.output),
            ]
            run(cmd)
        else:
            pipe = workdir / "gource.pipe"
            run(["mkfifo", str(pipe)])
            gource_cmd = (
                "SDL_VIDEODRIVER=x11 xvfb-run -a -s '-screen 0 {w}x{h}x24' gource "
                "--seconds-per-day {spd} --user-scale {us} --time-scale {ts} --auto-skip-seconds {as_} "
                "--title '{title}' --background-colour 000000 --font-colour FFFFFF --camera-mode overview "
                "--hide usernames,mouse,date,filenames --font-size 42 --dir-name-depth 3 --filename-time 2 "
                "--max-user-speed 500 --bloom-multiplier 1.2 --{iw}x{ih} --stop-at-end '{log}' -r {fps} -o - > '{pipe}'"
            ).format(
                w=width,
                h=height,
                spd=config.seconds_per_day,
                us=config.user_scale,
                ts=config.time_scale,
                as_=config.auto_skip,
                title=config.title,
                iw=inner_w,
                ih=inner_h,
                log=devlog,
                fps=config.fps,
                pipe=pipe,
            )
            gource_proc = subprocess.Popen(["bash", "-lc", gource_cmd])

            try:
                if use_complex:
                    cmd = [
                        "ffmpeg",
                        "-y",
                        "-r",
                        str(config.fps),
                        "-f",
                        "image2pipe",
                        "-probesize",
                        "100M",
                        "-i",
                        str(pipe),
                    ]
                    if logo_file:
                        cmd += ["-i", str(logo_file)]
                    cmd += [
                        "-filter_complex",
                        complex_filter,
                        "-map",
                        f"[{final_label or 'outv'}]",
                        "-vcodec",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        "-crf",
                        str(config.crf),
                        "-preset",
                        config.preset,
                        "-bf",
                        "0",
                        str(config.output),
                    ]
                else:
                    cmd = [
                        "ffmpeg",
                        "-y",
                        "-r",
                        str(config.fps),
                        "-f",
                        "image2pipe",
                        "-probesize",
                        "100M",
                        "-i",
                        str(pipe),
                    ]
                    if base_filter:
                        cmd += ["-vf", base_filter]
                    cmd += [
                        "-vcodec",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        "-crf",
                        str(config.crf),
                        "-preset",
                        config.preset,
                        "-bf",
                        "0",
                        str(config.output),
                    ]
                run(cmd)
            finally:
                gource_proc.wait()

        console.print(f"[bold green]Done:[/bold green] {config.output}")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def cli(
    repo: str | None = typer.Argument(None, help="Repo path or git URL"),
    output: Path = typer.Option(Path("output.mp4"), "--output", "-o"),
    resolution: Resolution = typer.Option("1080p", "--resolution", "-r"),
    fps: int = typer.Option(60, "--fps", "-f"),
    title: str = typer.Option("Software Development", "--title", "-t"),
    template: str = typer.Option(DEFAULT_TEMPLATE, "--template"),
    logo: str | None = typer.Option(None, "--logo"),
    multi_dir: Path | None = typer.Option(None, "--multi-dir"),
    sync_timing: SyncMode = typer.Option("auto", "--sync-timing"),
    sync_span: int = typer.Option(31536000, "--sync-span"),
    legend: LegendMode = typer.Option("auto", "--legend"),
    legend_limit: int = typer.Option(8, "--legend-limit"),
    seconds_per_day: float = typer.Option(0.12, "--seconds-per-day"),
    time_scale: float = typer.Option(1.6, "--time-scale"),
    user_scale: float = typer.Option(1.35, "--user-scale"),
    auto_skip: float = typer.Option(0.5, "--auto-skip"),
    crf: int = typer.Option(22, "--crf"),
    preset: str = typer.Option("medium", "--preset"),
) -> None:
    """Render Git history videos with Gource + FFmpeg."""
    if multi_dir and repo:
        raise typer.BadParameter("Use either <repo> or --multi-dir, not both")
    if not multi_dir and not repo:
        raise typer.BadParameter("Provide either a repo input or --multi-dir")
    if template not in TEMPLATES:
        raise typer.BadParameter(f"Unsupported template: {template}")
    if legend_limit < 1:
        raise typer.BadParameter("--legend-limit must be >= 1")

    cfg = RenderConfig(
        output=output,
        resolution=resolution,
        fps=fps,
        title=title,
        template=template,
        logo=logo,
        multi_dir=multi_dir,
        input_repo=repo,
        sync_timing=sync_timing,
        sync_span=sync_span,
        legend=legend,
        legend_limit=legend_limit,
        seconds_per_day=seconds_per_day,
        time_scale=time_scale,
        user_scale=user_scale,
        auto_skip=auto_skip,
        crf=crf,
        preset=preset,
    )
    render(cfg)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
