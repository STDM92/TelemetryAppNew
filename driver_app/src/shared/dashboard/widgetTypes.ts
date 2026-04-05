import type { ReactNode } from "react";
import type { BackendStatus } from "../../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../telemetry/telemetryTypes";

export type DashboardWidgetContext = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
  snapshotTick: number;
};

export type WidgetId =
  | "session-summary"
  | "backend-status"
  | "driver-inputs"
  | "standings-info"
  | "pit-info"
  | "line-chart";

export type WidgetDefinition<TConfig = unknown> = {
  id: WidgetId;
  title: string;
  render: (context: DashboardWidgetContext, config?: TConfig) => ReactNode;
};

export type WidgetInstance<TConfig = unknown> = {
  id?: string;
  type: WidgetId;
  config?: TConfig;
};
