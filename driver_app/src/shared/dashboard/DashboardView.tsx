import React from "react";
import type { BackendStatus } from "../../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../telemetry/telemetryTypes";
import type { WidgetDefinition } from "./widgetTypes";

type DashboardViewProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
  widgets: WidgetDefinition[];
};

export function DashboardView({ backendStatus, snapshot, widgets }: DashboardViewProps) {
  const context = {
    backendStatus,
    snapshot,
  };

  return (
      <div className="widget-grid">
        {widgets.map((widget) => (
            <React.Fragment key={widget.id}>{widget.render(context)}</React.Fragment>
        ))}
      </div>
  );
}