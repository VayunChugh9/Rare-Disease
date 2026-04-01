"""FastAPI application entry point for RefTriage."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router
from backend.app.database import init_db

app = FastAPI(
    title="RefTriage",
    description="AI-powered clinical referral triage and summary system",
    version="0.1.0",
)

# CORS — allow frontend dev server and any configured production origin
_allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]
_prod_origin = os.getenv("FRONTEND_URL")
if _prod_origin:
    _allowed_origins.append(_prod_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve frontend static build in production (if dist exists)
_static_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _static_dir.is_dir():
    from starlette.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = _static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_static_dir / "index.html")

    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
