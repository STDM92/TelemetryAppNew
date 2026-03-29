/**
 * @typedef {Object} Vector3
 * @property {number|null} x
 * @property {number|null} y
 * @property {number|null} z
 */

/**
 * @typedef {Object} Orientation
 * @property {number|null} yaw_rad
 * @property {number|null} pitch_rad
 * @property {number|null} roll_rad
 */

/**
 * @typedef {Object} AngularRate
 * @property {number|null} yaw_rad_s
 * @property {number|null} pitch_rad_s
 * @property {number|null} roll_rad_s
 */

/**
 * @typedef {Object} TireBandTemperature
 * @property {number|null} left_c
 * @property {number|null} center_c
 * @property {number|null} right_c
 */

/**
 * @typedef {Object} TireBandWear
 * @property {number|null} left_ratio
 * @property {number|null} center_ratio
 * @property {number|null} right_ratio
 */

/**
 * @typedef {Object} TireCornerData
 * @property {number|null} cold_pressure_kpa
 * @property {number|null} live_pressure_kpa
 * @property {TireBandTemperature|null} carcass_temp_c
 * @property {TireBandTemperature|null} surface_temp_c
 * @property {TireBandWear|null} wear_ratio
 * @property {number|null} tread_remaining_ratio
 * @property {number|null} compound_code
 * @property {number|null} odometer_m
 */

/**
 * @typedef {Object} TireSetData
 * @property {TireCornerData|null} left_front
 * @property {TireCornerData|null} right_front
 * @property {TireCornerData|null} left_rear
 * @property {TireCornerData|null} right_rear
 */

/**
 * @typedef {Object} BrakeCornerData
 * @property {number|null} line_pressure_bar
 */

/**
 * @typedef {Object} BrakeSystemData
 * @property {number|null} brake_bias_ratio
 * @property {number|null} abs_setting
 * @property {boolean|null} abs_active
 * @property {BrakeCornerData|null} left_front
 * @property {BrakeCornerData|null} right_front
 * @property {BrakeCornerData|null} left_rear
 * @property {BrakeCornerData|null} right_rear
 */

/**
 * @typedef {Object} SuspensionCornerData
 * @property {number|null} ride_height_mm
 * @property {number|null} damper_position_mm
 * @property {number|null} damper_velocity_mm_s
 * @property {number|null} suspension_deflection_mm
 * @property {number|null} wheel_load_n
 * @property {number|null} wheel_speed_kph
 */

/**
 * @typedef {Object} SuspensionData
 * @property {SuspensionCornerData|null} left_front
 * @property {SuspensionCornerData|null} right_front
 * @property {SuspensionCornerData|null} left_rear
 * @property {SuspensionCornerData|null} right_rear
 */

/**
 * @typedef {Object} DriverInputs
 * @property {number|null} throttle_ratio
 * @property {number|null} brake_ratio
 * @property {number|null} clutch_ratio
 * @property {number|null} steering_angle_rad
 * @property {number|null} handbrake_ratio
 */

/**
 * @typedef {Object} SessionInfo
 * @property {string|null} simulator_name
 * @property {string|null} track_name
 * @property {string|null} session_type
 * @property {string|null} session_phase
 * @property {string|null} session_flags
 * @property {number|null} session_time_s
 * @property {number|null} session_time_remaining_s
 * @property {number|null} session_laps_total
 * @property {number|null} session_laps_remaining
 * @property {boolean|null} is_on_track
 * @property {boolean|null} is_on_pit_road
 * @property {boolean|null} is_in_garage
 */

/**
 * @typedef {Object} LapData
 * @property {number|null} current_lap
 * @property {number|null} completed_laps
 * @property {number|null} lap_distance_m
 * @property {number|null} lap_distance_ratio
 * @property {number|null} current_lap_time_s
 * @property {number|null} last_lap_time_s
 * @property {number|null} best_lap_time_s
 * @property {number|null} optimal_lap_time_s
 * @property {number|null} delta_to_best_lap_s
 * @property {number|null} delta_to_optimal_lap_s
 * @property {number|null} delta_to_session_best_lap_s
 * @property {boolean|null} delta_to_best_lap_valid
 * @property {boolean|null} delta_to_optimal_lap_valid
 * @property {boolean|null} delta_to_session_best_lap_valid
 */

/**
 * @typedef {Object} RacePosition
 * @property {number|null} overall_position
 * @property {number|null} class_position
 * @property {number|null} car_index
 * @property {number|null} gap_ahead_s
 * @property {number|null} gap_behind_s
 * @property {number|null} distance_ahead_m
 * @property {number|null} distance_behind_m
 */

/**
 * @typedef {Object} PowertrainData
 * @property {number|null} gear
 * @property {number|null} engine_speed_rpm
 * @property {number|null} vehicle_speed_kph
 * @property {number|null} fuel_remaining_l
 * @property {number|null} fuel_remaining_ratio
 * @property {number|null} fuel_use_per_hour
 * @property {number|null} oil_temp_c
 * @property {number|null} oil_pressure_bar
 * @property {number|null} water_temp_c
 * @property {number|null} water_level_l
 * @property {number|null} fuel_pressure_bar
 * @property {number|null} voltage_v
 */

/**
 * @typedef {Object} VehicleDynamics
 * @property {Vector3|null} velocity_mps
 * @property {Vector3|null} acceleration_mps2
 * @property {Orientation|null} orientation
 * @property {AngularRate|null} angular_rate
 * @property {number|null} steering_torque_nm
 * @property {number|null} steering_torque_pct
 * @property {number|null} lateral_accel_g
 * @property {number|null} longitudinal_accel_g
 * @property {number|null} vertical_accel_g
 */

/**
 * @typedef {Object} EnvironmentData
 * @property {number|null} air_temp_c
 * @property {number|null} track_temp_c
 * @property {number|null} relative_humidity_ratio
 * @property {number|null} air_pressure_pa
 * @property {number|null} air_density_kg_m3
 * @property {number|null} wind_speed_mps
 * @property {number|null} wind_direction_rad
 * @property {string|null} sky_condition
 * @property {number|null} precipitation_ratio
 * @property {number|null} fog_ratio
 * @property {string|null} surface_wetness
 * @property {boolean|null} wet_tires_allowed
 */

/**
 * @typedef {Object} PitData
 * @property {string|null} pit_service_status
 * @property {boolean|null} pit_stop_active
 * @property {number|null} required_repair_time_s
 * @property {number|null} optional_repair_time_s
 * @property {number|null} fast_repairs_used
 * @property {number|null} fast_repairs_remaining
 */

/**
 * @typedef {Object} TrackCarMarker
 * @property {number|null} car_index
 * @property {number|null} overall_position
 * @property {number|null} class_position
 * @property {number|null} lap_distance_ratio
 * @property {number|null} estimated_lap_time_to_marker_s
 * @property {boolean|null} is_on_pit_road
 * @property {string|null} track_location
 * @property {string|null} track_surface
 * @property {number|null} last_lap_time_s
 * @property {number|null} best_lap_time_s
 */

/**
 * @typedef {Object} TrackMapData
 * @property {number|null} player_car_index
 * @property {TrackCarMarker[]|null} cars
 */

/**
 * @typedef {Object} UnifiedSnapshot
 * @property {string} source
 * @property {number} timestamp
 * @property {SessionInfo|null} session
 * @property {LapData|null} lap
 * @property {RacePosition|null} race
 * @property {DriverInputs|null} inputs
 * @property {PowertrainData|null} powertrain
 * @property {TireSetData|null} tires
 * @property {BrakeSystemData|null} brakes
 * @property {SuspensionData|null} suspension
 * @property {VehicleDynamics|null} dynamics
 * @property {EnvironmentData|null} environment
 * @property {PitData|null} pit
 * @property {TrackMapData|null} track_map
 */