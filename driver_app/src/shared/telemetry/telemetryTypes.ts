export type TelemetrySnapshot = {
  source?: string | null;
  session_phase?: string | null;
  current_lap?: number | null;
  vehicle_speed_kph?: number | null;
  gear?: number | null;
  throttle?: number | null;
  brake?: number | null;
  clutch?: number | null;
  steering_angle_deg?: number | null;
};
