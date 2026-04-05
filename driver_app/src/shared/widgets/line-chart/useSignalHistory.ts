import { useEffect, useState } from "react";

export function useSignalHistory(value: number | null | undefined, maxSamples = 50): number[] {
  const [history, setHistory] = useState<number[]>([]);

  useEffect(() => {
    if (typeof value !== "number" || Number.isNaN(value)) {
      return;
    }

    setHistory((previous) => {
      const next = [...previous, value];
      if (next.length <= maxSamples) {
        return next;
      }
      return next.slice(next.length - maxSamples);
    });
  }, [value, maxSamples]);

  return history;
}
