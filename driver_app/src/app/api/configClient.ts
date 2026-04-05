import { invoke } from "@tauri-apps/api/core";
import type { AppConfig } from "../../types/api";

export async function getAppConfig(): Promise<AppConfig> {
  return invoke<AppConfig>("get_app_config");
}

export async function updateAppConfig(config: AppConfig): Promise<AppConfig> {
  return invoke<AppConfig>("update_app_config", {
    update: config,
  });
}
