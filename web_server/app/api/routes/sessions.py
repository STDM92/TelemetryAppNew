from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.session_registry import SessionRegistry
from app.models.session import CreateSessionResponse, SessionListResponse, SessionSummary

router = APIRouter(prefix="/api/session", tags=["session"])



def _get_registry(request: Request) -> SessionRegistry:
    return request.app.state.session_registry


@router.post("/create", response_model=CreateSessionResponse)
def create_session(request: Request) -> CreateSessionResponse:
    record = _get_registry(request).create_session()
    summary = _get_registry(request).get_session_summary(record.session_key)
    assert summary is not None
    return CreateSessionResponse(**summary.model_dump())


@router.get("/{session_key}", response_model=SessionSummary)
def get_session(session_key: str, request: Request) -> SessionSummary:
    session = _get_registry(request).get_session_summary(session_key)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@router.get("", response_model=SessionListResponse)
def list_sessions(request: Request) -> SessionListResponse:
    sessions = _get_registry(request).get_session_summaries()
    return SessionListResponse(sessions=sessions, count=len(sessions))
