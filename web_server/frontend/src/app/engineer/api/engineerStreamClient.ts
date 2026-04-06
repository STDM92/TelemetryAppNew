import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";

export type EngineerStreamCallbacks = {
  onOpen?: () => void;
  onSnapshot?: (snapshot: TelemetrySnapshot) => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  onInfo?: (payload: Record<string, unknown>) => void;
};

const RECONNECT_DELAY_MS = 1000;

function toWebSocketBaseUrl(serverBaseUrl: string): string {
  return serverBaseUrl
    .replace(/^http:\/\//i, "ws://")
    .replace(/^https:\/\//i, "wss://")
    .replace(/\/$/, "");
}

export function connectEngineerStream(
  serverBaseUrl: string,
  sessionKey: string,
  callbacks: EngineerStreamCallbacks,
): () => void {
  let socket: WebSocket | null = null;
  let reconnectTimer: number | null = null;
  let closedByCaller = false;

  function clearReconnectTimer(): void {
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  }

  function closeCurrentSocket(): void {
    if (!socket) {
      return;
    }

    if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
      socket.close();
    }

    socket = null;
  }

  function scheduleReconnect(): void {
    if (closedByCaller || reconnectTimer !== null) {
      return;
    }

    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, RECONNECT_DELAY_MS);
  }

  function connect(): void {
    clearReconnectTimer();
    closeCurrentSocket();

    const wsUrl =
      `${toWebSocketBaseUrl(serverBaseUrl)}/ws?session_key=${encodeURIComponent(sessionKey)}&role=engineer`;

    socket = new WebSocket(wsUrl);

    socket.addEventListener("open", () => {
      callbacks.onOpen?.();
    });

    socket.addEventListener("message", (event) => {
      try {
        const parsed = JSON.parse(event.data) as {
          type?: string;
          payload?: Record<string, unknown>;
        };

        if (parsed?.type === "telemetry_snapshot" && parsed.payload && typeof parsed.payload === "object") {
          callbacks.onSnapshot?.(parsed.payload as TelemetrySnapshot);
          return;
        }

        if (parsed?.type === "server_info" && parsed.payload && typeof parsed.payload === "object") {
          callbacks.onInfo?.(parsed.payload);
        }
      } catch {
        // ignore malformed frames
      }
    });

    socket.addEventListener("error", (event) => {
      callbacks.onError?.(event);
    });

    socket.addEventListener("close", () => {
      callbacks.onClose?.();
      socket = null;
      scheduleReconnect();
    });
  }

  connect();

  return () => {
    closedByCaller = true;
    clearReconnectTimer();
    closeCurrentSocket();
  };
}
