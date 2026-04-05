import asyncio
import logging
import time
from dataclasses import asdict
from typing import Awaitable, Callable

from live_telemetry_sidecar.telemetry.administrator import TelemetryStateAdministrator
from live_telemetry_sidecar.telemetry.adapter_contracts import SelectedTelemetrySource
from live_telemetry_sidecar.telemetry.contracts import TelemetryReceiver


logger = logging.getLogger(__name__)


class DriverBackendRuntime:
    def __init__(
        self,
        telemetry_source: TelemetryReceiver,
        publish_callback: Callable[[dict], Awaitable[None]] | None = None,
        active_source: SelectedTelemetrySource | None = None,
        tick_hz: float = 60,
        stale_after_s: float = 3.0,
    ):
        """
        Initializes the DriverBackendRuntime.

        :param telemetry_source: The source of telemetry data.
        :type telemetry_source: TelemetryReceiver

        :param publish_callback: An optional async callback to publish telemetry snapshots.
        :type publish_callback: Callable[[dict], Awaitable[None]] | None

        :param active_source: The currently selected telemetry source.
        :type active_source: SelectedTelemetrySource | None

        :param tick_hz: The frequency at which to poll the telemetry source, in Hertz.
        :type tick_hz: float

        :param stale_after_s: The duration in seconds after which data is considered stale.
        :type stale_after_s: float
        """
        self._telemetry_source = telemetry_source
        self._publish_callback = publish_callback
        self._tick_seconds = 1 / tick_hz
        self._stale_after_s = stale_after_s

        self._active_source = active_source
        self._administrator = TelemetryStateAdministrator()
        self._current_snapshot_dict: dict | None = None
        self._background_task: asyncio.Task | None = None
        self._status = "created"
        self._last_error: str | None = None
        self._has_logged_first_snapshot = False
        self._has_received_snapshot = False
        self._last_snapshot_at: float | None = None

    def set_active_source(self, active_source: SelectedTelemetrySource) -> None:
        """
        Sets the active telemetry source.

        :param active_source: The selected telemetry source to be made active.
        :type active_source: SelectedTelemetrySource
        """
        self._active_source = active_source

    async def start(self) -> None:
        """
        Starts the telemetry processing loop in a background task.
        """
        if self._background_task is not None and not self._background_task.done():
            logger.debug("Runtime start requested while background task is already running.")
            return

        source_start = getattr(self._telemetry_source, "start", None)
        if callable(source_start):
            source_start()

        logger.info("Starting driver backend runtime.")
        self._background_task = asyncio.create_task(
            self._telemetry_loop(),
            name="driver-backend-telemetry-loop",
        )
        self._background_task.add_done_callback(self._on_background_task_done)
        self._status = "running"
        self._last_error = None
        self._has_logged_first_snapshot = False
        self._has_received_snapshot = False
        self._last_snapshot_at = None

    async def stop(self) -> None:
        """
        Stops the telemetry processing loop and cancels the background task.
        """
        if self._background_task is None:
            source_stop = getattr(self._telemetry_source, "stop", None)
            if callable(source_stop):
                source_stop()

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
            source_stop = getattr(self._telemetry_source, "stop", None)
            if callable(source_stop):
                source_stop()

            if self._status != "failed":
                self._status = "stopped"
            logger.info("Driver backend runtime stopped.")

    def get_current_state(self) -> dict | None:
        """
        Returns the most recent telemetry snapshot as a dictionary.

        :return: The latest telemetry snapshot dictionary, or None if no snapshot has been received.
        :rtype: dict | None
        """
        return self._current_snapshot_dict

    def get_status(self) -> dict:
        """
        Returns the current status of the backend runtime, including stream and attachment states.
        Field discription:
            - status: Current status of the backend runtime. "created", "running", "stopped", or "failed".
            - last_error: The last error encountered by the backend runtime. "None" if no error has occurred.
            - source_attachment_state: State of the source attachment. "none", "waiting", or "attached".
            - stream_state: State of the telemetry stream. "failed", "idle", "stale", or "streaming".
            - has_received_snapshot: Whether a telemetry snapshot has been received. "True" or "False".
            - last_snapshot_at: Timestamp of the last received snapshot. "None" if no snapshot has been received.
            - sim: Kind of simulation being used, if any. "iracing", "acc", "lmu", "f1", "mock", or "unknown".
            - source_kind: Kind of source being used, if any. "mmap", "socket", "UDP", "websocket", or "unknown".

        :return: A dictionary containing status information.
        :rtype: dict
        """
        now = time.time()
        source_attachment_state = self._get_source_attachment_state()
        stream_state = self._get_stream_state(now)

        return {
            "status": self._status,
            "last_error": self._last_error,
            "source_attachment_state": source_attachment_state,
            "stream_state": stream_state,
            "has_received_snapshot": self._has_received_snapshot,
            "last_snapshot_at": self._last_snapshot_at,
            "sim": self._active_source.sim_kind.value if self._active_source is not None else None,
            "source_kind": self._active_source.source_kind.value if self._active_source is not None else None,
            "source_display_name": self._active_source.display_name if self._active_source is not None else None,
        }

    def _get_source_attachment_state(self) -> str:
        """
        Determines the attachment state of the telemetry source.

        :return: A string representing the attachment state ('none', 'waiting', or 'attached').
        :rtype: str
        """
        if self._active_source is None:
            return "none"

        if self._active_source.display_name == "Waiting for simulator":
            return "waiting"

        return "attached"

    def _get_stream_state(self, now: float) -> str:
        """
        Determines the state of the telemetry stream.

        :param now: The current timestamp in seconds.
        :type now: float

        :return: A string representing the stream state ('failed', 'idle', 'stale', or 'streaming').
        :rtype: str
        """
        if self._status == "failed":
            return "failed"

        if not self._has_received_snapshot:
            return "idle"

        if self._last_snapshot_at is None:
            return "idle"

        if now - self._last_snapshot_at > self._stale_after_s:
            return "stale"

        return "streaming"

    def _on_background_task_done(self, task: asyncio.Task) -> None:
        """
        Callback triggered when the telemetry loop background task finishes.

        :param task: The completed asyncio task.
        :type task: asyncio.Task
        """
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
        """
        The core telemetry processing loop that captures and publishes snapshots.
        """
        while True:
            try:
                snapshot = self._telemetry_source.capture_snapshot()
            except Exception:
                logger.exception("Telemetry source capture failed.")
                raise

            if snapshot is not None:
                self._administrator.apply_snapshot(snapshot)
                self._current_snapshot_dict = asdict(
                    self._administrator.get_latest_snapshot()
                )
                self._has_received_snapshot = True
                self._last_snapshot_at = time.time()

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
