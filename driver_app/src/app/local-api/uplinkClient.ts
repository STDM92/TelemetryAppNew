export type UplinkStatus = {
  enabled: boolean;
  remote_state: string;
  active_session_key?: string | null;
  engineer_url?: string | null;
  last_error?: string | null;
};

export async function fetchUplinkStatus(baseUrl: string): Promise<UplinkStatus> {
  const response = await fetch(`${baseUrl}/api/uplink`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Failed to fetch uplink status: ${response.status}`);
  }

  return (await response.json()) as UplinkStatus;
}
