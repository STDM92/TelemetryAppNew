from telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot


class ACCReceiver:
    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        return None
