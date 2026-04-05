import React from "react";
import type { BackendStatus } from "../../local-api/statusClient";
import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";
import { DashboardShell } from "../../dashboard/DashboardShell";

type DashboardPageProps = {
    snapshot: TelemetrySnapshot | null;
    backendStatus: BackendStatus | null;
};

export function DashboardPage({ snapshot, backendStatus }: DashboardPageProps) {
    return <DashboardShell backendStatus={backendStatus} snapshot={snapshot} />;
}