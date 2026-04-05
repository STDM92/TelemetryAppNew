import React from "react";
import type { BackendStatus } from "../../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../telemetry/telemetryTypes";
import { widgetCatalog } from "./widgetCatalog";
import type { WidgetId } from "./widgetTypes";

type WidgetGridProps = {
    backendStatus: BackendStatus | null;
    snapshot: TelemetrySnapshot | null;
    widgetIds: WidgetId[];
};

export function WidgetGrid({ backendStatus, snapshot, widgetIds }: WidgetGridProps) {
    const context = {
        backendStatus,
        snapshot,
    };

    return (
        <div className="widget-grid">
            {widgetIds.map((widgetId) => {
                const widget = widgetCatalog[widgetId];
                return <React.Fragment key={widget.id}>{widget.render(context)}</React.Fragment>;
            })}
        </div>
    );
}