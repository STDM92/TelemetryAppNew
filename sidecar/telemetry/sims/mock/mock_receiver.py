from __future__ import annotations

import asyncio
import json
import logging
import threading
from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin, get_type_hints

from websockets import connect

from sidecar.telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot


logger = logging.getLogger(__name__)


def _resolve_dataclass_type(annotation):
    origin = get_origin(annotation)

    if origin is None:
        if isinstance(annotation, type) and is_dataclass(annotation):
            return annotation
        return None

    if origin in (list, dict, tuple, set):
        return None

    for arg in get_args(annotation):
        if arg is type(None):
            continue
        if isinstance(arg, type) and is_dataclass(arg):
            return arg

    return None


def _from_dict(dataclass_type, data):
    if not is_dataclass(dataclass_type):
        return data

    if not isinstance(data, dict):
        return data

    type_hints = get_type_hints(dataclass_type)
    kwargs = {}

    for field_info in fields(dataclass_type):
        field_name = field_info.name
        if field_name not in data:
            continue

        value = data[field_name]
        annotation = type_hints.get(field_name, field_info.type)
        nested_type = _resolve_dataclass_type(annotation)

        if nested_type is not None and isinstance(value, dict):
            kwargs[field_name] = _from_dict(nested_type, value)
        else:
            kwargs[field_name] = value

    return dataclass_type(**kwargs)


class MockSimReceiver:
    def __init__(self, base_url: str = "http://127.0.0.1:8766"):
        self._base_url = base_url.rstrip("/")
        self._stream_url = (
            self._base_url.replace("http://", "ws://", 1)
            .replace("https://", "wss://", 1)
            + "/stream"
        )

        self._lock = threading.Lock()
        self._latest_payload: dict[str, Any] | None = None
        self._latest_sequence: int | None = None
        self._last_emitted_sequence: int | None = None

        self._worker_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._started = False

    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        self._ensure_started()

        with self._lock:
            if self._latest_payload is None:
                return None

            if self._latest_sequence == self._last_emitted_sequence:
                return None

            self._last_emitted_sequence = self._latest_sequence
            payload = self._latest_payload

        return _from_dict(UnifiedTelemetrySnapshot, payload)

    def close(self) -> None:
        self._stop_event.set()
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

    def _ensure_started(self) -> None:
        if self._started:
            return

        self._worker_thread = threading.Thread(
            target=self._run_worker_thread,
            name="mock-sim-receiver",
            daemon=True,
        )
        self._worker_thread.start()
        self._started = True
        logger.info("Started mock sim receiver thread. stream_url=%s", self._stream_url)

    def _run_worker_thread(self) -> None:
        try:
            asyncio.run(self._run_worker_async())
        except Exception:
            logger.exception("Mock sim receiver worker thread crashed.")

    async def _run_worker_async(self) -> None:
        while not self._stop_event.is_set():
            try:
                logger.info("Connecting to mock sim stream. stream_url=%s", self._stream_url)
                async with connect(self._stream_url, open_timeout=5) as websocket:
                    logger.info("Connected to mock sim stream.")
                    while not self._stop_event.is_set():
                        raw_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        message = json.loads(raw_message)

                        if message.get("type") != "telemetry_frame":
                            continue

                        payload = message.get("payload")
                        sequence = message.get("sequence")

                        if not isinstance(payload, dict):
                            continue
                        if not isinstance(sequence, int):
                            continue

                        with self._lock:
                            self._latest_payload = payload
                            self._latest_sequence = sequence

            except asyncio.TimeoutError:
                logger.warning("Timed out waiting for mock sim frame. Retrying connection.")
            except Exception:
                logger.exception("Mock sim receiver stream loop failed. Retrying in 1 second.")

            if self._stop_event.wait(1.0):
                return