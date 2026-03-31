from fastapi import APIRouter
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
