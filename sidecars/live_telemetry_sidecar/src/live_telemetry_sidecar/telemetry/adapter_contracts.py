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

    def probe_live(self, request: StartupRequest) -> ProbeResult: ...

    def describe_live_source(self, probe: ProbeResult) -> SelectedTelemetrySource: ...

    def build_live_source(self, request: StartupRequest) -> TelemetryReceiver: ...
