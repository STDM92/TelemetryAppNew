import React from "react";
import type { BackendStatus } from "../../app/local-api/statusClient";
import type { TelemetrySnapshot } from "../telemetry/telemetryTypes";
import { widgetCatalog } from "./widgetCatalog";
import type { WidgetId, WidgetInstance } from "./widgetTypes";

type WidgetGridProps = {
  backendStatus: BackendStatus | null;
  snapshot: TelemetrySnapshot | null;
  widgetIds?: WidgetId[];
  widgets?: WidgetInstance[];
};

export function WidgetGrid({ backendStatus, snapshot, widgetIds, widgets }: WidgetGridProps) {
  const context = {
    backendStatus,
    snapshot,
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
          <React.Fragment key={key}>
            {definition.render(context, widget.config)}
          </React.Fragment>
        );
      })}
    </div>
  );
}
