import React from "react";
import type { BackendStatus } from "../../local-api/statusClient";
import type { TelemetrySnapshot } from "../../../shared/telemetry/telemetryTypes";
import { WidgetGrid } from "../../../shared/dashboard/WidgetGrid";
import type { WidgetId } from "../../../shared/dashboard/widgetTypes";

type PitInfoDashboardViewProps = {
    backendStatus: BackendStatus | null;
    snapshot: TelemetrySnapshot| null;
};

const pitInfoWidgetIds: WidgetId[] = [
    "pit-info",
];

export function PitInfoDashboardView({ backendStatus, snapshot }: PitInfoDashboardViewProps) {
    return (
        <WidgetGrid
            backendStatus={backendStatus}
            snapshot={snapshot}
            widgetIds={pitInfoWidgetIds}
        />
    );
}

