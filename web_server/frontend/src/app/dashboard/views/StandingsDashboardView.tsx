import React from "react";
import type { BackendStatus } from "../../local-api/statusClient";
import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";
import { WidgetGrid } from "../../../shared/dashboard/WidgetGrid";
import type { WidgetId } from "../../../shared/dashboard/widgetTypes";

type StandingsDashboardViewProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
  snapshotTick: number;
};

const standingsWidgetIds: WidgetId[] = [
  "standings-info",
];

export function StandingsDashboardView({ backendStatus, snapshot, snapshotTick }: StandingsDashboardViewProps) {
  return (
    <WidgetGrid
      backendStatus={backendStatus}
      snapshot={snapshot}
      snapshotTick={snapshotTick}
      widgetIds={standingsWidgetIds}
    />
  );
}
