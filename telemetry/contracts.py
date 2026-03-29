from typing import Protocol

from telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot


class TelemetryReceiver(Protocol):
    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        ...
