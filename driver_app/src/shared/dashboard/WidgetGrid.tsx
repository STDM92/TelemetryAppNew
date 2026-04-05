import React from "react";
import type { BackendStatus } from "../../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../telemetry/telemetryTypes";
import { widgetCatalog } from "./widgetCatalog";
import type { WidgetId, WidgetInstance } from "./widgetTypes";

type WidgetGridProps = {
    backendStatus: BackendStatus | null;
    snapshot: TelemetrySnapshot | null;
    snapshotTick: number;
    widgetIds?: WidgetId[];
    widgets?: WidgetInstance[];
};

export function WidgetGrid({
                               backendStatus,
                               snapshot,
                               snapshotTick,
                               widgetIds,
                               widgets,
                           }: WidgetGridProps) {
    const context = {
        backendStatus,
        snapshot,
        snapshotTick,
    };

    const normalizedWidgets: WidgetInstance[] =
        widgets ??
        (widgetIds ?? []).map((widgetId) => ({
            type: widgetId,
        }));

    return (
        <div className="widget-grid">
            {normalizedWidgets.map((widget, index) => {
                const definition = widgetCatalog[widget.type];
                if (!definition) {
                    return null;
                }

                const key = widget.id ?? `${widget.type}-${index}`;

                return (
                    <div
                        key={key}
                        className="widget-grid__item"
                        style={{
                            gridColumn: widget.fullWidth ? "1 / -1" : undefined,
                            minWidth: 0,
                        }}
                    >
                        {definition.render(context, widget.config)}
                    </div>
                );
            })}
        </div>
    );
}