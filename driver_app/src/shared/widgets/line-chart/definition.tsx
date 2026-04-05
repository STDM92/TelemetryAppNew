import React from "react";
import type { WidgetDefinition } from "../../dashboard/widgetTypes";
import type { TelemetrySnapshot } from "../../telemetry/telemetryTypes";
import { LineChartWidget } from "./LineChartWidget";
import { useSignalHistory } from "./useSignalHistory";

export type NumericTelemetryKey = {
  [K in keyof TelemetrySnapshot]: TelemetrySnapshot[K] extends number | null | undefined ? K : never;
}[keyof TelemetrySnapshot];

export type LineChartWidgetConfig = {
  title?: string;
  sourceKey: NumericTelemetryKey;
  min?: number;
  max?: number;
  color?: string;
  zeroCentered?: boolean;
  maxSamples?: number;
};

type LineChartWidgetRendererProps = {
  snapshotValue: number | null | undefined;
  config?: LineChartWidgetConfig;
};

function LineChartWidgetRenderer({ snapshotValue, config }: LineChartWidgetRendererProps) {
  const history = useSignalHistory(snapshotValue, config?.maxSamples ?? 50);

  return (
    <LineChartWidget
      title={config?.title ?? "Line Chart"}
      data={history}
      min={config?.min}
      max={config?.max}
      color={config?.color}
      zeroCentered={config?.zeroCentered}
    />
  );
}

export const lineChartWidgetDefinition: WidgetDefinition<LineChartWidgetConfig> = {
  id: "line-chart",
  title: "Line Chart",
  render: (context, config) => {
    // Hooks must not be used directly inside this render callback.
    // Keep hook usage inside a dedicated React component.
    const rawValue = config && context.snapshot ? context.snapshot[config.sourceKey] : null;
    const snapshotValue = typeof rawValue === "number" ? rawValue : null;

    return <LineChartWidgetRenderer snapshotValue={snapshotValue} config={config} />;
  },
};
