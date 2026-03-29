import asyncio
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from telemetry.administrator import TelemetryStateAdministrator
from telemetry.receivers.iracing_receiver import IRacingReceiver

administrator = TelemetryStateAdministrator()
receiver = IRacingReceiver()
current_snapshot_dict = None


# --- Manage Multiple Viewers ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


# --- The 60Hz Loop ---
async def telemetry_loop():
    global current_snapshot_dict
    print("Backend Engine Started. Waiting for Simulator...")

    while True:
        snapshot = receiver.capture_snapshot()
        if snapshot is not None:
            administrator.apply_snapshot(snapshot)
            current_snapshot_dict = asdict(administrator.get_latest_snapshot())

            # Instantly push the data to anyone watching!
            if current_snapshot_dict and manager.active_connections:
                await manager.broadcast(current_snapshot_dict)

        await asyncio.sleep(1 / 60)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    background_task = asyncio.create_task(telemetry_loop())
    yield
    background_task.cancel()
    print("Backend Engine cleanly shut down.")


app = FastAPI(lifespan=lifespan)


# --- The WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)