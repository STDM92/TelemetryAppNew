from __future__ import annotations

import logging
import time
from typing import Callable

from sidecar.telemetry.adapter_contracts import SelectedTelemetrySource, TelemetryAdapter
from sidecar.telemetry.adapter_selection import select_live_adapter
from sidecar.telemetry.contracts import TelemetryReceiver
from sidecar.telemetry.modes import SimKind, SourceKind, StartupRequest


logger = logging.getLogger(__name__)


class DeferredLiveReceiver:
    def __init__(
        self,
        request: StartupRequest,
        adapters: list[TelemetryAdapter],
        on_source_selected: Callable[[SelectedTelemetrySource], None] | None = None,
        probe_interval_s: float = 1.0,
        detach_probe_interval_s: float = 1.0,
        detach_after_missed_probes: int = 3,
    ):
        self._request = request
        self._adapters = adapters
        self._on_source_selected = on_source_selected
        self._probe_interval_s = probe_interval_s
        self._detach_probe_interval_s = detach_probe_interval_s
        self._detach_after_missed_probes = detach_after_missed_probes

        self._waiting_source = SelectedTelemetrySource(
            sim_kind=SimKind.UNKNOWN,
            display_name="Waiting for simulator",
            source_kind=SourceKind.LIVE_FEED,
            file_path=None,
        )

        self._active_source: TelemetryReceiver | None = None
        self._active_adapter: TelemetryAdapter | None = None

        self._last_probe_attempt_monotonic = 0.0
        self._last_detach_probe_monotonic = 0.0
        self._missed_detach_probes = 0
        self._waiting_logged = False

    def set_on_source_selected(
        self,
        callback: Callable[[SelectedTelemetrySource], None] | None,
    ) -> None:
        self._on_source_selected = callback

    def capture_snapshot(self):
        active_source = self._active_source
        if active_source is not None:
            self._maybe_check_for_detach()

            active_source = self._active_source
            if active_source is None:
                return None

            return active_source.capture_snapshot()

        now = time.monotonic()
        if now - self._last_probe_attempt_monotonic < self._probe_interval_s:
            return None

        self._last_probe_attempt_monotonic = now

        try:
            selection = select_live_adapter(self._request, self._adapters)
        except RuntimeError:
            if not self._waiting_logged:
                logger.info("No supported live sim detected yet. Continuing to probe.")
                self._waiting_logged = True
            return None

        adapter = next(a for a in self._adapters if a.adapter_id == selection.adapter_id)
        self._active_source = adapter.build_live_source(self._request)
        self._active_adapter = adapter
        self._last_detach_probe_monotonic = 0.0
        self._missed_detach_probes = 0
        self._waiting_logged = False

        logger.info(
            "Attached live telemetry source. sim=%s adapter_id=%s source_kind=%s",
            selection.source.display_name,
            selection.adapter_id,
            selection.source.source_kind.value,
        )

        if self._on_source_selected is not None:
            self._on_source_selected(selection.source)

        return None
    def _maybe_check_for_detach(self) -> None:
        if self._active_adapter is None:
            return

        now = time.monotonic()
        if now - self._last_detach_probe_monotonic < self._detach_probe_interval_s:
            return

        self._last_detach_probe_monotonic = now

        probe = self._active_adapter.probe_live(self._request)
        if probe.is_running:
            if self._missed_detach_probes > 0:
                logger.info(
                    "Live source probe recovered. adapter_id=%s sim=%s",
                    self._active_adapter.adapter_id,
                    probe.sim_kind.value,
                )
            self._missed_detach_probes = 0
            return

        self._missed_detach_probes += 1
        logger.warning(
            "Live source probe missed. adapter_id=%s missed=%s/%s detail=%s",
            self._active_adapter.adapter_id,
            self._missed_detach_probes,
            self._detach_after_missed_probes,
            probe.detail,
        )

        if self._missed_detach_probes < self._detach_after_missed_probes:
            return

        logger.warning(
            "Detaching live telemetry source after repeated probe failures. adapter_id=%s",
            self._active_adapter.adapter_id,
        )

        close_method = getattr(self._active_source, "close", None)
        if callable(close_method):
            try:
                close_method()
            except Exception:
                logger.exception("Failed to close detached live telemetry source cleanly.")

        self._active_source = None
        self._active_adapter = None
        self._missed_detach_probes = 0
        self._last_probe_attempt_monotonic = 0.0
        self._waiting_logged = False

        if self._on_source_selected is not None:
            self._on_source_selected(self._waiting_source)