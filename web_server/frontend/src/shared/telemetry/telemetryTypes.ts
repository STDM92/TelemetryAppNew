export type NullableNumber = number | null;
export type NullableString = string | null;

export type TireTemperatureTriplet = {
  left_c: NullableNumber;
  center_c: NullableNumber;
  right_c: NullableNumber;
};

export type TireWearTriplet = {
  left_ratio: NullableNumber;
  center_ratio: NullableNumber;
  right_ratio: NullableNumber;
};

export type TireData = {
  cold_pressure_kpa: NullableNumber;
  live_pressure_kpa: NullableNumber;
  carcass_temp_c: TireTemperatureTriplet | null;
  surface_temp_c: TireTemperatureTriplet | null;
  wear_ratio: TireWearTriplet | null;
  tread_remaining_ratio: NullableNumber;
  compound_code: number | null;
  odometer_m: NullableNumber;
};

export type BrakeCornerData = {
  line_pressure_bar: NullableNumber;
  disc_temp_c: NullableNumber;
};

export type SuspensionCornerData = {
  ride_height_mm: NullableNumber;
  damper_position_mm: NullableNumber;
  damper_velocity_mm_s: NullableNumber;
  suspension_deflection_mm: NullableNumber;
  wheel_load_n: NullableNumber;
  wheel_speed_kph: NullableNumber;
};

export type Vector3 = {
  x: NullableNumber;
  y: NullableNumber;
  z: NullableNumber;
};

export type OrientationData = {
  yaw_rad: NullableNumber;
  pitch_rad: NullableNumber;
  roll_rad: NullableNumber;
};

export type AngularRateData = {
  yaw_rad_s: NullableNumber;
  pitch_rad_s: NullableNumber;
  roll_rad_s: NullableNumber;
};

export type TrackMapCar = {
  car_index: number | null;
  overall_position: number | null;
  class_position: number | null;
  lap_distance_ratio: NullableNumber;
  estimated_lap_time_to_marker_s: NullableNumber;
  is_on_pit_road: boolean | null;
  track_location: NullableString;
  track_surface: NullableString;
  last_lap_time_s: NullableNumber;
  best_lap_time_s: NullableNumber;
};

export type TelemetrySnapshot = {
  source: NullableString;
  timestamp: number | null;
  session: {
    simulator_name: NullableString;
    track_name: NullableString;
    session_type: NullableString;
    session_phase: NullableString;
    session_flags: NullableString;
    session_time_s: NullableNumber;
    session_time_remaining_s: NullableNumber;
    session_laps_total: number | null;
    session_laps_remaining: number | null;
    is_on_track: boolean | null;
    is_on_pit_road: boolean | null;
    is_in_garage: boolean | null;
  } | null;
  lap: {
    current_lap: number | null;
    completed_laps: number | null;
    lap_distance_m: NullableNumber;
    lap_distance_ratio: NullableNumber;
    current_lap_time_s: NullableNumber;
    last_lap_time_s: NullableNumber;
    best_lap_time_s: NullableNumber;
    optimal_lap_time_s: NullableNumber;
    delta_to_best_lap_s: NullableNumber;
    delta_to_optimal_lap_s: NullableNumber;
    delta_to_session_best_lap_s: NullableNumber;
    delta_to_best_lap_valid: boolean | null;
    delta_to_optimal_lap_valid: boolean | null;
    delta_to_session_best_lap_valid: boolean | null;
  } | null;
  race: {
    overall_position: number | null;
    class_position: number | null;
    car_index: number | null;
    gap_ahead_s: NullableNumber;
    gap_behind_s: NullableNumber;
    distance_ahead_m: NullableNumber;
    distance_behind_m: NullableNumber;
  } | null;
  inputs: {
    throttle_ratio: NullableNumber;
    brake_ratio: NullableNumber;
    clutch_ratio: NullableNumber;
    steering_angle_rad: NullableNumber;
    handbrake_ratio: NullableNumber;
  } | null;
  powertrain: {
    gear: number | null;
    engine_speed_rpm: NullableNumber;
    vehicle_speed_kph: NullableNumber;
    fuel_remaining_l: NullableNumber;
    fuel_remaining_ratio: NullableNumber;
    fuel_use_per_hour: NullableNumber;
    oil_temp_c: NullableNumber;
    oil_pressure_bar: NullableNumber;
    water_temp_c: NullableNumber;
    water_level_l: NullableNumber;
    fuel_pressure_bar: NullableNumber;
    voltage_v: NullableNumber;
  } | null;
  tires: {
    left_front: TireData | null;
    right_front: TireData | null;
    left_rear: TireData | null;
    right_rear: TireData | null;
  } | null;
  brakes: {
    brake_bias_ratio: NullableNumber;
    abs_setting: number | null;
    abs_active: boolean | null;
    left_front: BrakeCornerData | null;
    right_front: BrakeCornerData | null;
    left_rear: BrakeCornerData | null;
    right_rear: BrakeCornerData | null;
  } | null;
  suspension: {
    left_front: SuspensionCornerData | null;
    right_front: SuspensionCornerData | null;
    left_rear: SuspensionCornerData | null;
    right_rear: SuspensionCornerData | null;
  } | null;
  dynamics: {
    velocity_mps: Vector3 | null;
    acceleration_mps2: Vector3 | null;
    orientation: OrientationData | null;
    angular_rate: AngularRateData | null;
    steering_torque_nm: NullableNumber;
    steering_torque_pct: NullableNumber;
    lateral_accel_g: NullableNumber;
    longitudinal_accel_g: NullableNumber;
    vertical_accel_g: NullableNumber;
  } | null;
  environment: {
    air_temp_c: NullableNumber;
    track_temp_c: NullableNumber;
    relative_humidity_ratio: NullableNumber;
    air_pressure_pa: NullableNumber;
    air_density_kg_m3: NullableNumber;
    wind_speed_mps: NullableNumber;
    wind_direction_rad: NullableNumber;
    sky_condition: NullableString;
    precipitation_ratio: NullableNumber;
    fog_ratio: NullableNumber;
    surface_wetness: NullableString;
    wet_tires_allowed: boolean | null;
  } | null;
  pit: {
    pit_service_status: NullableString;
    pit_stop_active: boolean | null;
    required_repair_time_s: NullableNumber;
    optional_repair_time_s: NullableNumber;
    fast_repairs_used: number | null;
    fast_repairs_remaining: number | null;
  } | null;
  track_map: {
    player_car_index: number | null;
    cars: TrackMapCar[];
  } | null;
};
