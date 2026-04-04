from sidecar.telemetry.adapter_contracts import TelemetryAdapter
from sidecar.telemetry.adapters.mock_sim_adapter import MockSimTelemetryAdapter
from sidecar.telemetry.adapters.iracing_adapter import IRacingTelemetryAdapter


def build_available_adapters() -> list[TelemetryAdapter]:
    # Keep registration explicit and tiny.
    # This is a simple composition helper, not a plugin framework.
    return [
        MockSimTelemetryAdapter(),
        IRacingTelemetryAdapter(),
    ]
