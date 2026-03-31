export type BootstrapConfig = {
  localBackendBaseUrl: string;
  localBackendWebSocketUrl: string;
  environment: "development" | "production";
};

export async function getBootstrapConfig(): Promise<BootstrapConfig> {
  return {
    localBackendBaseUrl: "http://127.0.0.1:8000",
    localBackendWebSocketUrl: "ws://127.0.0.1:8000/ws",
    environment: "development"
  };
}
