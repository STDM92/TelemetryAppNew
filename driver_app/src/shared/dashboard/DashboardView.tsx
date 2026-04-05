import React from "react";
import type { BackendStatus } from "../../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../telemetry/telemetryTypes";
import { widgetRegistry } from "./widgetRegistry";

type DashboardViewProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
};

export function DashboardView({ backendStatus, snapshot }: DashboardViewProps) {
  const context = {
    backendStatus,
    snapshot,
  };

  return (
      <div className="widget-grid">
        {widgetRegistry.map((widget) => (
            <React.Fragment key={widget.id}>{widget.render(context)}</React.Fragment>
        ))}
      </div>
  );
}