from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable

from live_telemetry_sidecar.telemetry.adapter_contracts import SelectedTelemetrySource, TelemetryAdapter
from live_telemetry_sidecar.telemetry.contracts import TelemetryReceiver
from live_telemetry_sidecar.telemetry.modes import SimKind, SourceKind, StartupRequest


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _PendingCandidate:
    adapter: TelemetryAdapter
    selected_source: SelectedTelemetrySource
    confidence: int
    detail: str | None


class TelemetrySourceManager:
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
            source_kind=SourceKind.UNKNOWN,
        )

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._probe_thread: threading.Thread | None = None

        self._active_source: TelemetryReceiver | None = None
        self._active_adapter: TelemetryAdapter | None = None
        self._pending_candidate: _PendingCandidate | None = None

        self._missed_detach_probes = 0
        self._waiting_logged = False

    def start(self) -> None:
        with self._lock:
            thread = self._probe_thread
            if thread is not None and thread.is_alive():
                logger.debug("Telemetry source manager start requested while probe worker is already running.")
                return

            self._stop_event.clear()
            self._probe_thread = threading.Thread(
                target=self._probe_worker,
                name="telemetry-source-probe-worker",
                daemon=True,
            )
            self._probe_thread.start()

        logger.info("Telemetry source manager probe worker started.")

    def stop(self) -> None:
        self._stop_event.set()

        thread: threading.Thread | None
        with self._lock:
            thread = self._probe_thread

        if thread is not None and thread.is_alive():
            thread.join(timeout=max(self._probe_interval_s, self._detach_probe_interval_s) + 0.5)

        callback_source: SelectedTelemetrySource | None = None
        with self._lock:
            self._probe_thread = None
            self._pending_candidate = None
            self._missed_detach_probes = 0
            self._waiting_logged = False
            callback_source = self._detach_active_source_locked(notify=False)

        if callback_source is not None:
            logger.info("Telemetry source manager stopped and detached active telemetry source.")
        else:
            logger.info("Telemetry source manager stopped.")

    def set_on_source_selected(
        self,
        callback: Callable[[SelectedTelemetrySource], None] | None,
    ) -> None:
        self._on_source_selected = callback

    def capture_snapshot(self):
        callback_source: SelectedTelemetrySource | None = None

        with self._lock:
            if self._active_source is not None:
                return self._active_source.capture_snapshot()

            if self._pending_candidate is None:
                return None

            callback_source = self._attach_pending_candidate_locked()

        if callback_source is not None:
            callback = self._on_source_selected
            if callback is not None:
                callback(callback_source)

        return None

    def _probe_worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                callback_source = self._run_probe_cycle()
                if callback_source is not None:
                    callback = self._on_source_selected
                    if callback is not None:
                        callback(callback_source)
            except Exception:
                logger.exception("Telemetry probe worker cycle failed.")

            with self._lock:
                active_adapter = self._active_adapter

            wait_seconds = self._detach_probe_interval_s if active_adapter is not None else self._probe_interval_s
            self._stop_event.wait(wait_seconds)

    def _run_probe_cycle(self) -> SelectedTelemetrySource | None:
        with self._lock:
            active_adapter = self._active_adapter

        if active_adapter is not None:
            return self._check_for_detach(active_adapter)

        candidate = self._select_live_candidate()
        if candidate is None:
            with self._lock:
                self._pending_candidate = None
                should_log_waiting = not self._waiting_logged
                self._waiting_logged = True

            if should_log_waiting:
                logger.info("No supported live sim detected yet. Continuing to probe.")
            return None

        should_log = False
        with self._lock:
            same_candidate = self._is_same_pending_candidate_locked(candidate)
            if not same_candidate:
                self._pending_candidate = candidate
                should_log = True
            self._waiting_logged = False

        if should_log:
            logger.info(
                "Prepared live candidate. adapter_id=%s sim=%s confidence=%s detail=%s",
                candidate.adapter.adapter_id,
                candidate.selected_source.sim_kind.value,
                candidate.confidence,
                candidate.detail,
            )

        return None

    def _check_for_detach(self, active_adapter: TelemetryAdapter) -> SelectedTelemetrySource | None:
        probe = active_adapter.probe_live(self._request)
        if probe.is_running:
            recovered = False
            with self._lock:
                recovered = self._missed_detach_probes > 0
                self._missed_detach_probes = 0

            if recovered:
                logger.info(
                    "Live source probe recovered. adapter_id=%s sim=%s",
                    active_adapter.adapter_id,
                    probe.sim_kind.value,
                )
            return None

        should_detach = False
        missed_count = 0
        with self._lock:
            self._missed_detach_probes += 1
            missed_count = self._missed_detach_probes
            should_detach = self._missed_detach_probes >= self._detach_after_missed_probes

        logger.warning(
            "Live source probe missed. adapter_id=%s missed=%s/%s detail=%s",
            active_adapter.adapter_id,
            missed_count,
            self._detach_after_missed_probes,
            probe.detail,
        )

        if not should_detach:
            return None

        logger.warning(
            "Detaching live telemetry source after repeated probe failures. adapter_id=%s",
            active_adapter.adapter_id,
        )

        with self._lock:
            return self._detach_active_source_locked(notify=True)

    def _attach_pending_candidate_locked(self) -> SelectedTelemetrySource | None:
        candidate = self._pending_candidate
        if candidate is None:
            return None

        source = candidate.adapter.build_live_source(self._request)
        self._active_source = source
        self._active_adapter = candidate.adapter
        self._pending_candidate = None
        self._missed_detach_probes = 0
        self._waiting_logged = False

        logger.info(
            "Attached live telemetry source. sim=%s adapter_id=%s source_kind=%s",
            candidate.selected_source.display_name,
            candidate.adapter.adapter_id,
            candidate.selected_source.source_kind.value,
        )

        return candidate.selected_source

    def _detach_active_source_locked(self, notify: bool) -> SelectedTelemetrySource | None:
        active_source = self._active_source
        active_adapter = self._active_adapter
        if active_source is None and active_adapter is None:
            return None

        close_method = getattr(active_source, "close", None)
        if callable(close_method):
            try:
                close_method()
            except Exception:
                logger.exception("Failed to close detached live telemetry source cleanly.")

        self._active_source = None
        self._active_adapter = None
        self._pending_candidate = None
        self._missed_detach_probes = 0
        self._waiting_logged = False

        if notify:
            return self._waiting_source

        return None

    def _is_same_pending_candidate_locked(self, candidate: _PendingCandidate) -> bool:
        pending = self._pending_candidate
        if pending is None:
            return False

        return (
            pending.adapter.adapter_id == candidate.adapter.adapter_id
            and pending.selected_source == candidate.selected_source
            and pending.confidence == candidate.confidence
            and pending.detail == candidate.detail
        )

    def _select_live_candidate(self) -> _PendingCandidate | None:
        candidates: list[_PendingCandidate] = []

        for adapter in self._adapters:
            if not adapter.capabilities.supports_live:
                continue

            if self._request.requested_sim is not None and adapter.sim_kind is not self._request.requested_sim:
                continue

            probe = adapter.probe_live(self._request)
            if not probe.is_running:
                continue

            selected_source = adapter.describe_live_source(probe)
            candidates.append(
                _PendingCandidate(
                    adapter=adapter,
                    selected_source=selected_source,
                    confidence=probe.confidence,
                    detail=probe.detail,
                )
            )

        if not candidates:
            return None

        candidates.sort(key=lambda item: item.confidence, reverse=True)
        return candidates[0]
