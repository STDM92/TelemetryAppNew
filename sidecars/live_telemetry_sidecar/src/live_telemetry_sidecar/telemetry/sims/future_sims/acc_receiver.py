from live_telemetry_sidecar.telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot


class ACCReceiver:
    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        """
        Captures a telemetry snapshot from Assetto Corsa Competizione. 
        Currently not implemented.

        :return: None as it is not implemented.
        :rtype: UnifiedTelemetrySnapshot | None
        """
        return None
