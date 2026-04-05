import type { ReactNode } from "react";
import type { BackendStatus } from "../../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../telemetry/telemetryTypes";

export type DashboardWidgetContext = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
};

export type WidgetDefinition = {
  id: string;
  title: string;
  render: (context: DashboardWidgetContext) => ReactNode;
};