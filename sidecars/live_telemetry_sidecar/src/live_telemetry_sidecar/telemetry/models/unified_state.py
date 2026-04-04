from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass, field

from live_telemetry_sidecar.telemetry.models.unified_snapshot import (
    UnifiedTelemetrySnapshot,
    SessionInfo,
    LapData,
    RacePosition,
    DriverInputs,
    PowertrainData,
    TireSetData,
    BrakeSystemData,
    SuspensionData,
    VehicleDynamics,
    EnvironmentData,
    PitData,
    TrackMapData,
)


def _merge_dataclass_state(target, incoming) -> None:
    for f in fields(target):
        incoming_value = getattr(incoming, f.name)
        current_value = getattr(target, f.name)

        if is_dataclass(incoming_value) and is_dataclass(current_value):
            _merge_dataclass_state(current_value, incoming_value)
            continue

        if incoming_value is not None:
            setattr(target, f.name, incoming_value)


@dataclass
class UnifiedStateData:
    source: str = "unknown"
    timestamp: float = 0.0

    session: SessionInfo = field(default_factory=SessionInfo)
    lap: LapData = field(default_factory=LapData)
    race: RacePosition = field(default_factory=RacePosition)
    inputs: DriverInputs = field(default_factory=DriverInputs)
    powertrain: PowertrainData = field(default_factory=PowertrainData)
    tires: TireSetData = field(default_factory=TireSetData)
    brakes: BrakeSystemData = field(default_factory=BrakeSystemData)
    suspension: SuspensionData = field(default_factory=SuspensionData)
    dynamics: VehicleDynamics = field(default_factory=VehicleDynamics)
    environment: EnvironmentData = field(default_factory=EnvironmentData)
    pit: PitData = field(default_factory=PitData)
    track_map: TrackMapData = field(default_factory=TrackMapData)


class UnifiedState:
    def __init__(self) -> None:
        self.data = UnifiedStateData()

        self.lap_time_history_s: list[float] = []
        self.fuel_usage_per_lap_l: list[float] = []

    def apply_snapshot(self, snapshot: UnifiedTelemetrySnapshot) -> None:
        self.data.source = snapshot.source
        self.data.timestamp = snapshot.timestamp

        _merge_dataclass_state(self.data.session, snapshot.session)
        _merge_dataclass_state(self.data.lap, snapshot.lap)
        _merge_dataclass_state(self.data.race, snapshot.race)
        _merge_dataclass_state(self.data.inputs, snapshot.inputs)
        _merge_dataclass_state(self.data.powertrain, snapshot.powertrain)
        _merge_dataclass_state(self.data.tires, snapshot.tires)
        _merge_dataclass_state(self.data.brakes, snapshot.brakes)
        _merge_dataclass_state(self.data.suspension, snapshot.suspension)
        _merge_dataclass_state(self.data.dynamics, snapshot.dynamics)
        _merge_dataclass_state(self.data.environment, snapshot.environment)
        _merge_dataclass_state(self.data.pit, snapshot.pit)

        incoming_track_map = snapshot.track_map

        if incoming_track_map.cars or incoming_track_map.player_car_index is not None:
            self.data.track_map = TrackMapData(
                player_car_index=(
                    incoming_track_map.player_car_index
                    if incoming_track_map.player_car_index is not None
                    else self.data.track_map.player_car_index
                ),
                cars=(
                    incoming_track_map.cars
                    if incoming_track_map.cars
                    else self.data.track_map.cars
                ),
            )

    def update_lap_history(self, lap_time_s: float, fuel_used_l: float, max_items: int = 5) -> None:
        self.lap_time_history_s.append(lap_time_s)
        self.fuel_usage_per_lap_l.append(fuel_used_l)

        if len(self.lap_time_history_s) > max_items:
            self.lap_time_history_s.pop(0)
            self.fuel_usage_per_lap_l.pop(0)

    def to_snapshot(self) -> UnifiedTelemetrySnapshot:
        return UnifiedTelemetrySnapshot(
            source=self.data.source,
            timestamp=self.data.timestamp,
            session=deepcopy(self.data.session),
            lap=deepcopy(self.data.lap),
            race=deepcopy(self.data.race),
            inputs=deepcopy(self.data.inputs),
            powertrain=deepcopy(self.data.powertrain),
            tires=deepcopy(self.data.tires),
            brakes=deepcopy(self.data.brakes),
            suspension=deepcopy(self.data.suspension),
            dynamics=deepcopy(self.data.dynamics),
            environment=deepcopy(self.data.environment),
            pit=deepcopy(self.data.pit),
            track_map=deepcopy(self.data.track_map),
        )
