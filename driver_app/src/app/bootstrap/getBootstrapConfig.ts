import { invoke } from "@tauri-apps/api/core";
import type { BootstrapConfig } from "./bootstrapTypes";

export async function getBootstrapConfig(): Promise<BootstrapConfig> {
  return await invoke<BootstrapConfig>("get_bootstrap_config");
}