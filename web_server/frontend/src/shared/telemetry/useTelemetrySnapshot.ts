import { useEffect, useState } from "react";
import type { TelemetrySnapshot } from "./telemetryTypes";

export function useTelemetrySnapshot(): {
  snapshot: TelemetrySnapshot | null;
  isConnected: boolean;
} {
  const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    setIsConnected(false);
    setSnapshot(null);
  }, []);

  return {
    snapshot,
    isConnected,
  };
}
