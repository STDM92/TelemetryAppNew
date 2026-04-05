export type SidecarProcessState = {
  status: string;
  pid?: number | null;
  exitCode?: number | null;
  lastError?: string | null;
};

export async function getSidecarProcessState(): Promise<SidecarProcessState> {
  return {
    status: "unknown",
    pid: null,
    exitCode: null,
    lastError: null,
  };
}
