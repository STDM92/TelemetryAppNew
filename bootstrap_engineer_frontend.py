from __future__ import annotations

import shutil
from pathlib import Path
from textwrap import dedent

ROOT = Path.cwd()
DRIVER_APP = ROOT / "driver_app"
WEB_FRONTEND = ROOT / "web_server" / "frontend"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def patch_widget_grid(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    content = content.replace("  snapshotTick: number;\n", "  snapshotTick?: number;\n")
    content = content.replace("    snapshotTick,\n", "    snapshotTick: snapshotTick ?? 0,\n")
    path.write_text(content, encoding="utf-8")


def main() -> int:
    if not DRIVER_APP.exists():
        raise SystemExit("Run this from the repo root so ./driver_app exists.")

    (WEB_FRONTEND / "src").mkdir(parents=True, exist_ok=True)

    # Copy reusable UI files from driver_app.
    copy_tree(DRIVER_APP / "src" / "shared", WEB_FRONTEND / "src" / "shared")
    copy_tree(DRIVER_APP / "src" / "app" / "dashboard", WEB_FRONTEND / "src" / "app" / "dashboard")

    # Copy base styling from driver_app, then append engineer-specific styles.
    styles_src = DRIVER_APP / "src" / "styles" / "app.css"
    styles_dst = WEB_FRONTEND / "src" / "styles" / "app.css"
    write_text(styles_dst, styles_src.read_text(encoding="utf-8") + "\n" + ENGINEER_EXTRA_CSS)

    # Add type-only local-api status shape expected by shared/dashboard code.
    write_text(WEB_FRONTEND / "src" / "app" / "local-api" / "statusClient.ts", STATUS_CLIENT_TS)

    # Fix the copied WidgetGrid to allow views that do not pass snapshotTick.
    patch_widget_grid(WEB_FRONTEND / "src" / "shared" / "dashboard" / "WidgetGrid.tsx")

    # Write engineer frontend files.
    write_text(WEB_FRONTEND / "package.json", PACKAGE_JSON)
    write_text(WEB_FRONTEND / "tsconfig.json", TSCONFIG_JSON)
    write_text(WEB_FRONTEND / "vite.config.ts", VITE_CONFIG_TS)
    write_text(WEB_FRONTEND / "index.html", INDEX_HTML)
    write_text(WEB_FRONTEND / "src" / "main.tsx", MAIN_TSX)
    write_text(WEB_FRONTEND / "src" / "App.tsx", APP_TSX)
    write_text(WEB_FRONTEND / "src" / "engineer" / "api" / "engineerTelemetryStreamClient.ts", ENGINEER_WS_CLIENT_TS)
    write_text(WEB_FRONTEND / "src" / "engineer" / "EngineerApp.tsx", ENGINEER_APP_TSX)

    print("Engineer frontend scaffolded at web_server/frontend")
    print("Next steps:")
    print("  cd web_server/frontend")
    print("  npm install")
    print("  npm run dev")
    return 0


PACKAGE_JSON = dedent("""\
{
  "name": "telemetry-engineer-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 5174",
    "build": "tsc && vite build",
    "preview": "vite preview --host 0.0.0.0 --port 4174"
  },
  "dependencies": {
    "react": "^19.2.4",
    "react-dom": "^19.2.4"
  },
  "devDependencies": {
    "@types/react": "^19.2.14",
    "@types/react-dom": "^19.2.3",
    "typescript": "^5.6.2",
    "vite": "^8.0.3"
  }
}
""")

TSCONFIG_JSON = dedent("""\
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": false,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
""")

VITE_CONFIG_TS = dedent("""\
import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "0.0.0.0",
    port: 5174,
  },
  preview: {
    host: "0.0.0.0",
    port: 4174,
  },
});
""")

INDEX_HTML = dedent("""\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Telemetry Engineer Frontend</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""")

MAIN_TSX = dedent("""\
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/app.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
""")

APP_TSX = dedent("""\
import React from "react";
import { EngineerApp } from "./engineer/EngineerApp";

export default function App() {
  return <EngineerApp />;
}
""")

STATUS_CLIENT_TS = dedent("""\
export type BackendStatus = {
  status: "created" | "running" | "stopped" | "failed" | string;
  last_error?: string | null;
  source_attachment_state?: "none" | "waiting" | "attached" | string | null;
  stream_state?: "failed" | "idle" | "stale" | "streaming" | string | null;
  has_received_snapshot?: boolean;
  last_snapshot_at?: number | null;
  sim?: string | null;
  source_kind?: string | null;
  source_display_name?: string | null;
};
""")

ENGINEER_WS_CLIENT_TS = dedent("""\
export type EngineerStreamCallbacks = {
  onOpen?: () => void;
  onSnapshot?: (snapshot: Record<string, unknown>) => void;
  onInfo?: (payload: Record<string, unknown>) => void;
  onServerError?: (payload: Record<string, unknown>) => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
};

const RECONNECT_DELAY_MS = 1000;

function toWebSocketUrl(serverBaseUrl: string, sessionKey: string): string {
  const normalizedBase = serverBaseUrl.replace(/\\/$/, "");
  const url = new URL(normalizedBase);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws";
  url.search = `session_key=${encodeURIComponent(sessionKey)}&role=engineer`;
  return url.toString();
}

export function connectEngineerTelemetryStream(
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

  function scheduleReconnect(): void {
    if (closedByCaller || reconnectTimer !== null) {
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

    socket = new WebSocket(toWebSocketUrl(serverBaseUrl, sessionKey));

    socket.addEventListener("open", () => {
      callbacks.onOpen?.();
    });

    socket.addEventListener("message", (event) => {
      try {
        const parsed = JSON.parse(event.data) as {
          type?: string;
          payload?: Record<string, unknown>;
        };

        if (parsed.type === "telemetry_snapshot" && parsed.payload && typeof parsed.payload === "object") {
          callbacks.onSnapshot?.(parsed.payload);
          return;
        }

        if (parsed.type === "server_info" && parsed.payload && typeof parsed.payload === "object") {
          callbacks.onInfo?.(parsed.payload);
          return;
        }

        if (parsed.type === "server_error" && parsed.payload && typeof parsed.payload === "object") {
          callbacks.onServerError?.(parsed.payload);
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
""")

ENGINEER_APP_TSX = dedent("""\
import React, { useEffect, useMemo, useState } from "react";
import { DashboardShell } from "../app/dashboard/DashboardShell";
import type { BackendStatus } from "../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../shared/telemetry/telemetryTypes";
import { connectEngineerTelemetryStream } from "./api/engineerTelemetryStreamClient";

function getInitialValue(name: string, fallback: string): string {
  const value = new URLSearchParams(window.location.search).get(name);
  return value && value.trim().length > 0 ? value.trim() : fallback;
}

function parseBooleanParam(name: string): boolean {
  const value = new URLSearchParams(window.location.search).get(name);
  return value === "1" || value === "true";
}

function createBackendStatus(
  connectionState: "idle" | "connecting" | "streaming" | "failed",
  snapshot: TelemetrySnapshot | null,
  lastError: string | null,
): BackendStatus {
  switch (connectionState) {
    case "streaming":
      return {
        status: "running",
        source_attachment_state: "attached",
        stream_state: "streaming",
        has_received_snapshot: snapshot !== null,
        last_snapshot_at: snapshot?.timestamp ?? null,
        sim: snapshot?.session?.simulator_name ?? "Remote session",
        source_kind: "engineer-session",
        source_display_name: "Remote Session",
        last_error: lastError,
      };
    case "connecting":
      return {
        status: "created",
        source_attachment_state: "waiting",
        stream_state: "idle",
        has_received_snapshot: snapshot !== null,
        last_snapshot_at: snapshot?.timestamp ?? null,
        sim: snapshot?.session?.simulator_name ?? null,
        source_kind: "engineer-session",
        source_display_name: "Connecting…",
        last_error: lastError,
      };
    case "failed":
      return {
        status: "failed",
        source_attachment_state: "none",
        stream_state: "failed",
        has_received_snapshot: snapshot !== null,
        last_snapshot_at: snapshot?.timestamp ?? null,
        sim: snapshot?.session?.simulator_name ?? null,
        source_kind: "engineer-session",
        source_display_name: "Disconnected",
        last_error: lastError,
      };
    case "idle":
    default:
      return {
        status: "created",
        source_attachment_state: "none",
        stream_state: "idle",
        has_received_snapshot: snapshot !== null,
        last_snapshot_at: snapshot?.timestamp ?? null,
        sim: snapshot?.session?.simulator_name ?? null,
        source_kind: "engineer-session",
        source_display_name: "Not connected",
        last_error: lastError,
      };
  }
}

export function EngineerApp() {
  const [serverBaseUrl, setServerBaseUrl] = useState(() => getInitialValue("server", "http://127.0.0.1:8080"));
  const [sessionKeyInput, setSessionKeyInput] = useState(() => getInitialValue("session", ""));
  const [activeSessionKey, setActiveSessionKey] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
  const [snapshotTick, setSnapshotTick] = useState(0);
  const [frameCount, setFrameCount] = useState(0);
  const [connectionState, setConnectionState] = useState<"idle" | "connecting" | "streaming" | "failed">("idle");
  const [lastInfo, setLastInfo] = useState<string>("Waiting to connect.");
  const [lastError, setLastError] = useState<string | null>(null);

  useEffect(() => {
    if (!parseBooleanParam("autoconnect")) {
      return;
    }

    const trimmed = sessionKeyInput.trim().toUpperCase();
    if (!trimmed) {
      return;
    }

    setActiveSessionKey(trimmed);
  }, []);

  useEffect(() => {
    if (!activeSessionKey) {
      return;
    }

    setConnectionState("connecting");
    setLastError(null);
    setLastInfo(`Connecting to session ${activeSessionKey}…`);

    const disconnect = connectEngineerTelemetryStream(serverBaseUrl, activeSessionKey, {
      onOpen: () => {
        setConnectionState((current) => (current === "streaming" ? current : "connecting"));
      },
      onSnapshot: (nextSnapshot) => {
        setSnapshot(nextSnapshot as TelemetrySnapshot);
        setSnapshotTick((value) => value + 1);
        setFrameCount((value) => value + 1);
        setConnectionState("streaming");
        setLastError(null);
      },
      onInfo: (payload) => {
        const event = typeof payload.event === "string" ? payload.event : "connected";
        setLastInfo(`${event} (${activeSessionKey})`);
      },
      onServerError: (payload) => {
        const event = typeof payload.event === "string" ? payload.event : "server_error";
        setLastError(event);
        setConnectionState("failed");
      },
      onError: () => {
        setLastError("WebSocket error");
      },
      onClose: () => {
        setConnectionState((current) => (current === "idle" ? current : "failed"));
      },
    });

    return () => {
      disconnect();
    };
  }, [serverBaseUrl, activeSessionKey]);

  const backendStatus = useMemo(
    () => createBackendStatus(connectionState, snapshot, lastError),
    [connectionState, snapshot, lastError],
  );

  function handleConnect(): void {
    const trimmed = sessionKeyInput.trim().toUpperCase();
    if (!trimmed) {
      setLastError("Session key is required.");
      return;
    }

    setSnapshot(null);
    setSnapshotTick(0);
    setFrameCount(0);
    setActiveSessionKey(trimmed);
  }

  function handleDisconnect(): void {
    setActiveSessionKey(null);
    setConnectionState("idle");
    setLastInfo("Disconnected.");
  }

  return (
    <div className="engineer-screen">
      <section className="engineer-control-bar">
        <div className="engineer-control-bar__fields">
          <label className="engineer-field">
            <span className="engineer-field__label">Server</span>
            <input
              className="engineer-field__input"
              value={serverBaseUrl}
              onChange={(event) => setServerBaseUrl(event.target.value)}
              placeholder="http://127.0.0.1:8080"
            />
          </label>

          <label className="engineer-field">
            <span className="engineer-field__label">Session Key</span>
            <input
              className="engineer-field__input engineer-field__input--session"
              value={sessionKeyInput}
              onChange={(event) => setSessionKeyInput(event.target.value.toUpperCase())}
              placeholder="ABCDEFGH"
            />
          </label>
        </div>

        <div className="engineer-control-bar__actions">
          <button type="button" className="engineer-button" onClick={handleConnect}>
            Connect
          </button>
          <button type="button" className="engineer-button engineer-button--secondary" onClick={handleDisconnect}>
            Disconnect
          </button>
        </div>

        <div className="engineer-status-strip">
          <span><strong>State:</strong> {connectionState}</span>
          <span><strong>Frames:</strong> {frameCount}</span>
          <span><strong>Session:</strong> {activeSessionKey ?? "—"}</span>
          <span><strong>Info:</strong> {lastInfo}</span>
          {lastError ? <span><strong>Error:</strong> {lastError}</span> : null}
        </div>
      </section>

      <DashboardShell
        backendStatus={backendStatus}
        snapshot={snapshot}
        snapshotTick={snapshotTick}
      />
    </div>
  );
}
""")

ENGINEER_EXTRA_CSS = dedent("""\
.engineer-screen {
  min-height: 100vh;
  width: 100%;
}

.engineer-control-bar {
  display: grid;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(7, 9, 19, 0.88);
  backdrop-filter: blur(10px);
}

.engineer-control-bar__fields {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.engineer-field {
  display: grid;
  gap: 6px;
  min-width: 260px;
}

.engineer-field__label {
  color: #94a3b8;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.engineer-field__input {
  min-height: 42px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  color: #e5e7eb;
  outline: none;
}

.engineer-field__input--session {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  letter-spacing: 0.08em;
}

.engineer-control-bar__actions {
  display: flex;
  gap: 10px;
}

.engineer-button {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  border: 0;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: white;
  cursor: pointer;
  font-weight: 700;
}

.engineer-button--secondary {
  background: rgba(255, 255, 255, 0.1);
}

.engineer-status-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  color: #cbd5e1;
  font-size: 14px;
}

@media (max-width: 900px) {
  body {
    overflow: auto;
  }

  .widget-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-shell {
    grid-template-columns: 1fr;
  }

  .dashboard-sidebar {
    width: 100%;
    border-right: 0;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .dashboard-sidebar__nav {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}
""")


if __name__ == "__main__":
    raise SystemExit(main())
