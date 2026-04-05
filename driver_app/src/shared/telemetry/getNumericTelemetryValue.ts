import type { TelemetrySnapshot } from "./telemetryTypes";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function getTelemetryValueAtPath(snapshot: TelemetrySnapshot | null, path: string): unknown {
  if (!snapshot || !path) {
    return null;
  }

  const segments = path.split(".").filter(Boolean);
  let current: unknown = snapshot;

  for (const segment of segments) {
    if (!isRecord(current) || !(segment in current)) {
      return null;
    }

    current = current[segment];
  }

  return current;
}

export function getNumericTelemetryValue(snapshot: TelemetrySnapshot | null, path: string): number | null {
  const value = getTelemetryValueAtPath(snapshot, path);

  if (typeof value !== "number" || Number.isNaN(value)) {
    return null;
  }

  return value;
}
