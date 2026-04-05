from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket

from app.models.messages import WebSocketRole


class ConnectionHub:
    def __init__(self) -> None:
        self._connections: dict[str, dict[WebSocketRole, set[WebSocket]]] = defaultdict(
            lambda: {
                WebSocketRole.PRODUCER: set(),
                WebSocketRole.ENGINEER: set(),
            }
        )

    def register(self, session_key: str, role: WebSocketRole, websocket: WebSocket) -> None:
        self._connections[session_key][role].add(websocket)

    def unregister(self, session_key: str, role: WebSocketRole, websocket: WebSocket) -> None:
        role_map = self._connections.get(session_key)
        if role_map is None:
            return

        role_map[role].discard(websocket)
        if not role_map[WebSocketRole.PRODUCER] and not role_map[WebSocketRole.ENGINEER]:
            self._connections.pop(session_key, None)

    def get_connection_counts(self, session_key: str) -> dict[str, int]:
        role_map = self._connections.get(session_key)
        if role_map is None:
            return {
                WebSocketRole.PRODUCER.value: 0,
                WebSocketRole.ENGINEER.value: 0,
            }

        return {
            WebSocketRole.PRODUCER.value: len(role_map[WebSocketRole.PRODUCER]),
            WebSocketRole.ENGINEER.value: len(role_map[WebSocketRole.ENGINEER]),
        }

    def get_total_connection_count(self) -> int:
        total = 0
        for role_map in self._connections.values():
            total += len(role_map[WebSocketRole.PRODUCER])
            total += len(role_map[WebSocketRole.ENGINEER])
        return total

    async def broadcast_to_engineers(self, session_key: str, message: dict) -> None:
        role_map = self._connections.get(session_key)
        if role_map is None:
            return

        stale_connections: list[WebSocket] = []
        for websocket in tuple(role_map[WebSocketRole.ENGINEER]):
            try:
                await websocket.send_json(message)
            except Exception:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            role_map[WebSocketRole.ENGINEER].discard(websocket)

        if not role_map[WebSocketRole.PRODUCER] and not role_map[WebSocketRole.ENGINEER]:
            self._connections.pop(session_key, None)
