import asyncio
import logging
from dataclasses import asdict
from typing import Awaitable, Callable

from sidecar.telemetry.administrator import TelemetryStateAdministrator
from sidecar.telemetry.contracts import TelemetryReceiver


logger = logging.getLogger(__name__)


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
            logger.debug("Runtime start requested while background task is already running.")
            return

        logger.info("Starting driver backend runtime.")
        self._background_task = asyncio.create_task(self._telemetry_loop(), name="driver-backend-telemetry-loop")
        self._background_task.add_done_callback(self._on_background_task_done)
        self._status = "running"
        self._last_error = None
        self._has_logged_first_snapshot = False

    async def stop(self) -> None:
        if self._background_task is None:
            self._status = "stopped"
            logger.info("Driver backend runtime stopped (no active task).")
            return

        logger.info("Stopping driver backend runtime.")
        task = self._background_task
        self._background_task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            logger.debug("Driver backend runtime task cancelled during stop.")
        finally:
            self._background_task = None
            if self._status != "failed":
                self._status = "stopped"
            logger.info("Driver backend runtime stopped.")

    def get_current_state(self) -> dict | None:
        return self._current_snapshot_dict

    def get_status(self) -> dict:
        return {
            "status": self._status,
            "last_error": self._last_error,
        }

    def _on_background_task_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            logger.debug("Telemetry loop task completed via cancellation.")
            return

        try:
            task.result()
        except Exception as exc:
            self._status = "failed"
            self._last_error = str(exc)
            logger.exception("Telemetry loop failed.")

    async def _telemetry_loop(self) -> None:
        while True:
            try:
                snapshot = self._telemetry_source.capture_snapshot()
            except Exception:
                logger.exception("Telemetry source capture failed.")
                raise

            if snapshot is not None:
                self._administrator.apply_snapshot(snapshot)
                self._current_snapshot_dict = asdict(self._administrator.get_latest_snapshot())

                if not self._has_logged_first_snapshot:
                    logger.info("First telemetry snapshot applied.")
                    self._has_logged_first_snapshot = True

                if self._current_snapshot_dict and self._publish_callback is not None:
                    try:
                        await self._publish_callback(self._current_snapshot_dict)
                    except Exception:
                        logger.exception("Publish callback failed.")
                        raise

            await asyncio.sleep(self._tick_seconds)
