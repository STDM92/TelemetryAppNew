from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UnifiedTelemetrySnapshot:
    source: str
    timestamp: float

    track_name: Optional[str] = None
    session_type: Optional[str] = None
    current_lap: Optional[int] = None
    total_laps: Optional[int] = None
    track_status: Optional[str] = None
    weather: Optional[str] = None

    speed_kph: Optional[float] = None
    gear: Optional[int] = None
    fuel_remaining_liters: Optional[float] = None
    position: Optional[int] = None

    car_ahead_gap: Optional[float] = None
    car_behind_gap: Optional[float] = None

    tire_wear_percent: Optional[list[float]] = None
    tire_surface_temp_c: Optional[list[float]] = None
    tire_inner_temp_c: Optional[list[float]] = None