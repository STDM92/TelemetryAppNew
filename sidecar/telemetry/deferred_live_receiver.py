from __future__ import annotations

import logging
import time
from typing import Callable

from sidecar.telemetry.adapter_contracts import SelectedTelemetrySource, TelemetryAdapter
from sidecar.telemetry.adapter_selection import select_live_adapter
from sidecar.telemetry.contracts import TelemetryReceiver
from sidecar.telemetry.modes import StartupRequest


logger = logging.getLogger(__name__)


class DeferredLiveReceiver:
    def __init__(
        self,
        request: StartupRequest,
        adapters: list[TelemetryAdapter],
        on_source_selected: Callable[[SelectedTelemetrySource], None] | None = None,
        probe_interval_s: float = 1.0,
    ):
        self._request = request
        self._adapters = adapters
        self._on_source_selected = on_source_selected
        self._probe_interval_s = probe_interval_s

        self._active_source: TelemetryReceiver | None = None
        self._last_probe_attempt_monotonic = 0.0
        self._waiting_logged = False

    def set_on_source_selected(
        self,
        callback: Callable[[SelectedTelemetrySource], None] | None,
    ) -> None:
        self._on_source_selected = callback

    def capture_snapshot(self):
        if self._active_source is not None:
            return self._active_source.capture_snapshot()

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