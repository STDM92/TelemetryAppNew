from __future__ import annotations

import logging
import time
from typing import Any, Optional

import irsdk

from live_telemetry_sidecar.telemetry.models.unified_snapshot import (
    AngularRate,
    BrakeCornerData,
    BrakeSystemData,
    DriverInputs,
    EnvironmentData,
    LapData,
    Orientation,
    PitData,
    PowertrainData,
    RacePosition,
    SessionInfo,
    SuspensionCornerData,
    SuspensionData,
    TireBandTemperature,
    TireBandWear,
    TireCornerData,
    TireSetData,
    TrackCarMarker,
    TrackMapData,
    UnifiedTelemetrySnapshot,
    Vector3,
    VehicleDynamics,
)

logger = logging.getLogger(__name__)

def enum_class_to_dict(enum_cls, *, overrides: dict[int, str] | None = None) -> dict[int, str]:
    """
    Converts an IRSDK enum class to a dictionary mapping integer values to member names.

    :param enum_cls: The enum class to convert.
    :type enum_cls: Any

    :param overrides: Optional dictionary of value-to-name overrides.
    :type overrides: dict[int, str] | None

    :return: A dictionary mapping enum values to names.
    :rtype: dict[int, str]
    """
    result = {}
    for name, value in vars(enum_cls).items():
        if name.startswith("_"):
            continue
        if isinstance(value, int):
            result[value] = name
    if overrides:
        result.update(overrides)
    return result


def bitfield_class_to_dict(bitfield_cls) -> dict[int, str]:
    """
    Converts an IRSDK bitfield class to a dictionary mapping bitmask values to member names.

    :param bitfield_cls: The bitfield class to convert.
    :type bitfield_cls: Any

    :return: A dictionary mapping bitfield values to names.
    :rtype: dict[int, str]
    """
    result = {}
    for name, value in vars(bitfield_cls).items():
        if name.startswith("_"):
            continue
        if isinstance(value, int):
            result[value] = name
    return result


IRSDK_SESSION_STATE = enum_class_to_dict(irsdk.SessionState, overrides={2: "approaching_pits"})
IRSDK_TRACK_LOCATION = enum_class_to_dict(irsdk.TrkLoc, overrides={2: "approaching_pits"})
IRSDK_TRACK_SURFACE = enum_class_to_dict(irsdk.TrkSurf)
IRSDK_TRACK_WETNESS = enum_class_to_dict(irsdk.TrackWetness)

IRSDK_FLAG_BITS = bitfield_class_to_dict(irsdk.Flags)
IRSDK_PIT_SERVICE_STATUS_BITS = bitfield_class_to_dict(irsdk.PitSvFlags)
IRSDK_ENGINE_WARNINGS = bitfield_class_to_dict(irsdk.EngineWarnings)
IRSDK_PIT_SERVICE_STATUS = enum_class_to_dict(irsdk.PitSvStatus)
IRSDK_PACE_MODE = enum_class_to_dict(irsdk.PaceMode)
IRSDK_PACE_FLAGS = bitfield_class_to_dict(irsdk.PaceFlags)
IRSDK_CAR_LEFT_RIGHT = enum_class_to_dict(irsdk.CarLeftRight)

IRSDK_SKIES = { 0: "clear", 1: "partly_cloudy", 2: "mostly_cloudy", 3: "overcast", }


class IRacingBaseParser:
    def __init__(self) -> None:
        """
        Initializes the IRacingBaseParser.
        """
        self.connected = False
        self.source_name = "iracing" # Readers can override this to "iracing_replay"

    # --- ABSTRACT METHODS (Implemented by Receiver/Reader) ---
    def check_connection(self) -> None:
        """
        Checks if the parser is connected to an iRacing data source.
        Must be implemented by subclasses.

        :raises NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError

    def _get(self, name: str, default: Any = None) -> Any:
        """
        Retrieves a raw telemetry value by name from the data source.
        Must be implemented by subclasses.

        :param name: The name of the telemetry variable to retrieve.
        :type name: str

        :param default: The default value to return if the variable is not found.
        :type default: Any

        :return: The telemetry value or the default.
        :rtype: Any

        :raises NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError

    def _pre_capture(self) -> None:
        """
        Hook called before a snapshot capture begins. Can be overridden by subclasses.
        """
        pass

    def _post_capture(self) -> None:
        """
        Hook called after a snapshot capture finishes. Can be overridden by subclasses.
        """
        pass

    # --- SHARED HELPER METHODS ---
    def _get_bool(self, name: str) -> Optional[bool]:
        """
        Retrieves a telemetry value as a boolean.

        :param name: The name of the telemetry variable.
        :type name: str

        :return: The boolean value, or None if not found.
        :rtype: bool | None
        """
        value = self._get(name)
        return None if value is None else bool(value)

    def _get_float(self, name: str) -> Optional[float]:
        """
        Retrieves a telemetry value as a float.

        :param name: The name of the telemetry variable.
        :type name: str

        :return: The float value, or None if not found or invalid.
        :rtype: float | None
        """
        value = self._get(name)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _get_airpressure_pa(self, name: str) -> Optional[float]:
        """
        Retrieves a telemetry value and converts it from inches of mercury to Pascals.

        :param name: The name of the telemetry variable.
        :type name: str

        :return: The air pressure in Pascals, or None if not found.
        :rtype: float | None
        """
        raw_value = self._get(name)
        if raw_value is None:
            return None
        try:
            return float(raw_value) * 3386.389
        except (TypeError, ValueError):
            return None

    def _get_float_distance_ahead_behind(self, name: str) -> Optional[float]:
        """
        Retrieves a float telemetry value representing distance, with a specific check for iRacing's large 'no distance' value.

        :param name: The name of the telemetry variable.
        :type name: str

        :return: The distance in meters, or None if not found or no distance is available.
        :rtype: float | None
        """
        value = self._get(name)
        if value is None:
            return None
        try:
            f = float(value)
            if f >= 500000.0:
                return None
            return f
        except (TypeError, ValueError):
            return None

    def _get_int(self, name: str) -> Optional[int]:
        """
        Retrieves a telemetry value as an integer.

        :param name: The name of the telemetry variable.
        :type name: str

        :return: The integer value, or None if not found or invalid.
        :rtype: int | None
        """
        value = self._get(name)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _get_session_laps_int(self, name: str) -> Optional[int]:
        """
        Retrieves a session laps telemetry value as an integer, treating 32767 as None (infinite).

        :param name: The name of the telemetry variable.
        :type name: str

        :return: The number of laps, or None if not found or infinite.
        :rtype: int | None
        """
        value = self._get_int(name)
        if value is None or value == 32767:
            return None
        return value

    def _map_enum(self, value: Any, mapping: dict[int, str]) -> Optional[str]:
        """
        Maps an integer telemetry value to its corresponding enum name.

        :param value: The integer value to map.
        :type value: Any

        :param mapping: A dictionary mapping integers to names.
        :type mapping: dict[int, str]

        :return: The name of the enum member, or the original value as a string.
        :rtype: str | None
        """
        if value is None:
            return None
        try:
            return mapping.get(int(value), str(value))
        except (TypeError, ValueError):
            return str(value)

    def _decode_bitfield(self, value: Any, mapping: dict[int, str]) -> Optional[str]:
        """
        Decodes a bitfield telemetry value into a pipe-separated string of active flag names.

        :param value: The bitfield value to decode.
        :type value: Any

        :param mapping: A dictionary mapping bitmasks to flag names.
        :type mapping: dict[int, str]

        :return: A pipe-separated string of active flag names, 'none' if no flags are set, or None if value is None.
        :rtype: str | None
        """
        if value is None:
            return None
        try:
            raw = int(value)
        except (TypeError, ValueError):
            return None
        active = [name for bit, name in mapping.items() if raw & bit]
        return "|".join(active) if active else "none"

    def _ms_to_kph(self, value_mps: Optional[float]) -> Optional[float]:
        """
        Converts meters per second to kilometers per hour.

        :param value_mps: The speed in meters per second.
        :type value_mps: float | None

        :return: The speed in kilometers per hour, or None if input was None.
        :rtype: float | None
        """
        return None if value_mps is None else value_mps * 3.6

    def _m_to_mm(self, value_m: Optional[float]) -> Optional[float]:
        """
        Converts meters to millimeters.

        :param value_m: The distance in meters.
        :type value_m: float | None

        :return: The distance in millimeters, or None if input was None.
        :rtype: float | None
        """
        return None if value_m is None else value_m * 1000.0

    def _mps_to_mmps(self, value_mps: Optional[float]) -> Optional[float]:
        """
        Converts meters per second to millimeters per second.

        :param value_mps: The speed in meters per second.
        :type value_mps: float | None

        :return: The speed in millimeters per second, or None if input was None.
        :rtype: float | None
        """
        return None if value_mps is None else value_mps * 1000.0

    def _ratio_like(self, value: Optional[float]) -> Optional[float]:
        """
        Identity function for ratio-like values.

        :param value: The ratio value.
        :type value: float | None

        :return: The original ratio value.
        :rtype: float | None
        """
        return value

    def _build_tire_corner(self, prefix: str, compound_code: Optional[int]) -> TireCornerData:
        """
        Builds a TireCornerData object for a specific tire corner.

        :param prefix: The telemetry variable prefix for the tire corner (e.g., 'LF').
        :type prefix: str

        :param compound_code: The tire compound code.
        :type compound_code: int | None

        :return: A TireCornerData object containing the tire telemetry.
        :rtype: TireCornerData
        """
        live_pressure_kpa = self._get_float(f"{prefix}pressure")
        if live_pressure_kpa is None:
            live_pressure_kpa = self._get_float(f"{prefix}Press")

        wear_left = self._get_float(f"{prefix}wearL")
        wear_center = self._get_float(f"{prefix}wearM")
        wear_right = self._get_float(f"{prefix}wearR")

        return TireCornerData(
            cold_pressure_kpa=self._get_float(f"{prefix}coldPressure"),
            live_pressure_kpa=live_pressure_kpa,
            carcass_temp_c=TireBandTemperature(
                left_c=self._get_float(f"{prefix}tempCL"),
                center_c=self._get_float(f"{prefix}tempCM"),
                right_c=self._get_float(f"{prefix}tempCR"),
            ),
            surface_temp_c=TireBandTemperature(
                left_c=self._get_float(f"{prefix}tempL"),
                center_c=self._get_float(f"{prefix}tempM"),
                right_c=self._get_float(f"{prefix}tempR"),
            ),
            wear_ratio=TireBandWear(
                left_ratio=wear_left,
                center_ratio=wear_center,
                right_ratio=wear_right,
            ),
            tread_remaining_ratio=(
                min(v for v in (wear_left, wear_center, wear_right) if v is not None)
                if any(v is not None for v in (wear_left, wear_center, wear_right))
                else None
            ),
            compound_code=compound_code,
            odometer_m=self._get_float(f"{prefix}odometer"),
        )

    def _build_suspension_corner(self, prefix: str) -> SuspensionCornerData:
        """
        Builds a SuspensionCornerData object for a specific suspension corner.

        :param prefix: The telemetry variable prefix for the suspension corner (e.g., 'LF').
        :type prefix: str

        :return: A SuspensionCornerData object containing the suspension telemetry.
        :rtype: SuspensionCornerData
        """
        return SuspensionCornerData(
            ride_height_mm=self._m_to_mm(self._get_float(f"{prefix}rideHeight")),
            damper_position_mm=self._m_to_mm(self._get_float(f"{prefix}shockDefl")),
            damper_velocity_mm_s=self._mps_to_mmps(self._get_float(f"{prefix}shockVel")),
            suspension_deflection_mm=self._m_to_mm(self._get_float(f"{prefix}shockDefl")),
            wheel_load_n=None,
            wheel_speed_kph=self._ms_to_kph(self._get_float(f"{prefix}speed")),
        )

    def _safe_array_value(self, arr: Any, idx: int) -> Any:
        """
        Safely retrieves a value from an array-like object by index.

        :param arr: The array-like object (list, tuple, etc.).
        :type arr: Any

        :param idx: The index to retrieve.
        :type idx: int

        :return: The value at the index, or None if out of bounds or invalid.
        :rtype: Any
        """
        if not isinstance(arr, (list, tuple)) or idx < 0 or idx >= len(arr):
            return None
        return arr[idx]

    def _safe_array_float_allow_negative_one(self, arr: Any, idx: int) -> Optional[float]:
        """
        Safely retrieves a float value from an array, treating negative values (like -1) as None.

        :param arr: The array-like object.
        :type arr: Any

        :param idx: The index to retrieve.
        :type idx: int

        :return: The float value, or None if invalid or negative.
        :rtype: float | None
        """
        value = self._safe_array_value(arr, idx)
        if value is None:
            return None
        try:
            f = float(value)
            return None if f < 0.0 else f
        except (TypeError, ValueError):
            return None

    def _safe_array_int_allow_negative_one(self, arr: Any, idx: int) -> Optional[int]:
        """
        Safely retrieves an integer value from an array, treating negative values as None.

        :param arr: The array-like object.
        :type arr: Any

        :param idx: The index to retrieve.
        :type idx: int

        :return: The integer value, or None if invalid or negative.
        :rtype: int | None
        """
        value = self._safe_array_value(arr, idx)
        if value is None:
            return None
        try:
            i = int(value)
            return None if i < 0 else i
        except (TypeError, ValueError):
            return None

    def _safe_array_bool(self, arr: Any, idx: int) -> Optional[bool]:
        """
        Safely retrieves a boolean value from an array.

        :param arr: The array-like object.
        :type arr: Any

        :param idx: The index to retrieve.
        :type idx: int

        :return: The boolean value, or None if invalid.
        :rtype: bool | None
        """
        value = self._safe_array_value(arr, idx)
        return None if value is None else bool(value)

    def _build_track_map(self) -> TrackMapData:
        """
        Builds a TrackMapData object by parsing car-specific telemetry arrays.

        :return: A TrackMapData object containing player index and car markers.
        :rtype: TrackMapData
        """
        lap_dist_pct = self._get("CarIdxLapDistPct", [])
        positions = self._get("CarIdxPosition", [])
        class_positions = self._get("CarIdxClassPosition", [])
        on_pit_road = self._get("CarIdxOnPitRoad", [])
        track_surface = self._get("CarIdxTrackSurface", [])
        track_surface_material = self._get("CarIdxTrackSurfaceMaterial", [])
        last_lap_time = self._get("CarIdxLastLapTime", [])
        best_lap_time = self._get("CarIdxBestLapTime", [])
        est_time = self._get("CarIdxEstTime", [])

        cars: list[TrackCarMarker] = []
        if isinstance(lap_dist_pct, (list, tuple)):
            for idx in range(len(lap_dist_pct)):
                lap_ratio = self._safe_array_float_allow_negative_one(lap_dist_pct, idx)
                if lap_ratio is None:
                    continue

                cars.append(
                    TrackCarMarker(
                        car_index=idx,
                        overall_position=self._safe_array_int_allow_negative_one(positions, idx),
                        class_position=self._safe_array_int_allow_negative_one(class_positions, idx),
                        lap_distance_ratio=lap_ratio,
                        estimated_lap_time_to_marker_s=self._safe_array_float_allow_negative_one(est_time, idx),
                        is_on_pit_road=self._safe_array_bool(on_pit_road, idx),
                        track_location=self._map_enum(
                            self._safe_array_value(track_surface, idx),
                            IRSDK_TRACK_LOCATION,
                        ),
                        track_surface=self._map_enum(
                            self._safe_array_value(track_surface_material, idx),
                            IRSDK_TRACK_SURFACE,
                        ),
                        last_lap_time_s=self._safe_array_float_allow_negative_one(last_lap_time, idx),
                        best_lap_time_s=self._safe_array_float_allow_negative_one(best_lap_time, idx),
                    )
                )

        return TrackMapData(
            player_car_index=self._get_int("PlayerCarIdx"),
            cars=tuple(cars),
        )

    # --- THE MASTER PARSER LOGIC ---
    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        """
        The core logic for capturing a full telemetry snapshot from iRacing.

        :return: A UnifiedTelemetrySnapshot instance, or None if not connected.
        :rtype: UnifiedTelemetrySnapshot | None
        """
        self.check_connection()
        if not self.connected:
            return None

        self._pre_capture()
        try:
            speed_mps = self._get_float("Speed")
            lat_accel = self._get_float("LatAccel")
            long_accel = self._get_float("LongAccel")
            vert_accel = self._get_float("VertAccel")
            player_tire_compound = self._get_int("PlayerTireCompound")

            session = SessionInfo(
                simulator_name=self.source_name,
                track_name=None,
                session_type=None,
                session_phase=self._map_enum(self._get("SessionState"), IRSDK_SESSION_STATE),
                session_flags=self._decode_bitfield(self._get("SessionFlags"), IRSDK_FLAG_BITS),
                session_time_s=self._get_float("SessionTime"),
                session_time_remaining_s=self._get_float("SessionTimeRemain"),
                session_laps_total=self._get_session_laps_int("SessionLapsTotal"),
                session_laps_remaining=(
                    self._get_session_laps_int("SessionLapsRemainEx")
                    if self._get_session_laps_int("SessionLapsRemainEx") is not None
                    else self._get_session_laps_int("SessionLapsRemain")
                ),
                is_on_track=self._get_bool("IsOnTrack"),
                is_on_pit_road=self._get_bool("OnPitRoad"),
                is_in_garage=self._get_bool("IsInGarage"),
            )

            lap = LapData(
                current_lap=self._get_int("Lap"),
                completed_laps=self._get_int("LapCompleted"),
                lap_distance_m=self._get_float("LapDist"),
                lap_distance_ratio=self._get_float("LapDistPct"),
                current_lap_time_s=self._get_float("LapCurrentLapTime"),
                last_lap_time_s=self._get_float("LapLastLapTime"),
                best_lap_time_s=self._get_float("LapBestLapTime"),
                optimal_lap_time_s=self._get_float("LapBestNLapTime"),
                delta_to_best_lap_s=self._get_float("LapDeltaToBestLap"),
                delta_to_optimal_lap_s=self._get_float("LapDeltaToOptimalLap"),
                delta_to_session_best_lap_s=self._get_float("LapDeltaToSessionBestLap"),
                delta_to_best_lap_valid=self._get_bool("LapDeltaToBestLap_OK"),
                delta_to_optimal_lap_valid=self._get_bool("LapDeltaToOptimalLap_OK"),
                delta_to_session_best_lap_valid=self._get_bool("LapDeltaToSessionBestLap_OK"),
            )

            race = RacePosition(
                overall_position=self._get_int("PlayerCarPosition"),
                class_position=self._get_int("PlayerCarClassPosition"),
                car_index=self._get_int("PlayerCarIdx"),
                gap_ahead_s=None,
                gap_behind_s=None,
                distance_ahead_m=self._get_float_distance_ahead_behind("CarDistAhead"),
                distance_behind_m=self._get_float_distance_ahead_behind("CarDistBehind"),
            )

            inputs = DriverInputs(
                throttle_ratio=self._ratio_like(self._get_float("Throttle")),
                brake_ratio=self._ratio_like(self._get_float("Brake")),
                clutch_ratio=self._ratio_like(self._get_float("Clutch")),
                steering_angle_rad=self._get_float("SteeringWheelAngle"),
                handbrake_ratio=self._ratio_like(self._get_float("HandbrakeRaw")),
            )

            powertrain = PowertrainData(
                gear=self._get_int("Gear"),
                engine_speed_rpm=self._get_float("RPM"),
                vehicle_speed_kph=self._ms_to_kph(speed_mps),
                fuel_remaining_l=self._get_float("FuelLevel"),
                fuel_remaining_ratio=self._ratio_like(self._get_float("FuelLevelPct")),
                fuel_use_per_hour=self._get_float("FuelUsePerHour"),
                oil_temp_c=self._get_float("OilTemp"),
                oil_pressure_bar=self._get_float("OilPress"),
                water_temp_c=self._get_float("WaterTemp"),
                water_level_l=self._get_float("WaterLevel"),
                fuel_pressure_bar=self._get_float("FuelPress"),
                voltage_v=self._get_float("Voltage"),
            )

            tires = TireSetData(
                left_front=self._build_tire_corner("LF", player_tire_compound),
                right_front=self._build_tire_corner("RF", player_tire_compound),
                left_rear=self._build_tire_corner("LR", player_tire_compound),
                right_rear=self._build_tire_corner("RR", player_tire_compound),
            )

            brakes = BrakeSystemData(
                brake_bias_ratio=self._get_float("dcBrakeBias"),
                abs_setting=self._get_float("dcABS"),
                abs_active=self._get_bool("BrakeABSactive"),
                left_front=BrakeCornerData(line_pressure_bar=self._get_float("LFbrakeLinePress")),
                right_front=BrakeCornerData(line_pressure_bar=self._get_float("RFbrakeLinePress")),
                left_rear=BrakeCornerData(line_pressure_bar=self._get_float("LRbrakeLinePress")),
                right_rear=BrakeCornerData(line_pressure_bar=self._get_float("RRbrakeLinePress")),
            )

            suspension = SuspensionData(
                left_front=self._build_suspension_corner("LF"),
                right_front=self._build_suspension_corner("RF"),
                left_rear=self._build_suspension_corner("LR"),
                right_rear=self._build_suspension_corner("RR"),
            )

            dynamics = VehicleDynamics(
                velocity_mps=Vector3(
                    x=self._get_float("VelocityX"),
                    y=self._get_float("VelocityY"),
                    z=self._get_float("VelocityZ"),
                ),
                acceleration_mps2=Vector3(
                    x=long_accel,
                    y=lat_accel,
                    z=vert_accel,
                ),
                orientation=Orientation(
                    yaw_rad=self._get_float("Yaw"),
                    pitch_rad=self._get_float("Pitch"),
                    roll_rad=self._get_float("Roll"),
                ),
                angular_rate=AngularRate(
                    yaw_rad_s=self._get_float("YawRate"),
                    pitch_rad_s=self._get_float("PitchRate"),
                    roll_rad_s=self._get_float("RollRate"),
                ),
                steering_torque_nm=self._get_float("SteeringWheelTorque"),
                steering_torque_pct=self._ratio_like(self._get_float("SteeringWheelPctTorque")),
                lateral_accel_g=(lat_accel / 9.80665) if lat_accel is not None else None,
                longitudinal_accel_g=(long_accel / 9.80665) if long_accel is not None else None,
                vertical_accel_g=(vert_accel / 9.80665) if vert_accel is not None else None,
            )

            environment = EnvironmentData(
                air_temp_c=self._get_float("AirTemp"),
                track_temp_c=(
                    self._get_float("TrackTempCrew")
                    if self._get_float("TrackTempCrew") is not None
                    else self._get_float("TrackTemp")
                ),
                relative_humidity_ratio=self._ratio_like(self._get_float("RelativeHumidity")),
                air_pressure_pa=self._get_airpressure_pa("AirPressure"),
                air_density_kg_m3=self._get_float("AirDensity"),
                wind_speed_mps=self._get_float("WindVel"),
                wind_direction_rad=self._get_float("WindDir"),
                sky_condition=self._map_enum(self._get("Skies"), IRSDK_SKIES),
                precipitation_ratio=self._ratio_like(self._get_float("Precipitation")),
                fog_ratio=self._ratio_like(self._get_float("FogLevel")),
                surface_wetness=self._map_enum(self._get("TrackWetness"), IRSDK_TRACK_WETNESS),
                wet_tires_allowed=self._get_bool("WeatherDeclaredWet"),
            )

            pit = PitData(
                pit_service_status=self._decode_bitfield(
                    self._get("PitSvFlags") if self._get("PitSvFlags") is not None else self._get("PlayerCarPitSvStatus"),
                    IRSDK_PIT_SERVICE_STATUS_BITS,
                ),
                pit_stop_active=self._get_bool("PitstopActive"),
                required_repair_time_s=self._get_float("PitRepairLeft"),
                optional_repair_time_s=self._get_float("PitOptRepairLeft"),
                fast_repairs_used=(
                    self._get_int("FastRepairUsed")
                    if self._get_int("FastRepairUsed") is not None
                    else self._get_int("PlayerFastRepairsUsed")
                ),
                fast_repairs_remaining=self._get_int("FastRepairAvailable"),
            )

            track_map = self._build_track_map()

            return UnifiedTelemetrySnapshot(
                source=self.source_name,
                timestamp=time.time(),
                session=session,
                lap=lap,
                race=race,
                inputs=inputs,
                powertrain=powertrain,
                tires=tires,
                brakes=brakes,
                suspension=suspension,
                dynamics=dynamics,
                environment=environment,
                pit=pit,
                track_map=track_map,
            )
        except Exception:
            logger.exception(
                "Failed to capture iRacing snapshot. source=%s connected=%s",
                self.source_name,
                self.connected,
            )
            raise
        finally:
            self._post_capture()
