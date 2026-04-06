import type { TelemetrySnapshot } from "../../shared/telemetry/telemetryTypes";

export async function fetchCurrentState(baseUrl: string): Promise<TelemetrySnapshot | null> {
  const response = await fetch(`${baseUrl}/api/state`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Failed to fetch current state: ${response.status}`);
  }

  return (await response.json()) as TelemetrySnapshot | null;
}
