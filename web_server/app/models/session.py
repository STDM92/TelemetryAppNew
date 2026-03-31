from pydantic import BaseModel

class SessionInfo(BaseModel):
    session_key: str
    status: str
    engineer_attached: bool = False
