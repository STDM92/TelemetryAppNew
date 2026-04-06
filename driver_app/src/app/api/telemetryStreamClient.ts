export type TelemetrySnapshotRecord = Record<string, unknown> | null;

type TelemetryStreamCallbacks = {
    onOpen?: () => void;
    onSnapshot?: (snapshot: TelemetrySnapshotRecord) => void;
    onClose?: () => void;
    onError?: (error: Event) => void;
};

const RECONNECT_DELAY_MS = 1000;

export function connectTelemetryStream(
    websocketUrl: string,
    callbacks: TelemetryStreamCallbacks
): () => void {
    let socket: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let closedByCaller = false;

    function clearReconnectTimer(): void {
        if (reconnectTimer != null) {
            window.clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
    }

    function scheduleReconnect(): void {
        if (closedByCaller || reconnectTimer != null) {
            return;
        }

        reconnectTimer = window.setTimeout(() => {
            reconnectTimer = null;
            connect();
        }, RECONNECT_DELAY_MS);
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

    function connect(): void {
        clearReconnectTimer();
        closeCurrentSocket();

        socket = new WebSocket(websocketUrl);

        socket.addEventListener("open", () => {
            callbacks.onOpen?.();
        });

        socket.addEventListener("message", (event) => {
            try {
                const parsed = JSON.parse(event.data) as unknown;

                if (parsed === null || (typeof parsed === "object" && !Array.isArray(parsed))) {
                    callbacks.onSnapshot?.(parsed as TelemetrySnapshotRecord);
                }
            } catch {
                // Ignore malformed frames.
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