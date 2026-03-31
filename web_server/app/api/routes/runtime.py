from fastapi import APIRouter

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
