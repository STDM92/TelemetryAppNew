import React from "react";
import { DashboardView } from "../../../shared/dashboard/DashboardView";

export function DashboardPage() {
  return (
    <div className="page-stack">
      <header className="page-header">
        <h1 className="page-header__title">Dashboard</h1>
        <p className="page-header__text">
          Shared dashboard surface intended to work in both the driver app and the future web UI.
        </p>
      </header>

      <DashboardView />
    </div>
  );
}
