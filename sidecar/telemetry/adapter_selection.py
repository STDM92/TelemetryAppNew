from sidecar.telemetry.adapter_contracts import (
    LiveSelectionResult,
    ProbeResult,
    TelemetryAdapter,
)
from sidecar.telemetry.modes import RuntimeMode, StartupRequest


def select_live_adapter(
    request: StartupRequest,
    adapters: list[TelemetryAdapter],
) -> LiveSelectionResult:
    if request.mode is not RuntimeMode.LIVE:
        raise RuntimeError(
            f"select_live_adapter only supports live mode, got {request.mode.value}."
        )

    candidates: list[tuple[TelemetryAdapter, ProbeResult]] = []

    for adapter in adapters:
        if not adapter.capabilities.supports_live:
            continue

        if request.requested_sim is not None and adapter.sim_kind is not request.requested_sim:
            continue

        probe = adapter.probe_live(request)
        if not probe.is_running:
            continue

        candidates.append((adapter, probe))

    if not candidates:
        if request.requested_sim is not None:
            raise RuntimeError(
                f"No supported live sim detected for requested sim '{request.requested_sim.value}'."
            )
        raise RuntimeError("No supported live sim detected.")

    candidates.sort(key=lambda item: item[1].confidence, reverse=True)
    selected_adapter, selected_probe = candidates[0]

    return LiveSelectionResult(
        adapter_id=selected_adapter.adapter_id,
        probe=selected_probe,
        source=selected_adapter.describe_live_source(selected_probe),
    )