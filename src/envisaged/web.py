from __future__ import annotations

import hashlib
import json
import re
import subprocess
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .cli import RenderConfig, render
from .templates import DEFAULT_TEMPLATE, TEMPLATES

OutputResolution = Literal["2160p", "1440p", "1080p", "720p"]
SyncMode = Literal["auto", "true", "false", "smart"]
LegendMode = Literal["auto", "none", "repos", "files", "actions", "all"]
SystemLogSource = Literal["journal", "kernel", "auth"]

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "web_templates"
WEB_OUTPUT_DIR = Path.home() / ".openclaw" / "workspace" / "out" / "web"
REPO_CACHE_DIR = Path("/tmp/envisaged-web-repos")
MULTI_REPO_WORK_DIR = Path("/tmp/envisaged-web-multi")

WEB_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MULTI_REPO_WORK_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Envisaged Web")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/videos", StaticFiles(directory=str(WEB_OUTPUT_DIR)), name="videos")


auth_repo_re = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass
class RenderJob:
    id: str
    title: str
    template: str
    status: str
    output_name: str
    created_at: str
    error: str | None = None


_JOBS: list[RenderJob] = []
_LOCK = threading.Lock()


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _add_job(job: RenderJob) -> None:
    with _LOCK:
        _JOBS.insert(0, job)
        del _JOBS[20:]


def _update_job(job_id: str, *, status: str, error: str | None = None) -> None:
    with _LOCK:
        for job in _JOBS:
            if job.id == job_id:
                job.status = status
                job.error = error
                return


def _jobs_snapshot() -> list[RenderJob]:
    with _LOCK:
        return [RenderJob(**job.__dict__) for job in _JOBS]


def _repo_owner_name(repo_input: str) -> tuple[str, str] | None:
    raw = repo_input.strip()

    if auth_repo_re.match(raw):
        owner, name = raw.split("/", 1)
        return owner, name.removesuffix(".git")

    if raw.startswith("git@github.com:"):
        path = raw.split("git@github.com:", 1)[1]
        if "/" in path:
            owner, name = path.split("/", 1)
            return owner, name.removesuffix(".git")

    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urllib.parse.urlparse(raw)
        if parsed.netloc.lower() in {"github.com", "www.github.com"}:
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) >= 2:
                return parts[0], parts[1].removesuffix(".git")

    return None


def _normalize_github_url(repo_input: str) -> str:
    owner_name = _repo_owner_name(repo_input)
    if owner_name is None:
        return repo_input
    owner, name = owner_name
    return f"https://github.com/{owner}/{name}.git"


def _ensure_local_repo(repo_input: str) -> str:
    owner_name = _repo_owner_name(repo_input)
    if owner_name is None:
        return repo_input

    owner, name = owner_name
    local_dir = REPO_CACHE_DIR / f"{owner}__{name}"
    remote_url = _normalize_github_url(repo_input)

    if (local_dir / ".git").is_dir():
        _run(["git", "-C", str(local_dir), "remote", "set-url", "origin", remote_url])
        _run(["git", "-C", str(local_dir), "fetch", "origin", "--prune"])
        _run(["git", "-C", str(local_dir), "pull", "--ff-only"])
    else:
        _run(["git", "clone", remote_url, str(local_dir)])

    return str(local_dir)


def _resolve_repo_to_local(repo_input: str) -> Path:
    raw = repo_input.strip()
    if not raw:
        raise ValueError("Empty repository entry")

    # Local path
    local_path = Path(raw).expanduser()
    if local_path.exists():
        resolved = local_path.resolve()
        if not (resolved / ".git").is_dir():
            raise ValueError(f"Not a git repo: {resolved}")
        return resolved

    # GitHub shorthand/url → cached clone
    owner_name = _repo_owner_name(raw)
    if owner_name is not None:
        return Path(_ensure_local_repo(raw))

    # Generic git URL clone cache
    if raw.startswith("http://") or raw.startswith("https://") or raw.startswith("git@"):
        slug = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        local_dir = REPO_CACHE_DIR / f"remote__{slug}"
        if (local_dir / ".git").is_dir():
            _run(["git", "-C", str(local_dir), "remote", "set-url", "origin", raw])
            _run(["git", "-C", str(local_dir), "fetch", "origin", "--prune"])
            _run(["git", "-C", str(local_dir), "pull", "--ff-only"])
        else:
            _run(["git", "clone", raw, str(local_dir)])
        return local_dir

    raise ValueError(f"Unsupported repository input: {raw}")


def _prepare_multi_repo_dir(job_id: str, repos_text: str, multi_dir: str) -> Path:
    entries = [line.strip() for line in repos_text.splitlines() if line.strip()]

    # Fallback to directory scanning if no explicit list provided.
    if not entries:
        base = Path(multi_dir).expanduser().resolve()
        if not base.is_dir():
            raise ValueError(f"Multi dir does not exist: {base}")
        return base

    job_dir = MULTI_REPO_WORK_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    used_names: set[str] = set()
    for idx, entry in enumerate(entries, start=1):
        repo_path = _resolve_repo_to_local(entry)
        base_name = re.sub(r"[^A-Za-z0-9_.-]", "-", repo_path.name) or f"repo-{idx}"
        name = base_name
        n = 2
        while name in used_names:
            name = f"{base_name}-{n}"
            n += 1
        used_names.add(name)

        link = job_dir / name
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(repo_path, target_is_directory=True)

    return job_dir


def _search_github_repos(query: str, per_page: int = 8) -> list[dict[str, str | int | None]]:
    q = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={per_page}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "envisaged-web",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))

    items: list[dict[str, str | int | None]] = []
    for item in payload.get("items", []):
        items.append(
            {
                "full_name": item.get("full_name"),
                "html_url": item.get("html_url"),
                "description": item.get("description"),
                "stars": item.get("stargazers_count", 0),
            }
        )
    return items


def _render_in_background(job_id: str, config: RenderConfig) -> None:
    try:
        render(config)
        _update_job(job_id, status="done")
    except Exception as exc:
        _update_job(job_id, status="error", error=str(exc))


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    message: str | None = Query(default=None),
    default_multi_repos: str = Query(default=""),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "templates": sorted(TEMPLATES.keys()),
            "default_template": DEFAULT_TEMPLATE,
            "jobs": _jobs_snapshot(),
            "default_multi_dir": "/tmp/envisaged-compare-src",
            "default_multi_repos": default_multi_repos,
            "message": message,
        },
    )


@app.get("/api/github-search", response_class=JSONResponse)
def github_search(q: str = Query(min_length=2, max_length=100)) -> JSONResponse:
    try:
        results = _search_github_repos(q)
        return JSONResponse({"ok": True, "results": results})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc), "results": []}, status_code=502)


@app.post("/render")
def create_render(
    mode: str = Form("single"),
    repo: str = Form("."),
    multi_dir: str = Form("/tmp/envisaged-compare-src"),
    multi_repos: str = Form(""),
    title: str = Form("Envisaged Render"),
    template: str = Form(DEFAULT_TEMPLATE),
    resolution: OutputResolution = Form("720p"),
    fps: int = Form(30),
    sync_timing: SyncMode = Form("auto"),
    legend: LegendMode = Form("auto"),
    legend_limit: int = Form(8),
    system_log: SystemLogSource = Form("journal"),
    system_log_since: str = Form("24 hours ago"),
    system_log_limit: int = Form(5000),
) -> RedirectResponse:
    job_id = uuid4().hex[:8]
    output_name = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{job_id}.mp4"
    output_path = WEB_OUTPUT_DIR / output_name

    try:
        repo_source = repo
        multi_source: Path | None = None
        system_source: SystemLogSource | None = None

        if mode == "single":
            repo_source = str(_resolve_repo_to_local(repo))
        elif mode == "multi":
            multi_source = _prepare_multi_repo_dir(job_id, multi_repos, multi_dir)
        elif mode == "system":
            system_source = system_log
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        cfg = RenderConfig(
            output=output_path,
            resolution=resolution,
            fps=fps,
            title=title,
            template=template,
            logo=None,
            multi_dir=multi_source if mode == "multi" else None,
            input_repo=repo_source if mode == "single" else None,
            system_log=system_source,
            system_log_since=system_log_since,
            system_log_limit=system_log_limit,
            sync_timing=sync_timing,
            sync_span=31536000,
            legend=legend,
            legend_limit=legend_limit,
            seconds_per_day=0.12,
            time_scale=1.6,
            user_scale=1.35,
            auto_skip=0.5,
            crf=22,
            preset="medium",
        )
    except Exception as exc:
        message = urllib.parse.quote(f"Error: {exc}")
        repos_q = urllib.parse.quote(multi_repos)
        return RedirectResponse(
            url=f"/?message={message}&default_multi_repos={repos_q}",
            status_code=303,
        )

    _add_job(
        RenderJob(
            id=job_id,
            title=title,
            template=template,
            status="running",
            output_name=output_name,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    )

    thread = threading.Thread(target=_render_in_background, args=(job_id, cfg), daemon=True)
    thread.start()

    message = urllib.parse.quote(f"Render started: {output_name}")
    repos_q = urllib.parse.quote(multi_repos)
    return RedirectResponse(
        url=f"/?message={message}&default_multi_repos={repos_q}",
        status_code=303,
    )


def main() -> None:
    uvicorn.run("envisaged.web:app", host="0.0.0.0", port=8787, reload=False)
