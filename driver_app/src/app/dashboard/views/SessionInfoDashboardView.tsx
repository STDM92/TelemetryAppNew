import React from "react";
import type { BackendStatus } from "../../local-api/statusClient";
import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";
import { DashboardView } from "../../../shared/dashboard/DashboardView";
import { backendStatusWidgetDefinition } from "../../../shared/widgets/backend-status/definition";
import { sessionSummaryWidgetDefinition } from "../../../shared/widgets/session-summary/definition";

type SessionInfoDashboardViewProps = {
    backendStatus: BackendStatus | null;
    snapshot: TelemetrySnapshot | null;
};

const sessionInfoWidgets = [
    sessionSummaryWidgetDefinition,
    backendStatusWidgetDefinition,
];

export function SessionInfoDashboardView({
                                             backendStatus,
                                             snapshot,
                                         }: SessionInfoDashboardViewProps) {
    return (
        <DashboardView
            backendStatus={backendStatus}
            snapshot={snapshot}
            widgets={sessionInfoWidgets}
        />
    );
}