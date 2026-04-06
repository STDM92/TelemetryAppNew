export type RuntimeStatus = {
  status: string;
  last_error?: string | null;
};

export async function fetchRuntimeStatus(baseUrl: string): Promise<RuntimeStatus> {
  const response = await fetch(`${baseUrl}/health`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Failed to fetch runtime status: ${response.status}`);
  }

  return (await response.json()) as RuntimeStatus;
}
