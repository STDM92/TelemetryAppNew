import logging
from fastapi import WebSocket


logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected. active_connections=%s", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected. active_connections=%s", len(self.active_connections))

    async def broadcast(self, data: dict) -> None:
        disconnected: list[WebSocket] = []

        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                logger.warning("WebSocket broadcast failed. Marking connection for removal.", exc_info=True)
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)
