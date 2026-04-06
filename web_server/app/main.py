from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.health import router as health_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.proposals import router as proposals_router
from app.api.routes.runtime import router as runtime_router
from app.api.routes.state import router as state_router
from app.api.routes.ws import router as ws_router
from app.core.connection_hub import ConnectionHub
from app.core.session_registry import SessionRegistry

app = FastAPI(title="Telemetry Web Server", version="0.1.0")

app.state.session_registry = SessionRegistry()
app.state.connection_hub = ConnectionHub()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(runtime_router)
app.include_router(state_router)
app.include_router(sessions_router)
app.include_router(proposals_router)
app.include_router(ws_router)

FRONTEND_DIST_DIR = Path(__file__).resolve().parents[1] / "frontend" / "dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"

if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="frontend-assets")


def _resolve_frontend_file(path_fragment: str) -> Path | None:
    if not FRONTEND_DIST_DIR.exists():
        return None

    normalized = path_fragment.lstrip("/")
    if not normalized:
        candidate = FRONTEND_DIST_DIR / "index.html"
        return candidate if candidate.exists() else None

    candidate = (FRONTEND_DIST_DIR / normalized).resolve()
    try:
        candidate.relative_to(FRONTEND_DIST_DIR.resolve())
    except ValueError:
        return None

    if candidate.is_file():
        return candidate

    index_file = FRONTEND_DIST_DIR / "index.html"
    return index_file if index_file.exists() else None


@app.get("/", include_in_schema=False)
def serve_frontend_index() -> FileResponse:
    file_path = _resolve_frontend_file("")
    if file_path is None:
        raise HTTPException(status_code=404, detail="Frontend build not found.")
    return FileResponse(file_path)


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend_app(full_path: str) -> FileResponse:
    if full_path == "ws" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found.")

    file_path = _resolve_frontend_file(full_path)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Frontend build not found.")
    return FileResponse(file_path)
