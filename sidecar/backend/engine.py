import argparse
import sys
import traceback
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from sidecar.backend.runtime import DriverBackendRuntime
from sidecar.backend.websocket import WebSocketConnectionManager
from sidecar.telemetry.sims.iracing.iracing_receiver import IRacingReceiver
from sidecar.telemetry.sims.iracing.iracing_reader import IRacingReader


@dataclass(frozen=True)
class StartupConfig:
    mode: str
    file: str | None
    port: int


def _port_argument(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--port must be an integer.") from exc

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("--port must be between 1 and 65535.")

    return port


def parse_startup_args(argv: list[str] | None = None) -> StartupConfig:
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
        type=_port_argument,
        default=8000,
        help="Port to run the API on",
    )

    args = parser.parse_args(argv)
    file_path = args.file.strip() if isinstance(args.file, str) else None
    file_path = file_path or None

    if args.mode in {"replay", "analyze"}:
        if file_path is None:
            parser.error("--file is required when --mode is replay or analyze.")

        candidate = Path(file_path)
        if not candidate.is_file():
            parser.error(f"--file does not point to a readable file: {file_path}")

        file_path = str(candidate)
    elif file_path is not None:
        parser.error("--file is only valid when --mode is replay or analyze.")

    return StartupConfig(mode=args.mode, file=file_path, port=args.port)


def build_telemetry_source(config: StartupConfig):
    if config.mode in {"replay", "analyze"}:
        return IRacingReader(config.file)
    return IRacingReceiver()

runtime: DriverBackendRuntime | None = None
manager = WebSocketConnectionManager()


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

@app.get("/status")
def get_current_state():
    if runtime is None:
        return {"status": "not_configured"}
    return runtime.get_status()


def main(argv: list[str] | None = None) -> int:
    try:
        config = parse_startup_args(argv)
        active_parser = build_telemetry_source(config)

        global runtime
        runtime = DriverBackendRuntime(
            telemetry_source=active_parser,
            publish_callback=manager.broadcast,
        )

        uvicorn.run(app, host="0.0.0.0", port=config.port)
        return 0
    except Exception as exc:
        print(f"Backend startup failed: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())