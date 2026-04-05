import type { BootstrapConfig } from "./bootstrapTypes";

declare global {
  interface Window {
    __APP_CONFIG__?: Partial<BootstrapConfig>;
  }
}

export async function getBootstrapConfig(): Promise<BootstrapConfig> {
  const injected = window.__APP_CONFIG__ ?? {};

  return {
    backendBaseUrl: injected.backendBaseUrl ?? "http://127.0.0.1:8000",
    backendWebSocketUrl: injected.backendWebSocketUrl ?? "ws://127.0.0.1:8000/ws",
    mode: injected.mode ?? "live",
  };
}
