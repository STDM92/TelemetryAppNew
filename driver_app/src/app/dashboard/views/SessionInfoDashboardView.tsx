import React from "react";
import type { BackendStatus } from "../../local-api/statusClient";
import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";
import { WidgetGrid } from "../../../shared/dashboard/WidgetGrid";
import type { WidgetId } from "../../../shared/dashboard/widgetTypes";

type SessionInfoDashboardViewProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
  snapshotTick: number;
};

const sessionInfoWidgetIds: WidgetId[] = [
  // keep your existing ids here
];

export function SessionInfoDashboardView({
  backendStatus,
  snapshot,
  snapshotTick,
}: SessionInfoDashboardViewProps) {
  return (
    <WidgetGrid
      backendStatus={backendStatus}
      snapshot={snapshot}
      snapshotTick={snapshotTick}
      widgetIds={sessionInfoWidgetIds}
    />
  );
}