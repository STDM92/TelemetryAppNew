from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.session import SessionListResponse, SessionStateView

router = APIRouter(prefix="/api/state", tags=["state"])


@router.get("", response_model=SessionListResponse)
def get_state(request: Request) -> SessionListResponse:
    sessions = request.app.state.session_registry.get_session_summaries()
    return SessionListResponse(sessions=sessions, count=len(sessions))


@router.get("/{session_key}", response_model=SessionStateView)
def get_session_state(session_key: str, request: Request) -> SessionStateView:
    state_view = request.app.state.session_registry.get_session_state_view(session_key)
    if state_view is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return state_view
