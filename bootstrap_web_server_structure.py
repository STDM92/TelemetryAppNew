#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

FILES = {
    "web_server/.gitignore": ".__pycache__/\n.venv/\n*.pyc\n",
    "web_server/README.md": """# Web Server

Minimal FastAPI-based LAN session/web server for the telemetry product.

Responsibilities in this first bootstrap:
- serve the engineer-facing web app later
- host a simple session relay API
- accept sidecar uplink connections later
- accept engineer browser connections later

Not responsible for:
- sim parsing
- telemetry authority
- driver-local process ownership
""",
    "web_server/requirements.txt": """fastapi>=0.115
uvicorn[standard]>=0.30
""",
    "web_server/app/__init__.py": "",
    "web_server/app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.proposals import router as proposals_router
from app.api.routes.runtime import router as runtime_router
from app.api.routes.state import router as state_router
from app.api.routes.ws import router as ws_router

app = FastAPI(title="Telemetry Web Server", version="0.1.0")

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
""",
    "web_server/app/api/__init__.py": "",
    "web_server/app/api/routes/__init__.py": "",
    "web_server/app/api/routes/health.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def get_health() -> dict:
    return {
        "status": "running",
        "service": "web_server",
        "last_error": None,
    }
""",
    "web_server/app/api/routes/runtime.py": """from fastapi import APIRouter

router = APIRouter(prefix="/api/runtime", tags=["runtime"])

@router.get("/status")
def get_runtime_status() -> dict:
    return {
        "state": "starting",
        "mode": "server",
        "source": None,
        "connected_to_sim": False,
        "session_attached": False,
        "last_error": None,
    }
""",
    "web_server/app/api/routes/state.py": """from fastapi import APIRouter

router = APIRouter(prefix="/api/state", tags=["state"])

@router.get("")
def get_state() -> dict:
    return {
        "session": None,
        "telemetry": None,
        "updated_at": None,
    }
""",
    "web_server/app/api/routes/sessions.py": """from fastapi import APIRouter
from uuid import uuid4

router = APIRouter(prefix="/api/session", tags=["session"])

@router.post("/create")
def create_session() -> dict:
    session_key = uuid4().hex[:8].upper()
    return {
        "session_key": session_key,
        "status": "created",
        "engineer_attached": False,
    }

@router.get("")
def get_session() -> dict:
    return {
        "session_key": None,
        "status": "not_connected",
        "engineer_attached": False,
    }

@router.post("/disconnect")
def disconnect_session() -> dict:
    return {
        "status": "disconnected",
    }
""",
    "web_server/app/api/routes/proposals.py": """from fastapi import APIRouter

router = APIRouter(prefix="/api/proposals", tags=["proposals"])

@router.get("/current")
def get_current_proposal() -> dict:
    return {
        "proposal": None,
    }

@router.post("/{proposal_id}/accept")
def accept_proposal(proposal_id: str) -> dict:
    return {
        "proposal_id": proposal_id,
        "status": "accepted",
    }

@router.post("/{proposal_id}/reject")
def reject_proposal(proposal_id: str) -> dict:
    return {
        "proposal_id": proposal_id,
        "status": "rejected",
    }
""",
    "web_server/app/api/routes/ws.py": """from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["ws"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
""",
    "web_server/app/core/__init__.py": "",
    "web_server/app/core/config.py": """from pydantic import BaseModel

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
""",
    "web_server/app/core/session_registry.py": """class SessionRegistry:
    # In-memory placeholder session registry for the first LAN prototype.

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}
""",
    "web_server/app/core/connection_hub.py": """class ConnectionHub:
    # Placeholder for future sidecar/engineer websocket connection tracking.

    def __init__(self) -> None:
        self._connections: dict[str, list] = {}
""",
    "web_server/app/models/__init__.py": "",
    "web_server/app/models/session.py": """from pydantic import BaseModel

class SessionInfo(BaseModel):
    session_key: str
    status: str
    engineer_attached: bool = False
""",
    "web_server/app/models/proposal.py": """from pydantic import BaseModel

class Proposal(BaseModel):
    proposal_id: str
    kind: str
    status: str
""",
    "web_server/app/models/messages.py": """from pydantic import BaseModel
from typing import Any

class EventMessage(BaseModel):
    type: str
    payload: Any
""",
    "web_server/run_dev.py": """import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
""",
    "web_server/tests/__init__.py": "",
    "web_server/tests/test_health_smoke.py": """from fastapi.testclient import TestClient

from app.main import app

def test_health_smoke() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "running"
""",
    "web_server/frontend/.gitkeep": "",
}

def write_file(path: Path, content: str, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        print(f"SKIP  {path} (already exists)")
        return
    path.write_text(content, encoding="utf-8")
    print(f"WRITE {path}")

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bootstrap web_server structure.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repo root. Defaults to current directory.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing bootstrap-created files.")
    return parser.parse_args(argv)

def main(argv=None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()

    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 1

    for relative_path, content in FILES.items():
        write_file(root / relative_path, content, force=args.force)

    print("\nDone.")
    print(f"Repo root: {root}")
    print("Next steps:")
    print("  1. Create and activate a virtual environment inside web_server/ if you want isolation.")
    print("  2. pip install -r web_server/requirements.txt")
    print("  3. Start the dev server with: python web_server/run_dev.py")
    print("  4. Open http://<LAN-IP>:8080/health from another device on the network.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
