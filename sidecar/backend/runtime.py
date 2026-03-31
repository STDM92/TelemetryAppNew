import asyncio
from dataclasses import asdict
from typing import Awaitable, Callable

from sidecar.telemetry.administrator import TelemetryStateAdministrator
from sidecar.telemetry.contracts import TelemetryReceiver


class DriverBackendRuntime:
    def __init__(
        self,
        telemetry_source: TelemetryReceiver,
        publish_callback: Callable[[dict], Awaitable[None]] | None = None,
        tick_hz: float = 60,
    ):
        self._telemetry_source = telemetry_source
        self._publish_callback = publish_callback
        self._tick_seconds = 1 / tick_hz

        self._administrator = TelemetryStateAdministrator()
        self._current_snapshot_dict: dict | None = None
        self._background_task: asyncio.Task | None = None
        self._status = "created"
        self._last_error: str | None = None

    async def start(self) -> None:
        if self._background_task is not None and not self._background_task.done():
            return

        self._background_task = asyncio.create_task(self._telemetry_loop())
        self._background_task.add_done_callback(self._on_background_task_done)
        self._status = "running"
        self._last_error = None

    async def stop(self) -> None:
        if self._background_task is None:
            self._status = "stopped"
            return

        task = self._background_task
        self._background_task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self._background_task = None
            if self._status != "failed":
                self._status = "stopped"

    def get_current_state(self) -> dict | None:
        return self._current_snapshot_dict

    def get_status(self) -> dict:
        return {
            "status": self._status,
            "last_error": self._last_error,
        }

    def _on_background_task_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return

        try:
            task.result()
        except Exception:
            self._status = "failed"
    async def _telemetry_loop(self) -> None:
        while True:
            try:
                snapshot = self._telemetry_source.capture_snapshot()
            except Exception as e:
                raise

            if snapshot is not None:
                self._administrator.apply_snapshot(snapshot)
                self._current_snapshot_dict = asdict(self._administrator.get_latest_snapshot())

                if self._current_snapshot_dict and self._publish_callback is not None:
                    await self._publish_callback(self._current_snapshot_dict)

            await asyncio.sleep(self._tick_seconds)
