from fastapi import APIRouter

router = APIRouter(prefix="/api/state", tags=["state"])

@router.get("")
def get_state() -> dict:
    return {
        "session": None,
        "telemetry": None,
        "updated_at": None,
    }
