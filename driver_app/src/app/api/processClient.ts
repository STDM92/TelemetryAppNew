import { invoke } from "@tauri-apps/api/core";
import type { SidecarProcessState } from "../../types/api";

export async function getSidecarProcessState(): Promise<SidecarProcessState> {
  return invoke<SidecarProcessState>("get_sidecar_process_state");
}

export async function startSidecar(): Promise<SidecarProcessState> {
  return invoke<SidecarProcessState>("start_sidecar");
}

export async function stopSidecar(): Promise<SidecarProcessState> {
  return invoke<SidecarProcessState>("stop_sidecar");
}

export async function restartSidecar(): Promise<SidecarProcessState> {
  return invoke<SidecarProcessState>("restart_sidecar");
}
