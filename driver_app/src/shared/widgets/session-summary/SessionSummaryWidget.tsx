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

export function SessionSummaryWidget({ backendStatus, snapshot }: SessionSummaryWidgetProps) {
    return (
        <WidgetFrame title="Session Summary">
            <div className="kv-list">
                <div className="kv-row">
                    <span className="kv-row__label">Connection</span>
                    <span className="kv-row__value">{formatConnectionText(backendStatus)}</span>
                </div>

                <div className="kv-row">
                    <span className="kv-row__label">Track</span>
                    <span className="kv-row__value">{snapshot?.track_name ?? "—"}</span>
                </div>

                <div className="kv-row">
                    <span className="kv-row__label">Session</span>
                    <span className="kv-row__value">{snapshot?.session_phase ?? "—"}</span>
                </div>

                <div className="kv-row">
                    <span className="kv-row__label">Lap</span>
                    <span className="kv-row__value">{snapshot?.current_lap ?? "—"}</span>
                </div>

                <div className="kv-row">
                    <span className="kv-row__label">Speed</span>
                    <span className="kv-row__value">{formatNumber(snapshot?.vehicle_speed_kph, 1)} kph</span>
                </div>

                <div className="kv-row">
                    <span className="kv-row__label">Gear</span>
                    <span className="kv-row__value">{snapshot?.gear ?? "—"}</span>
                </div>

                <div className="kv-row">
                    <span className="kv-row__label">Stream</span>
                    <span className="kv-row__value">{backendStatus?.stream_state ?? "—"}</span>
                </div>
            </div>
        </WidgetFrame>
    );
}