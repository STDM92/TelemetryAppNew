from __future__ import annotations

import time
from typing import Any, Optional

import irsdk

from telemetry.models.unified_snapshot import (
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


IRSDK_SESSION_STATE = {
    0: "invalid",
    1: "get_in_car",
    2: "warmup",
    3: "parade_laps",
    4: "racing",
    5: "checkered",
    6: "cooldown",
}

IRSDK_TRACK_LOCATION = {
    -1: "not_in_world",
    0: "off_track",
    1: "in_pit_stall",
    2: "approaching_pits",
    3: "on_track",
}

IRSDK_SKIES = {
    0: "clear",
    1: "partly_cloudy",
    2: "mostly_cloudy",
    3: "overcast",
}

# Newer live schemas may expose more values than the older public PDF.
IRSDK_TRACK_WETNESS = {
    0: "dry",
    1: "mostly_dry",
    2: "very_lightly_wet",
    3: "lightly_wet",
    4: "moderately_wet",
    5: "very_wet",
    6: "extremely_wet",
}

IRSDK_FLAG_BITS = {
    0x00000001: "checkered",
    0x00000002: "white",
    0x00000004: "green",
    0x00000008: "yellow",
    0x00000010: "red",
    0x00000020: "blue",
    0x00000040: "debris",
    0x00000080: "crossed",
    0x00000100: "yellow_waving",
    0x00000200: "one_lap_to_green",
    0x00000400: "green_held",
    0x00000800: "ten_to_go",
    0x00001000: "five_to_go",
    0x00002000: "random_waving",
    0x00004000: "caution",
    0x00008000: "caution_waving",
    0x00010000: "black",
    0x00020000: "disqualify",
    0x00040000: "servicible",
    0x00080000: "furled",
    0x00100000: "repair",
    0x10000000: "start_hidden",
    0x20000000: "start_ready",
    0x40000000: "start_set",
    0x80000000: "start_go",
}

IRSDK_PIT_SERVICE_STATUS_BITS = {
    0x0001: "lf_tire_change",
    0x0002: "rf_tire_change",
    0x0004: "lr_tire_change",
    0x0008: "rr_tire_change",
    0x0010: "fuel_fill",
    0x0020: "windshield_tearoff",
    0x0040: "fast_repair",
}


class IRacingReceiver:
    def __init__(self) -> None:
        self.ir = irsdk.IRSDK()
        self.connected = False

    def check_connection(self) -> None:
        if self.connected and not (self.ir.is_initialized and self.ir.is_connected):
            self.connected = False
            self.ir.shutdown()
            print("iRacing disconnected.")
        elif (
            not self.connected
            and self.ir.startup()
            and self.ir.is_initialized
            and self.ir.is_connected
        ):
            self.connected = True
            print("iRacing connected. Listening for telemetry...")

    def _get(self, name: str, default: Any = None) -> Any:
        try:
            value = self.ir[name]
            return default if value is None else value
        except KeyError:
            return default

    def _get_bool(self, name: str) -> Optional[bool]:
        value = self._get(name)
        return None if value is None else bool(value)

    def _get_float(self, name: str) -> Optional[float]:
        value = self._get(name)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _get_int(self, name: str) -> Optional[int]:
        value = self._get(name)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _map_enum(self, value: Any, mapping: dict[int, str]) -> Optional[str]:
        if value is None:
            return None
        try:
            return mapping.get(int(value), str(value))
        except (TypeError, ValueError):
            return str(value)

    def _decode_bitfield(self, value: Any, mapping: dict[int, str]) -> Optional[str]:
        if value is None:
            return None
        try:
            raw = int(value)
        except (TypeError, ValueError):
            return None
        active = [name for bit, name in mapping.items() if raw & bit]
        return "|".join(active) if active else "none"

    def _ms_to_kph(self, value_mps: Optional[float]) -> Optional[float]:
        return None if value_mps is None else value_mps * 3.6

    def _m_to_mm(self, value_m: Optional[float]) -> Optional[float]:
        return None if value_m is None else value_m * 1000.0

    def _mps_to_mmps(self, value_mps: Optional[float]) -> Optional[float]:
        return None if value_mps is None else value_mps * 1000.0

    def _ratio_like(self, value: Optional[float]) -> Optional[float]:
        return value

    def _build_tire_corner(self, prefix: str, compound_code: Optional[int]) -> TireCornerData:
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
        return SuspensionCornerData(
            ride_height_mm=self._m_to_mm(self._get_float(f"{prefix}rideHeight")),
            damper_position_mm=self._m_to_mm(self._get_float(f"{prefix}shockDefl")),
            damper_velocity_mm_s=self._mps_to_mmps(self._get_float(f"{prefix}shockVel")),
            suspension_deflection_mm=self._m_to_mm(self._get_float(f"{prefix}shockDefl")),
            wheel_load_n=None,
            wheel_speed_kph=self._ms_to_kph(self._get_float(f"{prefix}speed")),
        )

    def _safe_array_value(self, arr: Any, idx: int) -> Any:
        if not isinstance(arr, (list, tuple)) or idx < 0 or idx >= len(arr):
            return None
        return arr[idx]

    def _safe_array_float_allow_negative_one(self, arr: Any, idx: int) -> Optional[float]:
        value = self._safe_array_value(arr, idx)
        if value is None:
            return None
        try:
            f = float(value)
            return None if f < 0.0 else f
        except (TypeError, ValueError):
            return None

    def _safe_array_int_allow_negative_one(self, arr: Any, idx: int) -> Optional[int]:
        value = self._safe_array_value(arr, idx)
        if value is None:
            return None
        try:
            i = int(value)
            return None if i < 0 else i
        except (TypeError, ValueError):
            return None

    def _safe_array_bool(self, arr: Any, idx: int) -> Optional[bool]:
        value = self._safe_array_value(arr, idx)
        return None if value is None else bool(value)

    def _build_track_map(self) -> TrackMapData:
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
                        track_surface=(
                            None
                            if self._safe_array_value(track_surface_material, idx) is None
                            else str(self._safe_array_value(track_surface_material, idx))
                        ),
                        last_lap_time_s=self._safe_array_float_allow_negative_one(last_lap_time, idx),
                        best_lap_time_s=self._safe_array_float_allow_negative_one(best_lap_time, idx),
                    )
                )

        return TrackMapData(
            player_car_index=self._get_int("PlayerCarIdx"),
            cars=tuple(cars),
        )

    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        self.check_connection()
        if not self.connected:
            return None

        self.ir.freeze_var_buffer_latest()
        try:
            speed_mps = self._get_float("Speed")
            lat_accel = self._get_float("LatAccel")
            long_accel = self._get_float("LongAccel")
            vert_accel = self._get_float("VertAccel")
            player_tire_compound = self._get_int("PlayerTireCompound")

            session = SessionInfo(
                simulator_name="iracing",
                track_name=None,
                session_type=None,
                session_phase=self._map_enum(self._get("SessionState"), IRSDK_SESSION_STATE),
                session_flags=self._decode_bitfield(self._get("SessionFlags"), IRSDK_FLAG_BITS),
                session_time_s=self._get_float("SessionTime"),
                session_time_remaining_s=self._get_float("SessionTimeRemain"),
                session_laps_total=self._get_int("SessionLapsTotal"),
                session_laps_remaining=(
                    self._get_int("SessionLapsRemainEx")
                    if self._get_int("SessionLapsRemainEx") is not None
                    else self._get_int("SessionLapsRemain")
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
                distance_ahead_m=self._get_float("CarDistAhead"),
                distance_behind_m=self._get_float("CarDistBehind"),
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
                air_pressure_pa=self._get_float("AirPressure"),
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
                source="iracing",
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
        except Exception as ex:
            print(f"Failed to capture iRacing snapshot: {ex}")
            return None
        finally:
            self.ir.unfreeze_var_buffer_latest()
