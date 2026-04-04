import argparse
import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from live_telemetry_sidecar.backend.runtime import DriverBackendRuntime
from live_telemetry_sidecar.backend.websocket import WebSocketConnectionManager
from live_telemetry_sidecar.logging_config import configure_logging
from live_telemetry_sidecar.telemetry.adapter_contracts import SelectedTelemetrySource
from live_telemetry_sidecar.telemetry.adapter_registry import build_available_adapters
from live_telemetry_sidecar.telemetry.telemetry_source_manager import TelemetrySourceManager
from live_telemetry_sidecar.telemetry.modes import SimKind, SourceKind, StartupRequest


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
    parser = StartupArgumentParser(description="Telemetry Live Backend")
    parser.add_argument(
        "--port",
        type=_port_argument,
        default=8000,
        help="Port to run the API on",
    )

    args = parser.parse_args(argv)

    return StartupRequest(port=args.port)


def configure_framework_logging() -> None:
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


def _runtime_status_payload() -> dict:
    if runtime is None:
        return {"status": "not_configured"}

    return runtime.get_status()


@app.get("/health")
def health():
    return _runtime_status_payload()


@app.get("/status")
def get_current_status():
    return _runtime_status_payload()


@app.get("/api/state")
def get_current_state():
    if runtime is None:
        return None
    return runtime.get_current_state()





def main(argv: list[str] | None = None) -> int:
    try:
        log_file = configure_logging()
        configure_framework_logging()
        logger.info("Configured logging. log_file=%s", log_file)

        request = parse_startup_args(argv)
        logger.info(
            "Starting live backend (port=%s).",
            request.port,
        )

        adapters = build_available_adapters()
        waiting_source = SelectedTelemetrySource(
            sim_kind=SimKind.UNKNOWN,
            display_name="Waiting for simulator",
            source_kind=SourceKind.UNKNOWN,
        )
        telemetry_source = TelemetrySourceManager(
            request=request,
            adapters=adapters,
        )

        logger.info(
            "Telemetry source initialized. sim=%s source_kind=%s source=%s",
            waiting_source.display_name,
            waiting_source.source_kind.value,
            type(telemetry_source).__name__,
        )

        global runtime
        runtime = DriverBackendRuntime(
            telemetry_source=telemetry_source,
            publish_callback=manager.broadcast,
            active_source=waiting_source,
        )

        telemetry_source.set_on_source_selected(runtime.set_active_source)

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
