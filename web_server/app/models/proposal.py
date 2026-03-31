from pydantic import BaseModel

class Proposal(BaseModel):
    proposal_id: str
    kind: str
    status: str
