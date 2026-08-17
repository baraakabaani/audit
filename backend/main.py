"""
Audit Automation System — FastAPI entry point.

DISCLAIMER: AI-generated classifications, calculations, and draft reporting outputs
are subject to auditor review and approval. The system does not replace professional
judgment or the auditor's responsibility for the financial statements or audit opinion.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes import router
from backend.models.database import init_db

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

app = FastAPI(
    title="Audit Automation System",
    description=(
        "Professional audit and financial statement preparation system. "
        "AI-assisted account classification with mandatory auditor review and approval."
    ),
    version="1.0.0",
    # Only expose docs on localhost
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Serve React frontend (built files) ───────────────────────────────────────
if FRONTEND_DIST.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str, request: Request):
        # Don't intercept /api routes
        if full_path.startswith("api/") or full_path.startswith("health"):
            return {"error": "not found"}
        # For any other path, serve the SPA (React handles routing)
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "system": "Audit Automation System",
            "note": "Frontend not built. Run: cd frontend && npm run build",
        }
