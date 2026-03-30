import argparse
import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.runtime import RacerBackendRuntime
from backend.websocket import WebSocketConnectionManager
from telemetry.sims.iracing.iracing_receiver import IRacingReceiver
from telemetry.sims.iracing.iracing_reader import IRacingReader

runtime: RacerBackendRuntime | None = None
manager = WebSocketConnectionManager()

# Adjust this path to wherever your frontend files live.
# Example:
# backend/
#   engine.py
# frontend/
#   index.html
#   hud.js
#   telemetry-types.js
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if not FRONTEND_DIR.exists():
    raise RuntimeError(f"Frontend directory does not exist: {FRONTEND_DIR}")


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    if runtime is None:
        raise RuntimeError("Backend runtime has not been configured.")

    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop()
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
    if runtime is None:
        return {"status": "not_configured"}

    return runtime.get_status()


@app.get("/api/state")
def get_current_state():
    if runtime is None:
        return None
    return runtime.get_current_state()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telemetry Backend Engine")
    parser.add_argument(
        "--mode",
        choices=["live", "replay", "analyze"],
        default="live",
        help="Operating mode",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to the telemetry file (required for replay/analyze)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the API on",
    )

    args = parser.parse_args()
    run_mode = args.mode

    if run_mode in ["replay", "analyze"]:
        if not args.file:
            print("Error: --file argument is required when running in replay or analyze mode.")
            sys.exit(1)
        active_parser = IRacingReader(args.file)
    else:
        active_parser = IRacingReceiver()

    try:
        runtime = RacerBackendRuntime(
            telemetry_source=active_parser,
            publish_callback=manager.broadcast,
        )

        uvicorn.run(app, host="0.0.0.0", port=args.port)
    except Exception as exc:
        print(f"Backend startup failed: {exc}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
