from typing import Protocol

from live_telemetry_sidecar.telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot


class TelemetryReceiver(Protocol):
    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        """
        Captures a single telemetry snapshot from the source.

        :return: A UnifiedTelemetrySnapshot instance if data is available, otherwise None.
        :rtype: UnifiedTelemetrySnapshot | None
        """
        ...
