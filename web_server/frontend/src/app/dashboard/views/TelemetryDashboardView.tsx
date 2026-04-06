import React from "react";
import type { BackendStatus } from "../../local-api/statusClient";
import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";
import { WidgetGrid } from "../../../shared/dashboard/WidgetGrid";
import type { WidgetInstance } from "../../../shared/dashboard/widgetTypes";
import type { LineChartWidgetConfig } from "../../../shared/widgets/line-chart/definition";

type TelemetryDashboardViewProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
  snapshotTick: number;
};

const radToDeg = (rad: number) => rad * (180 / Math.PI);
const telemetryWidgets: WidgetInstance<LineChartWidgetConfig>[] = [
  {
    id: "telemetry-inputs-chart",
    type: "line-chart",
    fullWidth: true,
    config: {
      title: "Throttle / Brake",
      min: 0,
      max: 1,
      maxSamples: 1000,
      displayMultiplier: 100,
      displaySuffix: "%",
      displayDecimals: 0,
      series: [
        {
          label: "Throttle",
          sourcePath: "inputs.throttle_ratio",
          color: "#22c55e",
        },
        {
          label: "Brake",
          sourcePath: "inputs.brake_ratio",
          color: "#ef4444",
        },
      ],
    },
  },
  {
    id: "telemetry-steering-chart",
    type: "line-chart",
    fullWidth: true,
    config: {
      title: "Steering",
      sourcePath: "inputs.steering_angle_rad",
      min: -2.0944,
      max: 2.0944,
      color: "#f59e0b",
      zeroCentered: true,
      maxSamples: 1000,
      displayMultiplier: (180 / Math.PI),
      displaySuffix: "°",
    },
  },
  {
    id: "telemetry-speed-chart",
    type: "line-chart",
    fullWidth: true,
    config: {
      title: "Speed",
      sourcePath: "powertrain.vehicle_speed_kph",
      color: "#3b82f6",
      min: 0,
      max: 300,
      maxSamples: 1000,
    },
  },
];
export function TelemetryDashboardView({
                                         backendStatus,
                                         snapshot,
                                         snapshotTick,
                                       }: TelemetryDashboardViewProps) {
  return (
      <WidgetGrid
          backendStatus={backendStatus}
          snapshot={snapshot}
          snapshotTick={snapshotTick}
          widgets={telemetryWidgets}
      />
  );
}