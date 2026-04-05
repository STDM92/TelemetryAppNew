import React from "react";
import type { BackendStatus } from "../../local-api/statusClient";
import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";
import { WidgetGrid } from "../../../shared/dashboard/WidgetGrid";
import type { WidgetInstance } from "../../../shared/dashboard/widgetTypes";
import type { LineChartWidgetConfig } from "../../../shared/widgets/line-chart/definition";

type TelemetryDashboardViewProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
};

const telemetryWidgets: WidgetInstance<LineChartWidgetConfig>[] = [
  {
    id: "telemetry-driver-inputs",
    type: "driver-inputs",
  },
  {
    id: "telemetry-throttle-chart",
    type: "line-chart",
    config: {
      title: "Throttle",
      sourceKey: "throttle",
      color: "#22c55e",
      min: 0,
      max: 1,
      maxSamples: 50,
    },
  },
];

export function TelemetryDashboardView({ backendStatus, snapshot }: TelemetryDashboardViewProps) {
  return <WidgetGrid backendStatus={backendStatus} snapshot={snapshot} widgets={telemetryWidgets} />;
}
