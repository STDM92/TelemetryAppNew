from live_telemetry_sidecar.telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot
from live_telemetry_sidecar.telemetry.models.unified_state import UnifiedState


class TelemetryStateAdministrator:
    def __init__(self):
        """
        Initializes the TelemetryStateAdministrator with a fresh UnifiedState instance.
        """
        self._state = UnifiedState()

    def apply_snapshot(self, snapshot: UnifiedTelemetrySnapshot) -> None:
        """
        Applies a new telemetry snapshot to the current state.

        :param snapshot: The telemetry snapshot to apply.
        :type snapshot: UnifiedTelemetrySnapshot
        """
        self._state.apply_snapshot(snapshot)

    def get_latest_snapshot(self) -> UnifiedTelemetrySnapshot:
        """
        Retrieves the latest unified telemetry snapshot from the current state.

        :return: A UnifiedTelemetrySnapshot representing the current state.
        :rtype: UnifiedTelemetrySnapshot
        """
        return self._state.to_snapshot()
