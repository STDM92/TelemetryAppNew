from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"


class SessionSummary(BaseModel):
    session_key: str
    status: SessionStatus
    producer_attached: bool = False
    engineer_count: int = 0
    latest_snapshot_received_at: datetime | None = None
    latest_snapshot_type: str | None = None
    latest_snapshot_keys: list[str] = Field(default_factory=list)


class CreateSessionResponse(SessionSummary):
    pass


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]
    count: int


class SessionStateView(BaseModel):
    session: SessionSummary
    latest_snapshot: dict[str, Any] | None = None
