from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


CornerName = str  # "lf", "rf", "lr", "rr"


@dataclass
class Vector3:
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


@dataclass
class Orientation:
    yaw_rad: Optional[float] = None
    pitch_rad: Optional[float] = None
    roll_rad: Optional[float] = None


@dataclass
class AngularRate:
    yaw_rad_s: Optional[float] = None
    pitch_rad_s: Optional[float] = None
    roll_rad_s: Optional[float] = None


@dataclass
class DriverInputs:
    throttle_ratio: Optional[float] = None
    brake_ratio: Optional[float] = None
    clutch_ratio: Optional[float] = None
    steering_angle_rad: Optional[float] = None
    handbrake_ratio: Optional[float] = None


@dataclass
class SessionInfo:
    simulator_name: Optional[str] = None
    track_name: Optional[str] = None
    session_type: Optional[str] = None
    session_phase: Optional[str] = None
    session_flags: Optional[str] = None

    session_time_s: Optional[float] = None
    session_time_remaining_s: Optional[float] = None
    session_laps_total: Optional[int] = None
    session_laps_remaining: Optional[int] = None

    is_on_track: Optional[bool] = None
    is_on_pit_road: Optional[bool] = None
    is_in_garage: Optional[bool] = None


@dataclass
class LapData:
    current_lap: Optional[int] = None
    completed_laps: Optional[int] = None

    lap_distance_m: Optional[float] = None
    lap_distance_ratio: Optional[float] = None

    current_lap_time_s: Optional[float] = None
    last_lap_time_s: Optional[float] = None
    best_lap_time_s: Optional[float] = None
    optimal_lap_time_s: Optional[float] = None

    delta_to_best_lap_s: Optional[float] = None
    delta_to_optimal_lap_s: Optional[float] = None
    delta_to_session_best_lap_s: Optional[float] = None

    delta_to_best_lap_valid: Optional[bool] = None
    delta_to_optimal_lap_valid: Optional[bool] = None
    delta_to_session_best_lap_valid: Optional[bool] = None


@dataclass
class RacePosition:
    overall_position: Optional[int] = None
    class_position: Optional[int] = None
    car_index: Optional[int] = None

    gap_ahead_s: Optional[float] = None
    gap_behind_s: Optional[float] = None
    distance_ahead_m: Optional[float] = None
    distance_behind_m: Optional[float] = None


@dataclass
class PowertrainData:
    gear: Optional[int] = None
    engine_speed_rpm: Optional[float] = None
    vehicle_speed_kph: Optional[float] = None

    fuel_remaining_l: Optional[float] = None
    fuel_remaining_ratio: Optional[float] = None
    fuel_use_per_hour: Optional[float] = None

    oil_temp_c: Optional[float] = None
    oil_pressure_bar: Optional[float] = None
    water_temp_c: Optional[float] = None
    water_level_l: Optional[float] = None
    fuel_pressure_bar: Optional[float] = None
    voltage_v: Optional[float] = None


@dataclass
class TireBandTemperature:
    left_c: Optional[float] = None
    center_c: Optional[float] = None
    right_c: Optional[float] = None


@dataclass
class TireBandWear:
    left_ratio: Optional[float] = None
    center_ratio: Optional[float] = None
    right_ratio: Optional[float] = None


@dataclass
class TireCornerData:
    cold_pressure_kpa: Optional[float] = None
    live_pressure_kpa: Optional[float] = None

    carcass_temp_c: TireBandTemperature = field(default_factory=TireBandTemperature)
    surface_temp_c: TireBandTemperature = field(default_factory=TireBandTemperature)

    wear_ratio: TireBandWear = field(default_factory=TireBandWear)

    tread_remaining_ratio: Optional[float] = None
    compound_code: Optional[int] = None
    odometer_m: Optional[float] = None


@dataclass
class TireSetData:
    left_front: TireCornerData = field(default_factory=TireCornerData)
    right_front: TireCornerData = field(default_factory=TireCornerData)
    left_rear: TireCornerData = field(default_factory=TireCornerData)
    right_rear: TireCornerData = field(default_factory=TireCornerData)


@dataclass
class BrakeCornerData:
    line_pressure_bar: Optional[float] = None
    disc_temp_c: Optional[float] = None


@dataclass
class BrakeSystemData:
    brake_bias_ratio: Optional[float] = None
    abs_setting: Optional[float] = None
    abs_active: Optional[bool] = None

    left_front: BrakeCornerData = field(default_factory=BrakeCornerData)
    right_front: BrakeCornerData = field(default_factory=BrakeCornerData)
    left_rear: BrakeCornerData = field(default_factory=BrakeCornerData)
    right_rear: BrakeCornerData = field(default_factory=BrakeCornerData)


@dataclass
class SuspensionCornerData:
    ride_height_mm: Optional[float] = None
    damper_position_mm: Optional[float] = None
    damper_velocity_mm_s: Optional[float] = None
    suspension_deflection_mm: Optional[float] = None
    wheel_load_n: Optional[float] = None
    wheel_speed_kph: Optional[float] = None


@dataclass
class SuspensionData:
    left_front: SuspensionCornerData = field(default_factory=SuspensionCornerData)
    right_front: SuspensionCornerData = field(default_factory=SuspensionCornerData)
    left_rear: SuspensionCornerData = field(default_factory=SuspensionCornerData)
    right_rear: SuspensionCornerData = field(default_factory=SuspensionCornerData)


@dataclass
class VehicleDynamics:
    velocity_mps: Vector3 = field(default_factory=Vector3)
    acceleration_mps2: Vector3 = field(default_factory=Vector3)

    orientation: Orientation = field(default_factory=Orientation)
    angular_rate: AngularRate = field(default_factory=AngularRate)

    steering_torque_nm: Optional[float] = None
    steering_torque_pct: Optional[float] = None

    lateral_accel_g: Optional[float] = None
    longitudinal_accel_g: Optional[float] = None
    vertical_accel_g: Optional[float] = None


@dataclass
class EnvironmentData:
    air_temp_c: Optional[float] = None
    track_temp_c: Optional[float] = None

    relative_humidity_ratio: Optional[float] = None
    air_pressure_pa: Optional[float] = None
    air_density_kg_m3: Optional[float] = None

    wind_speed_mps: Optional[float] = None
    wind_direction_rad: Optional[float] = None

    sky_condition: Optional[str] = None
    precipitation_ratio: Optional[float] = None
    fog_ratio: Optional[float] = None
    surface_wetness: Optional[str] = None
    wet_tires_allowed: Optional[bool] = None


@dataclass
class PitData:
    pit_service_status: Optional[str] = None
    pit_stop_active: Optional[bool] = None

    required_repair_time_s: Optional[float] = None
    optional_repair_time_s: Optional[float] = None

    fast_repairs_used: Optional[int] = None
    fast_repairs_remaining: Optional[int] = None


@dataclass
class TrackCarMarker:
    car_index: Optional[int] = None
    overall_position: Optional[int] = None
    class_position: Optional[int] = None

    lap_distance_ratio: Optional[float] = None
    estimated_lap_time_to_marker_s: Optional[float] = None

    is_on_pit_road: Optional[bool] = None
    track_location: Optional[str] = None
    track_surface: Optional[str] = None

    last_lap_time_s: Optional[float] = None
    best_lap_time_s: Optional[float] = None


@dataclass
class TrackMapData:
    player_car_index: Optional[int] = None
    cars: tuple[TrackCarMarker, ...] = ()


@dataclass
class UnifiedTelemetrySnapshot:
    source: str
    timestamp: float

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
