import React, { useMemo, useState } from "react";
import type { BackendStatus } from "../local-api/statusClient";
import type { TelemetrySnapshot } from "../../shared/telemetry/telemetryTypes";
import { DashboardSidebar } from "./DashboardSidebar";
import { DashboardTopBar } from "./DashboardTopBar";
import type { DashboardViewId } from "./dashboardTypes";
import { PitInfoDashboardView } from "./views/PitInfoDashboardView";
import { SessionInfoDashboardView } from "./views/SessionInfoDashboardView";
import { StandingsDashboardView } from "./views/StandingsDashboardView";
import { TelemetryDashboardView } from "./views/TelemetryDashboardView";

type DashboardShellProps = {
    backendStatus: BackendStatus | null;
    snapshot: TelemetrySnapshot | null;
};

export function DashboardShell({ backendStatus, snapshot }: DashboardShellProps) {
    const [activeView, setActiveView] = useState<DashboardViewId>("telemetry");

    const content = useMemo(() => {
        switch (activeView) {
            case "standings":
                return <StandingsDashboardView backendStatus={backendStatus} snapshot={snapshot} />;
            case "pits":
                return <PitInfoDashboardView backendStatus={backendStatus} snapshot={snapshot} />;
            case "sessionInfo":
                return <SessionInfoDashboardView backendStatus={backendStatus} snapshot={snapshot} />;
            case "telemetry":
            default:
                return <TelemetryDashboardView backendStatus={backendStatus} snapshot={snapshot} />;
        }
    }, [activeView, backendStatus, snapshot]);

    return (
        <div className="dashboard-shell">
            <DashboardSidebar activeView={activeView} onSelectView={setActiveView} />

            <div className="dashboard-shell__main">
                <DashboardTopBar backendStatus={backendStatus} snapshot={snapshot} />
                <main className="dashboard-shell__content">{content}</main>
            </div>
        </div>
    );
}