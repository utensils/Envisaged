from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .cli import RenderConfig, render
from .templates import TEMPLATES

OutputResolution = Literal["2160p", "1440p", "1080p", "720p"]
SyncMode = Literal["auto", "true", "false", "smart"]

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "web_templates"
WEB_OUTPUT_DIR = Path.home() / ".openclaw" / "workspace" / "out" / "web"
WEB_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Envisaged Web")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/videos", StaticFiles(directory=str(WEB_OUTPUT_DIR)), name="videos")


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


def _render_in_background(job_id: str, config: RenderConfig) -> None:
    try:
        render(config)
        _update_job(job_id, status="done")
    except Exception as exc:
        _update_job(job_id, status="error", error=str(exc))


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "templates": sorted(TEMPLATES.keys()),
            "jobs": _jobs_snapshot(),
            "default_multi_dir": "/tmp/envisaged-compare-src",
        },
    )


@app.post("/render", response_class=HTMLResponse)
def create_render(
    request: Request,
    mode: str = Form("multi"),
    repo: str = Form("."),
    multi_dir: str = Form("/tmp/envisaged-compare-src"),
    title: str = Form("Envisaged Render"),
    template: str = Form("split-quad"),
    resolution: OutputResolution = Form("720p"),
    fps: int = Form(30),
    sync_timing: SyncMode = Form("auto"),
) -> HTMLResponse:
    job_id = uuid4().hex[:8]
    output_name = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{job_id}.mp4"
    output_path = WEB_OUTPUT_DIR / output_name

    cfg = RenderConfig(
        output=output_path,
        resolution=resolution,
        fps=fps,
        title=title,
        template=template,
        logo=None,
        multi_dir=Path(multi_dir).expanduser() if mode == "multi" else None,
        input_repo=repo if mode == "single" else None,
        sync_timing=sync_timing,
        sync_span=31536000,
        seconds_per_day=0.12,
        time_scale=1.6,
        user_scale=1.35,
        auto_skip=0.5,
        crf=22,
        preset="medium",
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

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "templates": sorted(TEMPLATES.keys()),
            "jobs": _jobs_snapshot(),
            "default_multi_dir": multi_dir,
            "message": f"Render started: {output_name}",
        },
    )


def main() -> None:
    uvicorn.run("envisaged.web:app", host="0.0.0.0", port=8787, reload=False)
