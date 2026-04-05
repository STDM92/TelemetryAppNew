import type { RuntimeStatusResponse } from "../../types/api";

export async function fetchRuntimeStatus(baseUrl: string): Promise<RuntimeStatusResponse> {
  const response = await fetch(`${baseUrl}/status`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Status request failed: ${response.status}`);
  }
  return response.json();
}
