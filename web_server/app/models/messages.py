from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class WebSocketRole(str, Enum):
    PRODUCER = "producer"
    ENGINEER = "engineer"


class WebSocketMessageType(str, Enum):
    TELEMETRY_SNAPSHOT = "telemetry_snapshot"
    SERVER_INFO = "server_info"
    SERVER_ERROR = "server_error"


class TelemetrySnapshotMessage(BaseModel):
    type: Literal[WebSocketMessageType.TELEMETRY_SNAPSHOT] = WebSocketMessageType.TELEMETRY_SNAPSHOT
    payload: dict[str, Any]


class ServerInfoMessage(BaseModel):
    type: Literal[WebSocketMessageType.SERVER_INFO] = WebSocketMessageType.SERVER_INFO
    payload: dict[str, Any] = Field(default_factory=dict)


class ServerErrorMessage(BaseModel):
    type: Literal[WebSocketMessageType.SERVER_ERROR] = WebSocketMessageType.SERVER_ERROR
    payload: dict[str, Any] = Field(default_factory=dict)
