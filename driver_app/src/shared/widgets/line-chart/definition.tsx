import React from "react";
import type { WidgetDefinition } from "../../dashboard/widgetTypes";
import { getNumericTelemetryValue } from "../../telemetry/getNumericTelemetryValue";
import { LineChartWidget } from "./LineChartWidget";
import { useSignalHistory } from "./useSignalHistory";

export type LineChartWidgetConfig = {
  title?: string;
  sourcePath: string;
  min?: number;
  max?: number;
  color?: string;
  zeroCentered?: boolean;
  maxSamples?: number;
};

type LineChartWidgetRendererProps = {
  snapshotValue: number | null;
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
    const snapshotValue = config ? getNumericTelemetryValue(context.snapshot, config.sourcePath) : null;

    return <LineChartWidgetRenderer snapshotValue={snapshotValue} config={config} />;
  },
};
