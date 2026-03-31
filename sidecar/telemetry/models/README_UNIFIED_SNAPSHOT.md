# Unified Telemetry Snapshot

`UnifiedTelemetrySnapshot` is the normalized telemetry contract shared by the app.

It is designed to be:
- simulator-agnostic
- partially populated
- safe for incremental rollout
- explicit about units

Receivers may leave any unsupported field as `None`.

## Top-Level Structure

- `source`: telemetry source name, e.g. `"iracing"`
- `timestamp`: capture timestamp in Unix seconds
- `session`
- `lap`
- `race`
- `inputs`
- `powertrain`
- `tires`
- `brakes`
- `suspension`
- `dynamics`
- `environment`
- `pit`
- `track_map`

---

## Canonical Units

These are the required units receivers must write into the snapshot.

| Domain | Field Type | Canonical Unit |
|---|---|---|
| Speed | vehicle speed, wheel speed | `kph` |
| Distance | track distance, tire odometer | `m` |
| Time | lap time, deltas, gaps, session time | `s` |
| Temperature | air, track, tire, oil, water, brake | `C` |
| Pressure | tire pressure | `kPa` |
| Pressure | brake line / oil / fuel | `bar` |
| Fuel volume | fuel remaining, water level where volumetric | `l` |
| Fuel rate | fuel use | source-specific semantic value, preserve source unit in field name or documentation |
| Angle | steering, yaw, pitch, roll, wind direction | `rad` |
| Angular rate | yaw/pitch/roll rate | `rad/s` |
| Linear acceleration | x/y/z acceleration | `m/s^2` |
| Gravity-normalized acceleration | lat/long/vert accel variants | `g` |
| Voltage | electrical system | `V` |
| Ride height / damper position / suspension deflection | chassis/suspension distances | `mm` |
| Damper velocity | suspension speed | `mm/s` |
| Wheel load | tire normal load | `N` |
| Ratios | throttle, brake, clutch, humidity, precipitation, wear | `0.0 .. 1.0` when possible |

## Ratio Convention

For ratio-like fields, receivers should prefer a `0.0 .. 1.0` representation if the source already uses that format.

If a source exposes true percentages as `0 .. 100`, convert them to `0.0 .. 1.0` before writing the snapshot.

Examples:
- throttle: `0.0 .. 1.0`
- brake: `0.0 .. 1.0`
- tire wear / tread remaining: `0.0 .. 1.0`
- humidity: ideally `0.0 .. 1.0`

---

## Field Groups

## `session`

General session state.

Important fields:
- `simulator_name`
- `track_name`
- `session_type`
- `session_phase`
- `session_flags`
- `session_time_s`
- `session_time_remaining_s`
- `session_laps_total`
- `session_laps_remaining`
- `is_on_track`
- `is_on_pit_road`
- `is_in_garage`

## `lap`

Player lap progress and time deltas.

Important fields:
- `current_lap`
- `completed_laps`
- `lap_distance_m`
- `lap_distance_ratio`
- `current_lap_time_s`
- `last_lap_time_s`
- `best_lap_time_s`
- `optimal_lap_time_s`
- `delta_to_best_lap_s`
- `delta_to_optimal_lap_s`
- `delta_to_session_best_lap_s`
- validity flags

## `race`

Player race position and local traffic context.

Important fields:
- `overall_position`
- `class_position`
- `car_index`
- `gap_ahead_s`
- `gap_behind_s`
- `distance_ahead_m`
- `distance_behind_m`

## `inputs`

Driver controls.

Important fields:
- `throttle_ratio`
- `brake_ratio`
- `clutch_ratio`
- `steering_angle_rad`
- `handbrake_ratio`

## `powertrain`

Core car operation values.

Important fields:
- `gear`
- `engine_speed_rpm`
- `vehicle_speed_kph`
- `fuel_remaining_l`
- `fuel_remaining_ratio`
- `fuel_use_per_hour`
- `oil_temp_c`
- `oil_pressure_bar`
- `water_temp_c`
- `fuel_pressure_bar`
- `voltage_v`

## `tires`

Per-corner tire information.

Each corner contains:
- `cold_pressure_kpa`
- `live_pressure_kpa`
- `carcass_temp_c.left_c / center_c / right_c`
- `surface_temp_c.left_c / center_c / right_c`
- `wear_ratio.left_ratio / center_ratio / right_ratio`
- `tread_remaining_ratio`
- `compound_code`
- `odometer_m`

## `brakes`

Brake system values.

Important fields:
- `brake_bias_ratio`
- `abs_setting`
- `abs_active`
- per-corner `line_pressure_bar`
- optional `disc_temp_c`

## `suspension`

Per-corner suspension and ride data.

Each corner may contain:
- `ride_height_mm`
- `damper_position_mm`
- `damper_velocity_mm_s`
- `suspension_deflection_mm`
- `wheel_load_n`
- `wheel_speed_kph`

## `dynamics`

Vehicle motion and body state.

Important fields:
- `velocity_mps.x/y/z`
- `acceleration_mps2.x/y/z`
- `orientation.yaw_rad / pitch_rad / roll_rad`
- `angular_rate.yaw_rad_s / pitch_rad_s / roll_rad_s`
- `steering_torque_nm`
- `steering_torque_pct`
- `lateral_accel_g`
- `longitudinal_accel_g`
- `vertical_accel_g`

## `environment`

Weather and track conditions.

Important fields:
- `air_temp_c`
- `track_temp_c`
- `relative_humidity_ratio`
- `air_pressure_pa`
- `air_density_kg_m3`
- `wind_speed_mps`
- `wind_direction_rad`
- `sky_condition`
- `precipitation_ratio`
- `fog_ratio`
- `surface_wetness`
- `wet_tires_allowed`

## `pit`

Pit stop and repair state.

Important fields:
- `pit_service_status`
- `pit_stop_active`
- `required_repair_time_s`
- `optional_repair_time_s`
- `fast_repairs_used`
- `fast_repairs_remaining`

## `track_map`

Opponent and player position around the lap.

- `player_car_index`
- `cars: tuple[TrackCarMarker, ...]`

Each `TrackCarMarker` may contain:
- `car_index`
- `overall_position`
- `class_position`
- `lap_distance_ratio`
- `estimated_lap_time_to_marker_s`
- `is_on_pit_road`
- `track_location`
- `track_surface`
- `last_lap_time_s`
- `best_lap_time_s`

---

## Snapshot Semantics

### Missing Data

`None` means:
- the source does not expose the field,
- the receiver has not wired it yet,
- the value is temporarily unavailable,
- or the source returned an invalid/sentinel value.

### Zero Is Not Missing

Do not use `0` as a substitute for missing data.

Examples:
- `0.0 throttle` means no throttle
- `None throttle` means unavailable

## Snapshot Ownership

Snapshots are transferable data copies.

A receiver may construct and populate a snapshot freely.
The administrator applies snapshots into the internal unified state.
When a caller requests the latest telemetry, the administrator returns a new snapshot copy.

Callers may mutate the returned snapshot without affecting the authoritative internal state.

## Receiver Responsibilities Summary

A receiver must:
- convert to canonical units
- map raw enums/bitfields into readable values
- keep unsupported fields as `None`
- avoid leaking source-specific names into the shared model

