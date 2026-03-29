from dataclasses import dataclass, field
from typing import List

from telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot


@dataclass
class TireData:
    wear_percent: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    surface_temp_c: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    inner_temp_c: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])


@dataclass
class SessionData:
    track_name: str = "Unknown"
    session_type: str = "Race"
    current_lap: int = 0
    total_laps: int = 0
    track_status: str = "Green"
    weather: str = "Clear"


class UnifiedState:
    def __init__(self):
        self.session = SessionData()
        self.tires = TireData()

        self.speed_kph: float = 0.0
        self.gear: int = 0
        self.fuel_remaining_liters: float = 0.0
        self.position: int = 0

        self.car_ahead_gap: float = 0.0
        self.car_behind_gap: float = 0.0

        self.lap_time_history: List[float] = []
        self.fuel_usage_per_lap: List[float] = []

        self.last_source: str = "unknown"
        self.last_timestamp: float = 0.0

    def apply_snapshot(self, snapshot: UnifiedTelemetrySnapshot) -> None:
        self.last_source = snapshot.source
        self.last_timestamp = snapshot.timestamp

        if snapshot.track_name is not None:
            self.session.track_name = snapshot.track_name
        if snapshot.session_type is not None:
            self.session.session_type = snapshot.session_type
        if snapshot.current_lap is not None:
            self.session.current_lap = snapshot.current_lap
        if snapshot.total_laps is not None:
            self.session.total_laps = snapshot.total_laps
        if snapshot.track_status is not None:
            self.session.track_status = snapshot.track_status
        if snapshot.weather is not None:
            self.session.weather = snapshot.weather

        if snapshot.speed_kph is not None:
            self.speed_kph = snapshot.speed_kph
        if snapshot.gear is not None:
            self.gear = snapshot.gear
        if snapshot.fuel_remaining_liters is not None:
            self.fuel_remaining_liters = snapshot.fuel_remaining_liters
        if snapshot.position is not None:
            self.position = snapshot.position

        if snapshot.car_ahead_gap is not None:
            self.car_ahead_gap = snapshot.car_ahead_gap
        if snapshot.car_behind_gap is not None:
            self.car_behind_gap = snapshot.car_behind_gap

        if snapshot.tire_wear_percent is not None:
            self.tires.wear_percent = list(snapshot.tire_wear_percent)
        if snapshot.tire_surface_temp_c is not None:
            self.tires.surface_temp_c = list(snapshot.tire_surface_temp_c)
        if snapshot.tire_inner_temp_c is not None:
            self.tires.inner_temp_c = list(snapshot.tire_inner_temp_c)

    def update_lap_history(self, lap_time: float, fuel_used: float):
        self.lap_time_history.append(lap_time)
        self.fuel_usage_per_lap.append(fuel_used)

        if len(self.lap_time_history) > 5:
            self.lap_time_history.pop(0)
            self.fuel_usage_per_lap.pop(0)

    def to_snapshot(self) -> UnifiedTelemetrySnapshot:
        return UnifiedTelemetrySnapshot(
            source=self.last_source,
            timestamp=self.last_timestamp,
            track_name=self.session.track_name,
            session_type=self.session.session_type,
            current_lap=self.session.current_lap,
            total_laps=self.session.total_laps,
            track_status=self.session.track_status,
            weather=self.session.weather,
            speed_kph=self.speed_kph,
            gear=self.gear,
            fuel_remaining_liters=self.fuel_remaining_liters,
            position=self.position,
            car_ahead_gap=self.car_ahead_gap,
            car_behind_gap=self.car_behind_gap,
            tire_wear_percent=list(self.tires.wear_percent),
            tire_surface_temp_c=list(self.tires.surface_temp_c),
            tire_inner_temp_c=list(self.tires.inner_temp_c),
        )