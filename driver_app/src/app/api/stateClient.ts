import type { TelemetryState } from "../../types/api";

export async function fetchState(baseUrl: string): Promise<TelemetryState> {
  const response = await fetch(`${baseUrl}/api/state`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`State request failed: ${response.status}`);
  }
  return response.json();
}
