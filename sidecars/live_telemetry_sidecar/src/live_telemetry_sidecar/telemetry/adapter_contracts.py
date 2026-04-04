from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from live_telemetry_sidecar.telemetry.contracts import TelemetryReceiver
from live_telemetry_sidecar.telemetry.modes import SimKind, SourceKind, StartupRequest


@dataclass(frozen=True)
class AdapterCapabilities:
    supports_live: bool


@dataclass(frozen=True)
class ProbeResult:
    sim_kind: SimKind
    display_name: str
    is_running: bool
    confidence: int = 0
    detail: str | None = None


@dataclass(frozen=True)
class SelectedTelemetrySource:
    sim_kind: SimKind
    display_name: str
    source_kind: SourceKind


@dataclass(frozen=True)
class LiveSelectionResult:
    source: SelectedTelemetrySource
    adapter_id: str
    probe: ProbeResult


class TelemetryAdapter(Protocol):
    @property
    def adapter_id(self) -> str: ...

    @property
    def sim_kind(self) -> SimKind: ...

    @property
    def display_name(self) -> str: ...

    @property
    def capabilities(self) -> AdapterCapabilities: ...

    def probe_live(self, request: StartupRequest) -> ProbeResult:
        """
        Probes for a live telemetry source of the simulator type supported by this adapter.

        :param request: The startup request configuration.
        :type request: StartupRequest

        :return: A ProbeResult containing information about the detected simulator state.
        :rtype: ProbeResult
        """
        ...

    def describe_live_source(self, probe: ProbeResult) -> SelectedTelemetrySource:
        """
        Provides a description of the live telemetry source based on the probe results.

        :param probe: The result of a previous live probe.
        :type probe: ProbeResult

        :return: A SelectedTelemetrySource object describing the detected source.
        :rtype: SelectedTelemetrySource
        """
        ...

    def build_live_source(self, request: StartupRequest) -> TelemetryReceiver:
        """
        Builds a TelemetryReceiver instance for capturing live data from the simulator.

        :param request: The startup request configuration.
        :type request: StartupRequest

        :return: A TelemetryReceiver instance for capturing live data.
        :rtype: TelemetryReceiver
        """
        ...
