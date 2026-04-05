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
    id: "telemetry-throttle-chart",
    type: "line-chart",
    config: {
      title: "Throttle",
      sourcePath: "inputs.throttle_ratio",
      color: "#22c55e",
      min: 0,
      max: 1,
      maxSamples: 50,
    },
  },
  {
    id: "telemetry-brake-chart",
    type: "line-chart",
    config: {
      title: "Brake",
      sourcePath: "inputs.brake_ratio",
      color: "#ef4444",
      min: 0,
      max: 1,
      maxSamples: 50,
    },
  },
  {
    id: "telemetry-steering-chart",
    type: "line-chart",
    config: {
      title: "Steering",
      sourcePath: "inputs.steering_angle_rad",
      color: "#f59e0b",
      zeroCentered: true,
      maxSamples: 50,
    },
  },
  {
    id: "telemetry-speed-chart",
    type: "line-chart",
    config: {
      title: "Speed",
      sourcePath: "powertrain.vehicle_speed_kph",
      color: "#3b82f6",
      min: 0,
      maxSamples: 50,
    },
  },
];

export function TelemetryDashboardView({ backendStatus, snapshot }: TelemetryDashboardViewProps) {
  return <WidgetGrid backendStatus={backendStatus} snapshot={snapshot} widgets={telemetryWidgets} />;
}
