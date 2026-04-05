import type { ReactNode } from "react";
import type { BackendStatus } from "../../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../telemetry/telemetryTypes";

export type DashboardWidgetContext = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
};

export type WidgetId =
    | "session-summary"
    | "backend-status"
    | "driver-inputs"
    | "standings-info"
    | "pit-info";

export type WidgetDefinition = {
  id: WidgetId;
  title: string;
  render: (context: DashboardWidgetContext) => ReactNode;
};