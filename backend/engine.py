import asyncio
import argparse
import sys
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from telemetry.administrator import TelemetryStateAdministrator
from telemetry.sims.iracing.iracing_receiver import IRacingReceiver
from telemetry.sims.iracing.iracing_reader import IRacingReader

administrator = TelemetryStateAdministrator()
current_snapshot_dict = None
active_parser = None
run_mode = "replay"


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

# Adjust this path to wherever your frontend files live.
# Example:
# backend/
#   engine.py
# frontend/
#   index.html
#   hud.js
#   telemetry-types.js
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

if not FRONTEND_DIR.exists():
    raise RuntimeError(f"Frontend directory does not exist: {FRONTEND_DIR}")


async def telemetry_loop():
    global current_snapshot_dict

    while True:
        snapshot = active_parser.capture_snapshot()

        if snapshot is not None:
            administrator.apply_snapshot(snapshot)
            current_snapshot_dict = asdict(administrator.get_latest_snapshot())

            if current_snapshot_dict and manager.active_connections:
                await manager.broadcast(current_snapshot_dict)

        await asyncio.sleep(1 / 60)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    background_task = asyncio.create_task(telemetry_loop())
    try:
        yield
    finally:
        background_task.cancel()
        print("Backend Engine cleanly shut down.")


app = FastAPI(lifespan=lifespan)

# Serve JS/CSS/static assets from /static
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def get_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/state")
def get_current_state():
    return current_snapshot_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telemetry Backend Engine")
    parser.add_argument("--mode", choices=["live", "replay", "analyze"], default="live", help="Operating mode")
    parser.add_argument("--file", type=str, help="Path to the telemetry file (required for replay/analyze)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the API on")

    args = parser.parse_args()
    run_mode = args.mode

    if run_mode in ["replay", "analyze"]:
        if not args.file:
            print("Error: --file argument is required when running in replay or analyze mode.")
            sys.exit(1)
        active_parser = IRacingReader(args.file)
    else:
        active_parser = IRacingReceiver()

    uvicorn.run(app, host="0.0.0.0", port=args.port)