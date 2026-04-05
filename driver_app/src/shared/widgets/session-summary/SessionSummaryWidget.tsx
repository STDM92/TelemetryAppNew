import React from "react";
import type { BackendStatus } from "../../../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../../telemetry/telemetryTypes";
import { WidgetFrame } from "../../components/WidgetFrame";

type SessionSummaryWidgetProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
};

function formatNumber(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }

  return value.toFixed(digits);
}

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

function formatPosition(overallPosition: number | null | undefined, classPosition: number | null | undefined): string {
  if (overallPosition === null || overallPosition === undefined) {
    return "—";
  }

  if (classPosition === null || classPosition === undefined) {
    return `P${overallPosition}`;
  }

  return `P${overallPosition} / Class P${classPosition}`;
}

export function SessionSummaryWidget({ backendStatus, snapshot }: SessionSummaryWidgetProps) {
  return (
    <WidgetFrame title="Session Summary">
      <div className="kv-list">
        <div className="kv-row">
          <span className="kv-row__label">Connection</span>
          <span className="kv-row__value">{formatConnectionText(backendStatus)}</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Source</span>
          <span className="kv-row__value">{snapshot?.source ?? "—"}</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Simulator</span>
          <span className="kv-row__value">{snapshot?.session?.simulator_name ?? "—"}</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Track</span>
          <span className="kv-row__value">{snapshot?.session?.track_name ?? "—"}</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Session Type</span>
          <span className="kv-row__value">{snapshot?.session?.session_type ?? "—"}</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Session Phase</span>
          <span className="kv-row__value">{snapshot?.session?.session_phase ?? "—"}</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Current Lap</span>
          <span className="kv-row__value">{snapshot?.lap?.current_lap ?? "—"}</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Completed Laps</span>
          <span className="kv-row__value">{snapshot?.lap?.completed_laps ?? "—"}</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Speed</span>
          <span className="kv-row__value">{formatNumber(snapshot?.powertrain?.vehicle_speed_kph, 1)} kph</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Gear</span>
          <span className="kv-row__value">{snapshot?.powertrain?.gear ?? "—"}</span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Position</span>
          <span className="kv-row__value">
            {formatPosition(snapshot?.race?.overall_position, snapshot?.race?.class_position)}
          </span>
        </div>

        <div className="kv-row">
          <span className="kv-row__label">Stream</span>
          <span className="kv-row__value">{backendStatus?.stream_state ?? "—"}</span>
        </div>
      </div>
    </WidgetFrame>
  );
}
