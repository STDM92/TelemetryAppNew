import asyncio
from dataclasses import asdict
from typing import Awaitable, Callable

from telemetry.administrator import TelemetryStateAdministrator
from telemetry.contracts import TelemetryReceiver


class RacerBackendRuntime:
    def __init__(
        self,
        telemetry_source: TelemetryReceiver,
        publish_callback: Callable[[dict], Awaitable[None]] | None = None,
        tick_hz: float = 60.0,
    ):
        self._telemetry_source = telemetry_source
        self._publish_callback = publish_callback
        self._tick_seconds = 1 / tick_hz

        self._administrator = TelemetryStateAdministrator()
        self._current_snapshot_dict: dict | None = None
        self._background_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._background_task is not None and not self._background_task.done():
            return

        self._background_task = asyncio.create_task(self._telemetry_loop())

    async def stop(self) -> None:
        if self._background_task is None:
            return

        self._background_task.cancel()

        try:
            await self._background_task
        except asyncio.CancelledError:
            pass
        finally:
            self._background_task = None

    def get_current_state(self) -> dict | None:
        return self._current_snapshot_dict

    async def _telemetry_loop(self) -> None:
        while True:
            snapshot = self._telemetry_source.capture_snapshot()

            if snapshot is not None:
                self._administrator.apply_snapshot(snapshot)
                self._current_snapshot_dict = asdict(self._administrator.get_latest_snapshot())

                if self._current_snapshot_dict and self._publish_callback is not None:
                    await self._publish_callback(self._current_snapshot_dict)

            await asyncio.sleep(self._tick_seconds)
