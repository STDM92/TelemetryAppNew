import React from "react";
import type { BackendStatus } from "../../local-api/statusClient";
import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";
import { DashboardShell } from "../../dashboard/DashboardShell";
import type { UplinkStatus } from "../../local-api/uplinkClient";

type DashboardPageProps = {
  snapshot: TelemetrySnapshot | null;
  snapshotTick: number;
  backendStatus: BackendStatus | null;
  uplinkStatus: UplinkStatus | null;
  isTogglingUplink: boolean;
  onToggleUplink: () => void;
};

export function DashboardPage({
  snapshot,
  snapshotTick,
  backendStatus,
  uplinkStatus,
  isTogglingUplink,
  onToggleUplink,
}: DashboardPageProps) {
  return (
    <DashboardShell
      backendStatus={backendStatus}
      snapshot={snapshot}
      snapshotTick={snapshotTick}
      uplinkStatus={uplinkStatus}
      isTogglingUplink={isTogglingUplink}
      onToggleUplink={onToggleUplink}
    />
  );
}
