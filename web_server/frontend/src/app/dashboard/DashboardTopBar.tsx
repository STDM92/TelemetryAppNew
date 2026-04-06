import React from "react";
import type { BackendStatus } from "../local-api/statusClient";
import type { TelemetrySnapshot } from "../../shared/telemetry/telemetryTypes";

type DashboardTopBarProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
};

function formatConnectionText(backendStatus: BackendStatus | null): string {
  if (!backendStatus) {
    return "Unknown";
  }

  if (backendStatus.source_attachment_state === "attached") {
    return backendStatus.source_display_name ?? backendStatus.sim ?? "Connected";
  }

  if (backendStatus.source_attachment_state === "waiting") {
    return "Waiting for simulator";
  }

  return "Disconnected";
}

function formatTrackText(snapshot: TelemetrySnapshot | null): string {
  return snapshot?.session?.track_name ?? "Unknown track";
}

function formatSessionText(snapshot: TelemetrySnapshot | null): string {
  const sessionType = snapshot?.session?.session_type;
  const sessionPhase = snapshot?.session?.session_phase;

  if (sessionType && sessionPhase) {
    return `${sessionType} · ${sessionPhase}`;
  }

  return sessionType ?? sessionPhase ?? "Unknown session";
}

function formatLapText(snapshot: TelemetrySnapshot | null): string {
  const currentLap = snapshot?.lap?.current_lap;
  if (currentLap === null || currentLap === undefined) {
    return "Lap —";
  }

  return `Lap ${currentLap}`;
}

function formatTimeLeftText(snapshot: TelemetrySnapshot | null): string {
  const seconds = snapshot?.session?.session_time_remaining_s;
  if (seconds === null || seconds === undefined || seconds < 0 || Number.isNaN(seconds)) {
    return "Time —";
  }

  const wholeSeconds = Math.floor(seconds);
  const hours = Math.floor(wholeSeconds / 3600);
  const minutes = Math.floor((wholeSeconds % 3600) / 60);
  const remSeconds = wholeSeconds % 60;

  if (hours > 0) {
    return `Time ${hours}:${String(minutes).padStart(2, "0")}:${String(remSeconds).padStart(2, "0")}`;
  }

  return `Time ${minutes}:${String(remSeconds).padStart(2, "0")}`;
}

function formatPitRoadText(snapshot: TelemetrySnapshot | null): string {
  const isOnPitRoad = snapshot?.session?.is_on_pit_road;

  if (isOnPitRoad === null || isOnPitRoad === undefined) {
    return "Unknown";
  }

  return isOnPitRoad ? "On pit road" : "Track";
}

export function DashboardTopBar({ backendStatus, snapshot }: DashboardTopBarProps) {
  return (
    <header className="dashboard-topbar">
      <div className="dashboard-topbar__group">
        <div className="dashboard-topbar__brand">Live Telemetry</div>
      </div>

      <div className="dashboard-topbar__metrics">
        <div className="dashboard-chip">
          <span className="dashboard-chip__label">Connection</span>
          <span className="dashboard-chip__value">{formatConnectionText(backendStatus)}</span>
        </div>

        <div className="dashboard-chip">
          <span className="dashboard-chip__label">Track</span>
          <span className="dashboard-chip__value">{formatTrackText(snapshot)}</span>
        </div>

        <div className="dashboard-chip">
          <span className="dashboard-chip__label">Session</span>
          <span className="dashboard-chip__value">{formatSessionText(snapshot)}</span>
        </div>

        <div className="dashboard-chip">
          <span className="dashboard-chip__label">Progress</span>
          <span className="dashboard-chip__value">{formatLapText(snapshot)}</span>
        </div>

        <div className="dashboard-chip">
          <span className="dashboard-chip__label">Remaining</span>
          <span className="dashboard-chip__value">{formatTimeLeftText(snapshot)}</span>
        </div>

        <div className="dashboard-chip">
          <span className="dashboard-chip__label">Pit Road</span>
          <span className="dashboard-chip__value">{formatPitRoadText(snapshot)}</span>
        </div>

        <div className="dashboard-chip">
          <span className="dashboard-chip__label">Stream</span>
          <span className="dashboard-chip__value">{backendStatus?.stream_state ?? "unknown"}</span>
        </div>
      </div>
    </header>
  );
}
