import React, { useMemo } from "react";
import { WidgetFrame } from "../../components/WidgetFrame";

type LineChartSeriesData = {
  label?: string;
  color?: string;
  sourcePath: string;
  data: number[];
};

type LineChartWidgetProps = {
  title: string;
  series: LineChartSeriesData[];
  min?: number;
  max?: number;
  zeroCentered?: boolean;
  valueSuffix?: string;
  valueDecimals?: number;
};

const DEFAULT_COLOR = "#60a5fa";
const SVG_WIDTH = 2000;
const SVG_HEIGHT = 48;
const PADDING = 4;

export function LineChartWidget({
                                  title,
                                  series,
                                  min,
                                  max,
                                  zeroCentered = false,
                                  valueSuffix = "",
                                  valueDecimals = 2,
                                }: LineChartWidgetProps) {
  const { resolvedMin, resolvedMax, renderedSeries, zeroLineY, latestValues } = useMemo(() => {
    const allValues = series.flatMap((entry) => (entry.data.length > 0 ? entry.data : [0]));
    const safeValues = allValues.length > 0 ? allValues : [0];

    const dataMin = Math.min(...safeValues);
    const dataMax = Math.max(...safeValues);

    let resolvedMin = min ?? dataMin;
    let resolvedMax = max ?? dataMax;

    if (zeroCentered) {
      const absMax = Math.max(Math.abs(resolvedMin), Math.abs(resolvedMax), 1);
      resolvedMin = -absMax;
      resolvedMax = absMax;
    }

    if (resolvedMin === resolvedMax) {
      resolvedMax = resolvedMin + 1;
    }

    const innerWidth = SVG_WIDTH - PADDING * 2;
    const innerHeight = SVG_HEIGHT - PADDING * 2;

    const toX = (index: number, length: number) => {
      if (length <= 1) {
        return PADDING;
      }
      return PADDING + (index / (length - 1)) * innerWidth;
    };

    const toY = (value: number) => {
      const normalized = (value - resolvedMin) / (resolvedMax - resolvedMin);
      return PADDING + (1 - normalized) * innerHeight;
    };

    const renderedSeries = series.map((entry) => {
      const safeData = entry.data.length > 0 ? entry.data : [0];
      const points = safeData
          .map((value, index) => `${toX(index, safeData.length)},${toY(value)}`)
          .join(" ");

      return {
        ...entry,
        points,
        color: entry.color ?? DEFAULT_COLOR,
      };
    });

    const zeroLineY = resolvedMin <= 0 && resolvedMax >= 0 ? toY(0) : null;

    const latestValues = renderedSeries.map((entry) => ({
      label: entry.label ?? entry.sourcePath,
      value: entry.data.length > 0 ? entry.data[entry.data.length - 1] : null,
      color: entry.color,
    }));

    return {
      resolvedMin,
      resolvedMax,
      renderedSeries,
      zeroLineY,
      latestValues,
    };
  }, [series, min, max, zeroCentered]);

  const formatValue = (value: number | null) => {
    if (value === null) {
      return "--";
    }
    return `${value.toFixed(valueDecimals)}${valueSuffix}`;
  };

    return (
        <WidgetFrame title={title}>
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.5rem",
                    height: "100%",
                    minHeight: 0,
                }}
            >
                <div
                    style={{
                        display: "flex",
                        flexDirection: "row",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "0.75rem",
                        fontSize: "0.875rem",
                        lineHeight: 1.1,
                        textAlign: "center",
                        flexShrink: 0,
                        flexWrap: "wrap",
                    }}
                >
                    {latestValues.map((entry) => (
                        <span key={entry.label} style={{ color: entry.color, whiteSpace: "nowrap" }}>
            {entry.label}: {formatValue(entry.value)}
        </span>
                    ))}
                </div>
                <div
                    style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "0.75rem",
                        height: "8rem",
                        flexShrink: 0,
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "space-between",
                            alignItems: "flex-start",
                            minWidth: "3.5rem",
                            height: "100%",
                            fontSize: "0.875rem",
                            lineHeight: 1,
                            color: "rgba(255,255,255,0.8)",
                            paddingTop: "0.15rem",
                            paddingBottom: "0.15rem",
                            boxSizing: "border-box",
                            flexShrink: 0,
                        }}
                    >
                        <span>{formatValue(resolvedMax)}</span>
                        <span>{formatValue(resolvedMin)}</span>
                    </div>

                    <svg
                        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
                        preserveAspectRatio="none"
                        aria-label={`${title} line chart`}
                        style={{
                            width: "100%",
                            height: "100%",
                            display: "block",
                            flex: 1,
                            minWidth: 0,
                        }}
                    >
                        <rect
                            x="0"
                            y="0"
                            width={SVG_WIDTH}
                            height={SVG_HEIGHT}
                            rx="6"
                            fill="rgba(255,255,255,0.03)"
                        />

                        {zeroLineY !== null ? (
                            <line
                                x1={PADDING}
                                y1={zeroLineY}
                                x2={SVG_WIDTH - PADDING}
                                y2={zeroLineY}
                                stroke="rgba(255,255,255,0.16)"
                                strokeWidth="1"
                            />
                        ) : null}

                        {renderedSeries.map((entry) => (
                            <polyline
                                key={entry.sourcePath}
                                fill="none"
                                stroke={entry.color}
                                strokeWidth="1.5"
                                strokeLinejoin="round"
                                strokeLinecap="round"
                                points={entry.points}
                            />
                        ))}
                    </svg>
                </div>
            </div>
        </WidgetFrame>
    );}