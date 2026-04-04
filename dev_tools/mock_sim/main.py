from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from dev_tools.mock_sim.models import MockSimConfig, StreamFrame
from dev_tools.mock_sim.replay_source import ReplayFrameSource


logger = logging.getLogger("mock_sim")


class MockSimArgumentError(ValueError):
    pass


class MockSimArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise MockSimArgumentError(message)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if message:
            self._print_message(message, sys.stderr)
        raise SystemExit(status)


class WebSocketFanout:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast_json(self, data: dict) -> None:
        disconnected: list[WebSocket] = []

        for connection in self._connections:
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


class MockSimRuntime:
    def __init__(self, config: MockSimConfig, fanout: WebSocketFanout):
        self._config = config
        self._fanout = fanout
        self._tick_seconds = 1.0 / config.hz
        self._task: asyncio.Task | None = None
        self._status = "created"
        self._last_error: str | None = None
        self._sequence = 0
        self._last_payload: dict | None = None
        self._frames_sent = 0
        self._source = ReplayFrameSource(config.file_path)

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return

        logger.info(
            "Starting mock sim runtime. file=%s hz=%s loop=%s",
            self._config.file_path,
            self._config.hz,
            self._config.loop,
        )
        self._task = asyncio.create_task(self._run())
        self._task.add_done_callback(self._on_done)
        self._status = "running"
        self._last_error = None

    async def stop(self) -> None:
        if self._task is None:
            self._status = "stopped"
            return

        task = self._task
        self._task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            if self._status != "failed":
                self._status = "stopped"

    def get_health(self) -> dict:
        return {"status": "ok"}

    def get_sim_info(self) -> dict:
        return {
            "sim_kind": "mock",
            "display_name": "Mock Sim",
            "source_file": self._config.file_path,
            "is_streaming": self._status == "running",
            "frame_rate_hz": self._config.hz,
            "frames_sent": self._frames_sent,
            "connected_clients": self._fanout.connection_count,
            "last_error": self._last_error,
        }

    def get_status(self) -> dict:
        return {
            "status": self._status,
            "last_error": self._last_error,
            "frames_sent": self._frames_sent,
            "connected_clients": self._fanout.connection_count,
            "last_payload_excerpt": self._build_excerpt(self._last_payload),
        }

    @staticmethod
    def _build_excerpt(payload: dict | None) -> dict | None:
        if not isinstance(payload, dict):
            return None

        return {
            "source": payload.get("source"),
            "session_phase": (payload.get("session") or {}).get("session_phase"),
            "current_lap": (payload.get("lap") or {}).get("current_lap"),
            "speed_kph": (payload.get("powertrain") or {}).get("vehicle_speed_kph"),
            "gear": (payload.get("powertrain") or {}).get("gear"),
        }

    def _on_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return

        try:
            task.result()
        except Exception as exc:
            self._status = "failed"
            self._last_error = str(exc)
            logger.exception("Mock sim runtime failed.")

    async def _run(self) -> None:
        logger.info("Mock sim replay loop started.")

        while True:
            sent_any = False

            for payload in self._source.iter_payloads():
                sent_any = True
                self._sequence += 1
                self._frames_sent += 1
                self._last_payload = payload

                frame = StreamFrame(sequence=self._sequence, payload=payload)
                await self._fanout.broadcast_json(
                    {
                        "type": "telemetry_frame",
                        "sequence": frame.sequence,
                        "payload": frame.payload,
                    }
                )

                await asyncio.sleep(self._tick_seconds)

            logger.info("Mock sim reached end of file.")

            if not self._config.loop:
                logger.info("Mock sim stopping replay because loop=False.")
                return

            logger.info("Mock sim restarting replay because loop=True.")
            self._source = ReplayFrameSource(self._config.file_path)

            if not sent_any:
                raise RuntimeError("Replay source produced no frames.")


def parse_args(argv: list[str] | None = None) -> MockSimConfig:
    parser = MockSimArgumentParser(description="Mock simulator for sidecars live-pipeline testing")
    parser.add_argument("--file", required=True, help="Path to the source .ibt file")
    parser.add_argument("--port", type=int, default=8766, help="Port to run the mock sim on")
    parser.add_argument("--hz", type=float, default=60.0, help="Replay rate in frames per second")
    parser.add_argument("--loop", action="store_true", help="Loop the replay when end of file is reached")

    args = parser.parse_args(argv)

    candidate = Path(args.file)
    if not candidate.is_file():
        raise MockSimArgumentError(f"--file does not point to a readable file: {args.file}")

    if args.port < 1 or args.port > 65535:
        raise MockSimArgumentError("--port must be between 1 and 65535.")

    if args.hz <= 0:
        raise MockSimArgumentError("--hz must be greater than 0.")

    return MockSimConfig(
        file_path=str(candidate),
        port=args.port,
        hz=args.hz,
        loop=args.loop,
    )


def build_app(config: MockSimConfig) -> FastAPI:
    fanout = WebSocketFanout()
    runtime = MockSimRuntime(config, fanout)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await runtime.start()
        try:
            yield
        finally:
            await runtime.stop()
            logger.info("Mock sim cleanly shut down.")

    app = FastAPI(lifespan=lifespan)

    @app.get("/health")
    def health():
        return runtime.get_health()

    @app.get("/sim-info")
    def sim_info():
        return runtime.get_sim_info()

    @app.get("/status")
    def status():
        return runtime.get_status()

    @app.websocket("/stream")
    async def stream(websocket: WebSocket):
        await fanout.connect(websocket)
        logger.info("Mock sim client connected. clients=%s", fanout.connection_count)
        try:
            while True:
                await asyncio.sleep(60)
        except WebSocketDisconnect:
            fanout.disconnect(websocket)
            logger.info("Mock sim client disconnected. clients=%s", fanout.connection_count)
        except Exception:
            fanout.disconnect(websocket)
            logger.exception("Mock sim websocket stream failed.")

    return app


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-8s | %(asctime)s | %(name)s | %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    try:
        configure_logging()
        config = parse_args(argv)
        logger.info(
            "Starting mock sim. file=%s port=%s hz=%s loop=%s",
            config.file_path,
            config.port,
            config.hz,
            config.loop,
        )
        app = build_app(config)
        uvicorn.run(app, host="127.0.0.1", port=config.port, log_config=None)
        return 0
    except MockSimArgumentError as exc:
        logger.error("Mock sim configuration invalid: %s", exc)
        return 1
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception:
        logger.exception("Mock sim failed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())