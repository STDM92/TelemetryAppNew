import React, { useMemo } from "react";
import { WidgetFrame } from "../../components/WidgetFrame";

type LineChartWidgetProps = {
  title: string;
  data: number[];
  min?: number;
  max?: number;
  color?: string;
  zeroCentered?: boolean;
};

const DEFAULT_COLOR = "#60a5fa";
const SVG_WIDTH = 100;
const SVG_HEIGHT = 48;
const PADDING = 4;

export function LineChartWidget({
  title,
  data,
  min,
  max,
  color = DEFAULT_COLOR,
  zeroCentered = false,
}: LineChartWidgetProps) {
  const { resolvedMin, resolvedMax, points, zeroLineY, latestValue } = useMemo(() => {
    const safeData = data.length > 0 ? data : [0];

    const dataMin = Math.min(...safeData);
    const dataMax = Math.max(...safeData);

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

    const points = safeData
      .map((value, index) => `${toX(index, safeData.length)},${toY(value)}`)
      .join(" ");

    const zeroLineY = resolvedMin <= 0 && resolvedMax >= 0 ? toY(0) : null;

    return {
      resolvedMin,
      resolvedMax,
      points,
      zeroLineY,
      latestValue: safeData[safeData.length - 1] ?? null,
    };
  }, [data, min, max, zeroCentered]);

  return (
    <WidgetFrame title={title}>
      <div className="line-chart-widget">
        <div className="line-chart-widget__meta">
          <span>{resolvedMax.toFixed(2)}</span>
          <span>{latestValue?.toFixed(2) ?? "--"}</span>
          <span>{resolvedMin.toFixed(2)}</span>
        </div>

        <svg
          viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
          className="line-chart-widget__svg"
          preserveAspectRatio="none"
          aria-label={`${title} line chart`}
        >
          <rect
            x="0"
            y="0"
            width={SVG_WIDTH}
            height={SVG_HEIGHT}
            rx="6"
            className="line-chart-widget__background"
          />

          {zeroLineY !== null ? (
            <line
              x1={PADDING}
              y1={zeroLineY}
              x2={SVG_WIDTH - PADDING}
              y2={zeroLineY}
              className="line-chart-widget__zero-line"
            />
          ) : null}

          <polyline
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinejoin="round"
            strokeLinecap="round"
            points={points}
          />
        </svg>
      </div>
    </WidgetFrame>
  );
}
