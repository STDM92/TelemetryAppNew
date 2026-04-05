import { invoke } from "@tauri-apps/api/core";

export type SidecarProcessState = {
  status: "not_running" | "running" | "exited" | string;
  pid?: number | null;
  exitCode?: number | null;
  lastError?: string | null;
  lastExitReason?: string | null;
  stdoutTail?: string[];
  stderrTail?: string[];
};

type RawSidecarProcessState = {
  status: string;
  pid?: number | null;
  exit_code?: number | null;
  last_error?: string | null;
  last_exit_reason?: string | null;
  stdout_tail?: string[];
  stderr_tail?: string[];
};

function mapProcessState(raw: RawSidecarProcessState): SidecarProcessState {
  return {
    status: raw.status,
    pid: raw.pid ?? null,
    exitCode: raw.exit_code ?? null,
    lastError: raw.last_error ?? null,
    lastExitReason: raw.last_exit_reason ?? null,
    stdoutTail: raw.stdout_tail ?? [],
    stderrTail: raw.stderr_tail ?? [],
  };
}

export async function getSidecarProcessState(): Promise<SidecarProcessState> {
  const raw = await invoke<RawSidecarProcessState>("get_sidecar_process_state");
  return mapProcessState(raw);
}

export async function startSidecar(): Promise<SidecarProcessState> {
  const raw = await invoke<RawSidecarProcessState>("start_sidecar");
  return mapProcessState(raw);
}

export async function stopSidecar(): Promise<SidecarProcessState> {
  const raw = await invoke<RawSidecarProcessState>("stop_sidecar");
  return mapProcessState(raw);
}

export async function restartSidecar(): Promise<SidecarProcessState> {
  const raw = await invoke<RawSidecarProcessState>("restart_sidecar");
  return mapProcessState(raw);
}