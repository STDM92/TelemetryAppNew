import React from "react";
import type { ShellPageId } from "../DriverShell";

type SideNavProps = {
  activePage: ShellPageId;
  onSelectPage: (page: ShellPageId) => void;
};

export function SideNav({ activePage, onSelectPage }: SideNavProps) {
  return (
    <aside className="side-nav">
      <div className="side-nav__brand">
        <div className="side-nav__title">Telemetry Driver App</div>
        <div className="side-nav__subtitle">Shell + shared dashboard</div>
      </div>

      <div className="side-nav__actions">
        <button
          className={activePage === "home" ? "nav-button nav-button--active" : "nav-button"}
          onClick={() => onSelectPage("home")}
        >
          Home
        </button>

        <button
          className={activePage === "dashboard" ? "nav-button nav-button--active" : "nav-button"}
          onClick={() => onSelectPage("dashboard")}
        >
          Dashboard
        </button>
      </div>
    </aside>
  );
}
