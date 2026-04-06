import React from "react";
import type { RuntimeStatus } from "../../local-api/runtimeClient";

type SidecarStatusCardProps = {
  runtimeStatus: RuntimeStatus | null;
  errorText: string | null;
};

export function SidecarStatusCard({ runtimeStatus, errorText }: SidecarStatusCardProps) {
  return (
    <section className="card">
      <h2 className="card__title">Sidecar Status</h2>
      <div className="kv-list">
        <div className="kv-row">
          <span className="kv-row__label">Status</span>
          <span className="kv-row__value">{runtimeStatus?.status ?? "loading"}</span>
        </div>
        <div className="kv-row">
          <span className="kv-row__label">Last Error</span>
          <span className="kv-row__value">{errorText ?? runtimeStatus?.last_error ?? "none"}</span>
        </div>
      </div>
    </section>
  );
}
