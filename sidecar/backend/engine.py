import argparse
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from sidecar.backend.runtime import DriverBackendRuntime
from sidecar.backend.websocket import WebSocketConnectionManager
from sidecar.logging_config import configure_logging
from sidecar.telemetry.adapter_contracts import SelectedTelemetrySource
from sidecar.telemetry.adapter_registry import build_available_adapters
from sidecar.telemetry.adapter_selection import select_live_adapter
from sidecar.telemetry.contracts import TelemetryReceiver
from sidecar.telemetry.modes import RuntimeMode, SourceKind, StartupRequest


class StartupArgumentError(ValueError):
    pass


class StartupArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise StartupArgumentError(message)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if message:
            self._print_message(message, sys.stderr)
        raise SystemExit(status)


logger = logging.getLogger(__name__)

runtime: DriverBackendRuntime | None = None
manager = WebSocketConnectionManager()


def _port_argument(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--port must be an integer.") from exc

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("--port must be between 1 and 65535.")

    return port


def parse_startup_args(argv: list[str] | None = None) -> StartupRequest:
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

    return StartupRequest(
        mode=RuntimeMode(args.mode),
        port=args.port,
        file_path=Path(file_path) if file_path is not None else None,
    )


def build_runtime_source(
    request: StartupRequest,
) -> tuple[TelemetryReceiver, SelectedTelemetrySource]:
    adapters = build_available_adapters()

    if request.mode is RuntimeMode.LIVE:
        selection = select_live_adapter(request, adapters)
        adapter = next(a for a in adapters if a.adapter_id == selection.adapter_id)
        return adapter.build_live_source(request), selection.source

    if request.mode in {RuntimeMode.ANALYZE, RuntimeMode.REPLAY}:
        if request.file_path is None:
            raise RuntimeError(f"{request.mode.value} mode requires a file_path.")

        if not adapters:
            raise RuntimeError("No telemetry adapters are registered.")

        # Keep file-based modes intentionally simple for now.
        # Replay stays minimally invasive so it can be removed later
        # without reshaping the live adapter architecture.
        # For now, reuse the first registered adapter's file path support.
        # For now, use the first registered adapter because the current
        # implementation is still effectively iRacing-only for file-based modes.
        adapter = adapters[0]
        source_kind = (
            SourceKind.REPLAY_FILE
            if request.mode is RuntimeMode.REPLAY
            else SourceKind.FILE
        )
        selected_source = SelectedTelemetrySource(
            sim_kind=adapter.sim_kind,
            display_name=adapter.display_name,
            mode=request.mode,
            source_kind=source_kind,
            file_path=request.file_path,
        )
        return adapter.build_file_source(request, request.file_path), selected_source

    raise RuntimeError(f"Unsupported mode: {request.mode.value}")


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

        request = parse_startup_args(argv)
        logger.info(
            "Starting backend engine (mode=%s, port=%s, file=%s).",
            request.mode.value,
            request.port,
            str(request.file_path) if request.file_path is not None else None,
        )

        telemetry_source, selected_source = build_runtime_source(request)
        logger.info(
            "Telemetry source initialized. sim=%s mode=%s source_kind=%s source=%s",
            selected_source.display_name,
            selected_source.mode.value,
            selected_source.source_kind.value,
            type(telemetry_source).__name__,
        )

        global runtime
        runtime = DriverBackendRuntime(
            telemetry_source=telemetry_source,
            publish_callback=manager.broadcast,
            active_source=selected_source,
        )

        logger.info("Launching HTTP server on port %s.", request.port)
        uvicorn.run(app, host="0.0.0.0", port=request.port, log_config=None)
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