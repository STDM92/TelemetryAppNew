from __future__ import annotations

from pathlib import Path

from sidecar.telemetry.adapter_contracts import (
    AdapterCapabilities,
    AnalyzableItem,
    ProbeResult,
    SelectedTelemetrySource,
)
from sidecar.telemetry.modes import RuntimeMode, SimKind, SourceKind, StartupRequest
from sidecar.telemetry.sims.iracing.iracing_reader import IRacingReader
from sidecar.telemetry.sims.iracing.iracing_receiver import IRacingReceiver


class IRacingTelemetryAdapter:
    @property
    def adapter_id(self) -> str:
        return "iracing"

    @property
    def sim_kind(self) -> SimKind:
        return SimKind.IRACING

    @property
    def display_name(self) -> str:
        return "iRacing"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_live=True,
            supports_analyze_catalog=True,
            supports_analyze_from_file=True,
            supports_replay_file=True,
        )

    def probe_live(self, request: StartupRequest) -> ProbeResult:
        # Placeholder implementation for the first architecture pass.
        # We are intentionally introducing the adapter seam now before
        # adding real per-sim detection logic.
        return ProbeResult(
            sim_kind=self.sim_kind,
            display_name=self.display_name,
            is_running=request.mode is RuntimeMode.LIVE,
            confidence=100 if request.mode is RuntimeMode.LIVE else 0,
            detail="placeholder iRacing live probe",
        )

    def describe_live_source(self, probe: ProbeResult) -> SelectedTelemetrySource:
        return SelectedTelemetrySource(
            sim_kind=probe.sim_kind,
            display_name=probe.display_name,
            mode=RuntimeMode.LIVE,
            source_kind=SourceKind.LIVE_FEED,
            file_path=None,
        )

    def build_live_source(self, request: StartupRequest) -> IRacingReceiver:
        return IRacingReceiver()

    def build_file_source(self, request: StartupRequest, file_path: Path) -> IRacingReader:
        return IRacingReader(str(file_path))

    def list_analyzable_items(self, request: StartupRequest) -> list[AnalyzableItem]:
        # Analyze catalog behavior is intentionally not implemented yet.
        # This method exists now so the later analyze architecture can plug
        # into the same adapter model without reshaping the interface again.
        return []
