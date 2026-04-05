import React from "react";
import type { BackendStatus } from "../../local-api/statusClient";
import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";
import { DashboardView } from "../../../shared/dashboard/DashboardView";

type TelemetryDashboardViewProps = {
    backendStatus: BackendStatus | null;
    snapshot: TelemetrySnapshot | null;
};

export function TelemetryDashboardView({ backendStatus, snapshot }: TelemetryDashboardViewProps) {
    return <DashboardView backendStatus={backendStatus} snapshot={snapshot} />;
}