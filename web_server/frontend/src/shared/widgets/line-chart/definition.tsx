import React from "react";
import type { WidgetDefinition } from "../../dashboard/widgetTypes";
import { getNumericTelemetryValue } from "../../telemetry/getNumericTelemetryValue";
import { LineChartWidget } from "./LineChartWidget";
import { useSignalHistory } from "./useSignalHistory";

export type LineChartSeriesConfig = {
    label?: string;
    sourcePath: string;
    color?: string;
};

export type LineChartWidgetConfig = {
    title?: string;
    sourcePath?: string;
    color?: string;
    series?: LineChartSeriesConfig[];
    min?: number;
    max?: number;
    zeroCentered?: boolean;
    maxSamples?: number;

    // keep these because your dashboard config still uses them
    displayMultiplier?: number;
    displaySuffix?: string;
    displayDecimals?: number;
};

type ResolvedLineChartSeries = {
    label?: string;
    color?: string;
    sourcePath: string;
    value: number | null;
};

type LineChartWidgetRendererProps = {
    series: ResolvedLineChartSeries[];
    snapshotTick: number;
    config?: LineChartWidgetConfig;
};

function normalizeSeries(config?: LineChartWidgetConfig): LineChartSeriesConfig[] {
    if (config?.series && config.series.length > 0) {
        return config.series;
    }

    if (config?.sourcePath) {
        return [
            {
                label: config.title,
                sourcePath: config.sourcePath,
                color: config.color,
            },
        ];
    }

    return [];
}

function LineChartWidgetRenderer({
                                     series,
                                     snapshotTick,
                                     config,
                                 }: LineChartWidgetRendererProps) {
    const historySeries = useSignalHistory(series, snapshotTick, config?.maxSamples ?? 50);

    const multiplier = config?.displayMultiplier ?? 1;

    const transformedSeries = historySeries.map((entry) => ({
        ...entry,
        data: entry.data.map((value) => value * multiplier),
    }));

    const transformedMin = config?.min !== undefined ? config.min * multiplier : undefined;
    const transformedMax = config?.max !== undefined ? config.max * multiplier : undefined;

    return (
        <LineChartWidget
            title={config?.title ?? "Line Chart"}
            series={transformedSeries}
            min={transformedMin}
            max={transformedMax}
            zeroCentered={config?.zeroCentered}
            valueSuffix={config?.displaySuffix}
            valueDecimals={config?.displayDecimals}
        />
    );
}

export const lineChartWidgetDefinition: WidgetDefinition<LineChartWidgetConfig> = {
    id: "line-chart",
    title: "Line Chart",
    render: (context, config) => {
        const resolvedSeries = normalizeSeries(config).map((series) => ({
            ...series,
            value: getNumericTelemetryValue(context.snapshot, series.sourcePath),
        }));

        return (
            <LineChartWidgetRenderer
                series={resolvedSeries}
                snapshotTick={context.snapshotTick}
                config={config}
            />
        );
    },
};