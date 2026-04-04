from live_telemetry_sidecar.telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot


class F1SeriesReceiver:
    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        """
        Captures a telemetry snapshot from the F1 series games. 
        Currently not implemented.

        :return: None as it is not implemented.
        :rtype: UnifiedTelemetrySnapshot | None
        """
        return None
