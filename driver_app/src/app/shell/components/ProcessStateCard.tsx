import React from "react";
import type { SidecarProcessState } from "../../local-api/processClient";

type ProcessStateCardProps = {
  processState: SidecarProcessState | null;
};

export function ProcessStateCard({ processState }: ProcessStateCardProps) {
  return (
    <section className="card">
      <h2 className="card__title">Process State</h2>
      <div className="kv-list">
        <div className="kv-row">
          <span className="kv-row__label">Status</span>
          <span className="kv-row__value">{processState?.status ?? "unknown"}</span>
        </div>
        <div className="kv-row">
          <span className="kv-row__label">PID</span>
          <span className="kv-row__value">{processState?.pid ?? "n/a"}</span>
        </div>
        <div className="kv-row">
          <span className="kv-row__label">Exit Code</span>
          <span className="kv-row__value">{processState?.exitCode ?? "n/a"}</span>
        </div>
      </div>
    </section>
  );
}
