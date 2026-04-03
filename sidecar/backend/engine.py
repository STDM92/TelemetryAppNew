import argparse
import logging
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from sidecar.backend.runtime import DriverBackendRuntime
from sidecar.logging_config import configure_logging
from sidecar.backend.websocket import WebSocketConnectionManager
from sidecar.telemetry.sims.iracing.iracing_receiver import IRacingReceiver
from sidecar.telemetry.sims.iracing.iracing_reader import IRacingReader


class StartupArgumentError(ValueError):
    pass


class StartupArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise StartupArgumentError(message)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if message:
            self._print_message(message, sys.stderr)
        raise SystemExit(status)


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
    parser = StartupArgumentParser(description="Telemetry Backend Engine")
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


logger = logging.getLogger(__name__)


def build_telemetry_source(config: StartupConfig):
    if config.mode in {"replay", "analyze"}:
        return IRacingReader(config.file)
    return IRacingReceiver()


def configure_framework_logging() -> None:
    """Route uvicorn/FastAPI logs through the sidecar's logging configuration."""
    logger_names = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ]

    for logger_name in logger_names:
        framework_logger = logging.getLogger(logger_name)
        framework_logger.handlers.clear()
        framework_logger.propagate = True
        framework_logger.setLevel(logging.INFO)


logger = logging.getLogger(__name__)

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
        logger.info("Backend Engine cleanly shut down.")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def get_current_status():
    if runtime is None:
        return {"status": "not_configured"}

    return runtime.get_status()


def main(argv: list[str] | None = None) -> int:
    try:
        log_file = configure_logging()
        configure_framework_logging()
        logger.info("Configured logging. log_file=%s", log_file)

        config = parse_startup_args(argv)
        logger.info(
            "Starting backend engine (mode=%s, port=%s, file=%s).",
            config.mode,
            config.port,
            config.file,
        )
        active_parser = build_telemetry_source(config)
        logger.info("Telemetry source initialized: %s", type(active_parser).__name__)

        global runtime
        runtime = DriverBackendRuntime(
            telemetry_source=active_parser,
            publish_callback=manager.broadcast,
        )

        logger.info("Launching HTTP server on port %s.", config.port)
        uvicorn.run(app, host="0.0.0.0", port=config.port, log_config=None)
        return 0
    except StartupArgumentError as exc:
        logger.error("Backend startup configuration invalid: %s", exc)
        return 1
    except SystemExit as exc:
        if exc.code not in (0, None):
            logger.error("Backend startup exited during argument parsing. exit_code=%s", exc.code)
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception:
        logger.exception("Backend startup failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())