from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def get_health() -> dict:
    return {
        "status": "running",
        "service": "web_server",
        "last_error": None,
    }
