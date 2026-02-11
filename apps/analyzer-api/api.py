from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from service import (
    analyze_sample,
    get_audio_root,
    list_samples,
    parse_sample_id_payload,
    resolve_sample_path,
)

from engine.core.errors import EngineError

app = FastAPI(title="BeetsNKeys - Analyzer API", version="v1")

DEFAULT_CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


def _cors_origins_from_env() -> list[str]:
    raw = os.getenv("ANALYZER_CORS_ORIGINS", "")
    if not raw.strip():
        return list(DEFAULT_CORS_ORIGINS)
    origins = [part.strip() for part in raw.split(",") if part.strip()]
    return origins or list(DEFAULT_CORS_ORIGINS)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_from_env(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validation_error(msg: str) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": [{"msg": msg}]})


@app.get("/samples")
def get_samples() -> dict[str, Any]:
    return {"samples": list_samples(get_audio_root())}


@app.post("/analyze")
async def post_analyze(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return _validation_error("Invalid JSON body")

    if not isinstance(payload, dict):
        return _validation_error("JSON body must be an object")

    try:
        role, sample_id = parse_sample_id_payload(payload)
        sample_path = resolve_sample_path(get_audio_root(), sample_id)
    except ValueError as exc:
        if str(exc) == "sample_id not found":
            return JSONResponse(
                status_code=404,
                content={"code": "SAMPLE_NOT_FOUND", "message": "sample_id not found"},
            )
        return _validation_error(str(exc))

    try:
        output = analyze_sample(role=role, sample_path=sample_path)
    except EngineError as exc:
        if exc.code == "UNSUPPORTED_INPUT":
            return JSONResponse(
                status_code=415,
                content={"code": "UNSUPPORTED_FORMAT", "message": exc.message},
            )
        if exc.code == "INVALID_INPUT":
            return _validation_error(exc.message)
        return JSONResponse(status_code=500, content={"code": exc.code, "message": exc.message})

    return JSONResponse(status_code=200, content=output)


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> JSONResponse:
    _ = job_id
    return JSONResponse(
        status_code=404,
        content={"code": "JOBS_NOT_SUPPORTED", "message": "Async jobs not enabled in v1"},
    )
