import { invoke } from "@tauri-apps/api/core";
import type { BootstrapConfig } from "../../types/api";

export async function getBootstrapConfig(): Promise<BootstrapConfig> {
  return invoke<BootstrapConfig>("get_bootstrap_config");
}

