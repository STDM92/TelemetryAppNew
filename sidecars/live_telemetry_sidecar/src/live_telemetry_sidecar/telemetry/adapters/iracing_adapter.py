from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from live_telemetry_sidecar.telemetry.adapter_contracts import (
    AdapterCapabilities,
    ProbeResult,
    SelectedTelemetrySource,
)
from live_telemetry_sidecar.telemetry.modes import SimKind, SourceKind, StartupRequest


if TYPE_CHECKING:
    from live_telemetry_sidecar.telemetry.sims.iracing.iracing_receiver import IRacingReceiver


def _is_windows_process_running(process_name: str) -> bool:
    """
    Checks if a Windows process with the given name is currently running.

    :param process_name: The name of the process to check for (e.g., 'iRacingUI.exe').
    :type process_name: str

    :return: True if the process is found in the task list, False otherwise.
    :rtype: bool
    """
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
            capture_output=True,
            text=True,
            errors="ignore",
            check=False,
        )
    except Exception:
        return False

    stdout = result.stdout or ""
    return process_name.lower() in stdout.lower()


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
        )

    def probe_live(self, request: StartupRequest) -> ProbeResult:
        """
        Probes for iRacing processes to determine if the simulator is running.

        :param request: The startup request configuration.
        :type request: StartupRequest

        :return: A ProbeResult indicating if iRacing processes were detected.
        :rtype: ProbeResult
        """
        ui_running = _is_windows_process_running("iRacingUI.exe")
        sim_running = _is_windows_process_running("iRacingSim64DX11.exe")

        is_running = ui_running or sim_running

        if sim_running:
            detail = "iRacing sim process detected (iRacingSim64DX11.exe)."
            confidence = 220
        elif ui_running:
            detail = "iRacing UI detected (iRacingUI.exe)."
            confidence = 180
        else:
            detail = "No iRacing process detected."
            confidence = 0

        return ProbeResult(
            sim_kind=self.sim_kind,
            display_name=self.display_name,
            is_running=is_running,
            confidence=confidence,
            detail=detail,
        )

    def describe_live_source(self, probe: ProbeResult) -> SelectedTelemetrySource:
        """
        Describes the iRacing live telemetry source.

        :param probe: The result of a previous live probe.
        :type probe: ProbeResult

        :return: A SelectedTelemetrySource object for iRacing.
        :rtype: SelectedTelemetrySource
        """
        return SelectedTelemetrySource(
            sim_kind=probe.sim_kind,
            display_name=probe.display_name,
            source_kind=SourceKind.MMAP,
        )

    def build_live_source(self, request: StartupRequest) -> "IRacingReceiver":
        """
        Builds an IRacingReceiver for capturing live telemetry.

        :param request: The startup request configuration.
        :type request: StartupRequest

        :return: An IRacingReceiver instance.
        :rtype: IRacingReceiver
        """
        from live_telemetry_sidecar.telemetry.sims.iracing.iracing_receiver import (
            IRacingReceiver,
        )

        return IRacingReceiver()
