from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/runtime", tags=["runtime"])


@router.get("/status")
def get_runtime_status(request: Request) -> dict:
    registry = request.app.state.session_registry
    hub = request.app.state.connection_hub
    sessions = registry.get_session_summaries()

    active_sessions = [
        session for session in sessions if session.producer_attached or session.engineer_count > 0
    ]

    return {
        "state": "running",
        "mode": "server",
        "last_error": None,
        "session_count": len(sessions),
        "active_session_count": len(active_sessions),
        "connection_count": hub.get_total_connection_count(),
    }
