"""FastAPI app — HF Spaces entrypoint."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.core.device import DevicePool
from app.core.message import render
from app.core.sender import NGLSender
from app.models.job import Job
from app.models.result import Result


app = FastAPI(
    title="NGL Test Suite (HF Spaces)",
    version="1.0.0-hf",
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


class SendRequest(BaseModel):
    """Payload untuk /api/send."""

    usernames: list[str] = Field(..., min_length=1, max_length=50)
    messages: list[str] = Field(..., min_length=1, max_length=50)
    count_per_user: int = Field(default=1, ge=1, le=20)
    max_retry: int = Field(default=2, ge=0, le=4)
    device_strategy: str = Field(default="pool")
    dry_run: bool = Field(default=False)
    timeout: float = Field(default=10.0, ge=1.0, le=30.0)
    concurrency: int = Field(default=10, ge=1, le=30)


class SendOneRequest(BaseModel):
    """Payload untuk /api/send-one."""

    username: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    dry_run: bool = Field(default=True)


MAX_JOBS_PER_REQUEST = 50


async def _send_one_job(
    sender: NGLSender,
    job: Job,
    max_retry: int,
    dry_run: bool,
) -> Result:
    """Kirim satu job dengan retry inline."""
    last_result: Result | None = None

    for attempt in range(max_retry + 1):
        try:
            job.increment_attempt()
            result = await sender.send(job, dry_run=dry_run)
            last_result = result

            if result.success:
                return result

            if result.status_code in (429, 500, 502, 503, 504):
                if attempt < max_retry:
                    await asyncio.sleep(min(2 ** attempt, 4))
                    continue
            return result
        except Exception as e:  # noqa: BLE001
            if attempt < max_retry:
                await asyncio.sleep(min(2 ** attempt, 4))
                continue
            return Result(
                job_id=job.id,
                username=job.username,
                message=job.message,
                status_code=0,
                success=False,
                latency_ms=0.0,
                error=str(e),
                attempts=job.attempts,
            )

    return last_result or Result(
        job_id=job.id,
        username=job.username,
        message=job.message,
        status_code=0,
        success=False,
        latency_ms=0.0,
        error="exhausted",
        attempts=job.attempts,
    )


@app.get("/api/health")
async def health() -> dict[str, Any]:
    """Health check."""
    return {
        "status": "ok",
        "version": "1.0.0-hf",
        "runtime": "huggingface-spaces",
    }


@app.post("/api/send")
async def send_batch(req: SendRequest) -> dict[str, Any]:
    """Kirim satu batch pesan ke NGL."""
    start = time.perf_counter()

    device_pool = DevicePool(
        strategy=req.device_strategy,  # type: ignore[arg-type]
    )

    jobs: list[Job] = []
    for i in range(req.count_per_user):
        for username in req.usernames:
            msg_template = req.messages[i % len(req.messages)]
            message = render(
                msg_template,
                index=len(jobs) + 1,
                username=username,
            )
            jobs.append(
                Job(
                    username=username,
                    message=message,
                    device_id=device_pool.next(),
                )
            )

    if len(jobs) > MAX_JOBS_PER_REQUEST:
        jobs = jobs[:MAX_JOBS_PER_REQUEST]

    if not jobs:
        raise HTTPException(status_code=400, detail="No jobs generated")

    semaphore = asyncio.Semaphore(req.concurrency)

    async def bounded_send(job: Job) -> Result:
        async with semaphore:
            return await _send_one_job(
                sender, job, req.max_retry, req.dry_run
            )

    async with NGLSender(timeout=req.timeout) as sender:
        results = await asyncio.gather(*[bounded_send(j) for j in jobs])

    elapsed = (time.perf_counter() - start) * 1000
    success_count = sum(1 for r in results if r.success)

    return {
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "success_rate": round(
            success_count / len(results) * 100 if results else 0, 2
        ),
        "elapsed_ms": round(elapsed, 1),
        "results": [r.to_dict() for r in results],
    }


@app.post("/api/send-one")
async def send_one(req: SendOneRequest) -> dict[str, Any]:
    """Kirim satu pesan saja — untuk testing."""
    batch_req = SendRequest(
        usernames=[req.username],
        messages=[req.message],
        count_per_user=1,
        max_retry=2,
        dry_run=req.dry_run,
    )
    return await send_batch(batch_req)


@app.get("/api")
async def api_root() -> dict[str, str]:
    """API root."""
    return {
        "name": "NGL Test Suite",
        "version": "1.0.0-hf",
        "docs": "/api/docs",
        "disclaimer": (
            "For educational testing only. "
            "Unauthorized spam violates NGL ToS."
        ),
    }


if STATIC_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve dashboard HTML."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            "<h1>NGL Test Suite</h1>"
            "<p>Frontend not found. API available at "
            "<a href='/api/docs'>/api/docs</a></p>"
        )
    return HTMLResponse(index_path.read_text(encoding="utf-8"))