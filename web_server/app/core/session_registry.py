from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from secrets import choice
from string import ascii_uppercase, digits
from typing import Any

from app.models.session import SessionStateView, SessionStatus, SessionSummary

SESSION_KEY_LENGTH = 8
SESSION_KEY_ALPHABET = ascii_uppercase + digits


@dataclass(slots=True)
class SessionRecord:
    session_key: str
    created_at: datetime
    producer_attached: bool = False
    engineer_count: int = 0
    latest_snapshot: dict[str, Any] | None = None
    latest_snapshot_received_at: datetime | None = None
    latest_snapshot_type: str | None = None
    latest_snapshot_keys: list[str] = field(default_factory=list)


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}

    def create_session(self) -> SessionRecord:
        session_key = self._generate_session_key()
        record = SessionRecord(
            session_key=session_key,
            created_at=datetime.now(timezone.utc),
        )
        self._sessions[session_key] = record
        return record

    def get_session(self, session_key: str) -> SessionRecord | None:
        return self._sessions.get(session_key.upper())

    def list_sessions(self) -> list[SessionRecord]:
        return list(self._sessions.values())

    def set_producer_attached(self, session_key: str, attached: bool) -> SessionRecord | None:
        record = self.get_session(session_key)
        if record is None:
            return None
        record.producer_attached = attached
        return record

    def set_engineer_count(self, session_key: str, engineer_count: int) -> SessionRecord | None:
        record = self.get_session(session_key)
        if record is None:
            return None
        record.engineer_count = max(0, engineer_count)
        return record

    def record_snapshot(self, session_key: str, snapshot: dict[str, Any], message_type: str) -> SessionRecord | None:
        record = self.get_session(session_key)
        if record is None:
            return None
        record.latest_snapshot = snapshot
        record.latest_snapshot_received_at = datetime.now(timezone.utc)
        record.latest_snapshot_type = message_type
        record.latest_snapshot_keys = sorted(snapshot.keys()) if isinstance(snapshot, dict) else []
        return record

    def get_session_state_view(self, session_key: str) -> SessionStateView | None:
        record = self.get_session(session_key)
        if record is None:
            return None
        return SessionStateView(
            session=self._to_summary(record),
            latest_snapshot=record.latest_snapshot,
        )

    def get_session_summary(self, session_key: str) -> SessionSummary | None:
        record = self.get_session(session_key)
        if record is None:
            return None
        return self._to_summary(record)

    def get_session_summaries(self) -> list[SessionSummary]:
        return [self._to_summary(record) for record in self.list_sessions()]

    def _to_summary(self, record: SessionRecord) -> SessionSummary:
        status = SessionStatus.ACTIVE if record.producer_attached or record.engineer_count > 0 else SessionStatus.CREATED
        return SessionSummary(
            session_key=record.session_key,
            status=status,
            producer_attached=record.producer_attached,
            engineer_count=record.engineer_count,
            latest_snapshot_received_at=record.latest_snapshot_received_at,
            latest_snapshot_type=record.latest_snapshot_type,
            latest_snapshot_keys=record.latest_snapshot_keys,
        )

    def _generate_session_key(self) -> str:
        while True:
            candidate = "".join(choice(SESSION_KEY_ALPHABET) for _ in range(SESSION_KEY_LENGTH))
            if candidate not in self._sessions:
                return candidate
