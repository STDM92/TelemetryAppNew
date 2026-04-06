import React, { useEffect, useMemo, useState } from "react";
import { DashboardShell } from "../dashboard/DashboardShell";
import type { BackendStatus } from "../local-api/statusClient";
import { connectEngineerStream } from "./api/engineerStreamClient";
import { fetchSessionState } from "./api/sessionClient";
import type { TelemetrySnapshot } from "../../shared/telemetry/telemetryTypes";

type StreamConnectionState = "idle" | "connecting" | "open" | "closed" | "error";

function getInitialServerBaseUrl(): string {
  const params = new URLSearchParams(window.location.search);
  return params.get("server")?.trim() || window.location.origin;
}

function getInitialSessionKey(): string {
  const params = new URLSearchParams(window.location.search);
  return (params.get("session_key") || "").trim().toUpperCase();
}

function buildBackendStatus(
  connectionState: StreamConnectionState,
  hasSnapshot: boolean,
  lastError: string | null,
): BackendStatus {
  const streamState =
    connectionState === "open"
      ? (hasSnapshot ? "streaming" : "idle")
      : connectionState === "error"
        ? "failed"
        : connectionState === "connecting"
          ? "idle"
          : "stale";

  return {
    status: lastError ? "failed" : "running",
    last_error: lastError,
    source_attachment_state: connectionState === "open" ? "attached" : "waiting",
    stream_state: streamState,
    has_received_snapshot: hasSnapshot,
    source_display_name: "Public session",
    sim: "remote",
  };
}

export function EngineerDashboardPage() {
  const [serverBaseUrl, setServerBaseUrl] = useState(getInitialServerBaseUrl);
  const [sessionKeyInput, setSessionKeyInput] = useState(getInitialSessionKey);
  const [activeSessionKey, setActiveSessionKey] = useState(getInitialSessionKey);
  const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
  const [snapshotTick, setSnapshotTick] = useState(0);
  const [frameCount, setFrameCount] = useState(0);
  const [connectionState, setConnectionState] = useState<StreamConnectionState>(
    getInitialSessionKey() ? "connecting" : "idle",
  );
  const [lastError, setLastError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeSessionKey) {
      setSnapshot(null);
      setFrameCount(0);
      setConnectionState("idle");
      return;
    }

    let cancelled = false;
    setConnectionState("connecting");
    setLastError(null);

    fetchSessionState(serverBaseUrl, activeSessionKey)
      .then((response) => {
        if (cancelled) {
          return;
        }

        if (response.latest_snapshot) {
          setSnapshot(response.latest_snapshot);
          setSnapshotTick((value) => value + 1);
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        setLastError(error instanceof Error ? error.message : String(error));
      });

    const disconnect = connectEngineerStream(serverBaseUrl, activeSessionKey, {
      onOpen: () => {
        if (cancelled) {
          return;
        }
        setConnectionState("open");
        setLastError(null);
      },
      onSnapshot: (nextSnapshot) => {
        if (cancelled) {
          return;
        }
        setSnapshot(nextSnapshot);
        setSnapshotTick((value) => value + 1);
        setFrameCount((value) => value + 1);
      },
      onClose: () => {
        if (cancelled) {
          return;
        }
        setConnectionState("closed");
      },
      onError: () => {
        if (cancelled) {
          return;
        }
        setConnectionState("error");
        setLastError("WebSocket connection failed.");
      },
    });

    return () => {
      cancelled = true;
      disconnect();
    };
  }, [serverBaseUrl, activeSessionKey]);

  const backendStatus = useMemo(
    () => buildBackendStatus(connectionState, snapshot !== null, lastError),
    [connectionState, snapshot, lastError],
  );

  function handleConnect(event: React.FormEvent) {
    event.preventDefault();

    const normalized = sessionKeyInput.trim().toUpperCase();
    setActiveSessionKey(normalized);
    setFrameCount(0);
    setSnapshot(null);
    setSnapshotTick(0);

    const url = new URL(window.location.href);
    if (normalized) {
      url.searchParams.set("session_key", normalized);
    } else {
      url.searchParams.delete("session_key");
    }
    url.searchParams.set("server", serverBaseUrl);
    window.history.replaceState({}, "", url);
  }

  return (
    <div className="engineer-page">
      <form className="engineer-toolbar" onSubmit={handleConnect}>
        <div className="engineer-toolbar__field engineer-toolbar__field--grow">
          <label htmlFor="serverBaseUrl">Server base URL</label>
          <input
            id="serverBaseUrl"
            value={serverBaseUrl}
            onChange={(event) => setServerBaseUrl(event.target.value)}
            placeholder="https://your-server"
          />
        </div>

        <div className="engineer-toolbar__field">
          <label htmlFor="sessionKey">Session key</label>
          <input
            id="sessionKey"
            value={sessionKeyInput}
            onChange={(event) => setSessionKeyInput(event.target.value.toUpperCase())}
            placeholder="ABCDEFGH"
          />
        </div>

        <div className="engineer-toolbar__actions">
          <button type="submit">Connect</button>
        </div>

        <div className="engineer-toolbar__status">
          <span>Status: {connectionState}</span>
          <span>Frames: {frameCount}</span>
          <span>Session: {activeSessionKey || "—"}</span>
        </div>
      </form>

      {lastError ? <div className="engineer-banner engineer-banner--error">{lastError}</div> : null}

      <DashboardShell
        backendStatus={backendStatus}
        snapshot={snapshot}
        snapshotTick={snapshotTick}
      />
    </div>
  );
}
