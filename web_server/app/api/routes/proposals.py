from fastapi import APIRouter

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
