from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from live_telemetry_sidecar.telemetry.adapter_contracts import (
    AdapterCapabilities,
    ProbeResult,
    SelectedTelemetrySource,
)
from live_telemetry_sidecar.telemetry.modes import SimKind, SourceKind, StartupRequest
from live_telemetry_sidecar.telemetry.sims.mock.mock_receiver import MockSimReceiver


class MockSimTelemetryAdapter:
    def __init__(self, base_url: str = "http://127.0.0.1:8766"):
        """
        Initializes the MockSimTelemetryAdapter.

        :param base_url: The base URL of the mock simulator API.
        :type base_url: str
        """
        self._base_url = base_url.rstrip("/")

    @property
    def adapter_id(self) -> str:
        return "mock"

    @property
    def sim_kind(self) -> SimKind:
        return SimKind.MOCK

    @property
    def display_name(self) -> str:
        return "Mock Sim"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_live=True,
        )

    def probe_live(self, request: StartupRequest) -> ProbeResult:
        """
        Probes the mock simulator to determine if it is currently streaming.

        :param request: The startup request configuration.
        :type request: StartupRequest

        :return: A ProbeResult indicating the state of the mock simulator.
        :rtype: ProbeResult
        """
        sim_info_url = f"{self._base_url}/sim-info"

        try:
            http_request = Request(sim_info_url, method="GET")
            with urlopen(http_request, timeout=1.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            return ProbeResult(
                sim_kind=self.sim_kind,
                display_name=self.display_name,
                is_running=False,
                confidence=0,
                detail=f"mock sim probe failed: {exc}",
            )

        is_streaming = bool(payload.get("is_streaming"))
        sim_kind = payload.get("sim_kind")
        display_name = payload.get("display_name") or self.display_name

        if sim_kind != self.sim_kind.value:
            return ProbeResult(
                sim_kind=self.sim_kind,
                display_name=display_name,
                is_running=False,
                confidence=0,
                detail=f"unexpected sim_kind from mock sim endpoint: {sim_kind!r}",
            )

        return ProbeResult(
            sim_kind=self.sim_kind,
            display_name=display_name,
            is_running=is_streaming,
            confidence=200 if is_streaming else 0,
            detail=f"mock sim endpoint reachable at {sim_info_url}",
        )

    def describe_live_source(self, probe: ProbeResult) -> SelectedTelemetrySource:
        """
        Describes the mock simulator live telemetry source.

        :param probe: The result of a previous live probe.
        :type probe: ProbeResult

        :return: A SelectedTelemetrySource object for the mock simulator.
        :rtype: SelectedTelemetrySource
        """
        return SelectedTelemetrySource(
            sim_kind=probe.sim_kind,
            display_name=probe.display_name,
            source_kind=SourceKind.WEBSOCKET,
        )

    def build_live_source(self, request: StartupRequest) -> MockSimReceiver:
        """
        Builds a MockSimReceiver for capturing live telemetry.

        :param request: The startup request configuration.
        :type request: StartupRequest

        :return: A MockSimReceiver instance.
        :rtype: MockSimReceiver
        """
        return MockSimReceiver(base_url=self._base_url)
