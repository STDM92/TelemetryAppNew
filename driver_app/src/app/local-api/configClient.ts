import { getBootstrapConfig } from "../bootstrap/getBootstrapConfig";

export async function getResolvedBackendBaseUrl(): Promise<string> {
  const config = await getBootstrapConfig();
  return config.backendBaseUrl;
}
