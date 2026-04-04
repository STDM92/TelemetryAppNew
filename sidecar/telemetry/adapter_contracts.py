from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sidecar.telemetry.contracts import TelemetryReceiver
from sidecar.telemetry.modes import RuntimeMode, SimKind, SourceKind, StartupRequest


@dataclass(frozen=True)
class AdapterCapabilities:
    supports_live: bool
    supports_analyze_catalog: bool
    supports_analyze_from_file: bool
    supports_replay_file: bool


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
    mode: RuntimeMode
    source_kind: SourceKind
    file_path: Path | None = None


@dataclass(frozen=True)
class LiveSelectionResult:
    source: SelectedTelemetrySource
    adapter_id: str
    probe: ProbeResult


@dataclass(frozen=True)
class AnalyzableItem:
    id: str
    title: str
    source_path: Path | None
    sim_kind: SimKind | None
    is_active_candidate: bool = False
    is_ready: bool = True


class TelemetryAdapter(Protocol):
    @property
    def adapter_id(self) -> str: ...

    @property
    def sim_kind(self) -> SimKind: ...

    @property
    def display_name(self) -> str: ...
