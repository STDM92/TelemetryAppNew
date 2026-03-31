from pydantic import BaseModel
from typing import Any

class EventMessage(BaseModel):
    type: str
    payload: Any
