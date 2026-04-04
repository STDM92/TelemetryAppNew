from sidecar.live_telemetry_sidecar.telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot
from sidecar.live_telemetry_sidecar.telemetry.models.unified_state import UnifiedState


class TelemetryStateAdministrator:
    def __init__(self):
        self._state = UnifiedState()

    def apply_snapshot(self, snapshot: UnifiedTelemetrySnapshot) -> None:
        self._state.apply_snapshot(snapshot)

    def get_latest_snapshot(self) -> UnifiedTelemetrySnapshot:
        return self._state.to_snapshot()
