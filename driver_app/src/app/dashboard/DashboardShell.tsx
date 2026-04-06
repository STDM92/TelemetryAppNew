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
import type { UplinkStatus } from "../local-api/uplinkClient";

type DashboardShellProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
  snapshotTick: number;
  uplinkStatus: UplinkStatus | null;
  isTogglingUplink: boolean;
  onToggleUplink: () => void;
};

export function DashboardShell({
  backendStatus,
  snapshot,
  snapshotTick,
  uplinkStatus,
  isTogglingUplink,
  onToggleUplink,
}: DashboardShellProps) {
  const [activeView, setActiveView] = useState<DashboardViewId>("telemetry");

  const content = useMemo(() => {
    switch (activeView) {
      case "standings":
        return (
          <StandingsDashboardView
            backendStatus={backendStatus}
            snapshot={snapshot}
            snapshotTick={snapshotTick}
          />);
      case "pits":
        return (
          <PitInfoDashboardView
            backendStatus={backendStatus}
            snapshot={snapshot}
            snapshotTick={snapshotTick}
          />);
      case "sessionInfo":
        return (
          <SessionInfoDashboardView
            backendStatus={backendStatus}
            snapshot={snapshot}
            snapshotTick={snapshotTick}
          />);
      case "telemetry":
      default:
        return (
          <TelemetryDashboardView
            backendStatus={backendStatus}
            snapshot={snapshot}
            snapshotTick={snapshotTick}
          />
        );
    }
  }, [activeView, backendStatus, snapshot, snapshotTick]);

  return (
    <div className="dashboard-shell">
      <DashboardSidebar activeView={activeView} onSelectView={setActiveView} />

      <div className="dashboard-shell__main">
        <DashboardTopBar
          backendStatus={backendStatus}
          snapshot={snapshot}
          uplinkStatus={uplinkStatus}
          isTogglingUplink={isTogglingUplink}
          onToggleUplink={onToggleUplink}
        />
        <main className="dashboard-shell__content">{content}</main>
      </div>
    </div>
  );
}
