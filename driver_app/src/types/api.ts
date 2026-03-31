export type BootstrapConfig = {
  backendBaseUrl: string;
  backendWebsocketUrl: string;
  mode: "development" | "tauri";
};

export type RuntimeStatusResponse = {
  status: string;
  last_error: string | null;
};

export type TelemetryState = Record<string, unknown> | null;

export type SidecarProcessState = {
  status: "not_running" | "running" | "exited";
  pid: number | null;
  exitCode: number | null;
  lastError: string | null;

