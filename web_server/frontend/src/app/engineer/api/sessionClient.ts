import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";

export type SessionStateResponse = {
  session: {
    session_key: string;
    producer_attached: boolean;
    engineer_count: number;
    latest_snapshot_received_at?: string | null;
  };
  latest_snapshot: TelemetrySnapshot | null;
};

export async function fetchSessionState(
  serverBaseUrl: string,
  sessionKey: string,
): Promise<SessionStateResponse> {
  const response = await fetch(
    `${serverBaseUrl.replace(/\/$/, "")}/api/state/${encodeURIComponent(sessionKey)}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch session state: ${response.status}`);
  }

  return (await response.json()) as SessionStateResponse;
}
