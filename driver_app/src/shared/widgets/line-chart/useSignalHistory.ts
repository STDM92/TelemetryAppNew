import { useEffect, useState } from "react";

type SignalSeriesInput = {
  label?: string;
  color?: string;
  sourcePath: string;
  value: number | null;
  displayMultiplier?: number;
  displaySuffix?: string;
  displayDecimals?: number;
};

type SignalSeriesHistory = {
  label?: string;
  color?: string;
  sourcePath: string;
  data: number[];
  displayMultiplier?: number;
  displaySuffix?: string;
  displayDecimals?: number;
};

export function useSignalHistory(
    series: SignalSeriesInput[],
    snapshotTick: number,
    maxSamples = 1
): SignalSeriesHistory[] {
  const [history, setHistory] = useState<Record<string, SignalSeriesHistory>>({});

  useEffect(() => {
    if (series.length === 0) {
      return;
    }

    setHistory((previous) => {
      const next: Record<string, SignalSeriesHistory> = { ...previous };

      for (const currentSeries of series) {
        const existing = next[currentSeries.sourcePath];
        const previousData = existing?.data ?? [];
        const previousLastValue =
            previousData.length > 0 ? previousData[previousData.length - 1] : 0;

        const nextValue =
            typeof currentSeries.value === "number" && !Number.isNaN(currentSeries.value)
                ? currentSeries.value
                : previousLastValue;

        const nextData = [...previousData, nextValue];
        const trimmedData =
            nextData.length <= maxSamples
                ? nextData
                : nextData.slice(nextData.length - maxSamples);

        next[currentSeries.sourcePath] = {
          label: currentSeries.label,
          color: currentSeries.color,
          sourcePath: currentSeries.sourcePath,
          data: trimmedData,
          displayMultiplier: currentSeries.displayMultiplier,
          displaySuffix: currentSeries.displaySuffix,
          displayDecimals: currentSeries.displayDecimals,
        };
      }

      return next;
    });
  }, [series, snapshotTick, maxSamples]);

  return series.map((currentSeries) => ({
    label: currentSeries.label,
    color: currentSeries.color,
    sourcePath: currentSeries.sourcePath,
    data: history[currentSeries.sourcePath]?.data ?? [],
    displayMultiplier: currentSeries.displayMultiplier,
    displaySuffix: currentSeries.displaySuffix,
    displayDecimals: currentSeries.displayDecimals,
  }));
}