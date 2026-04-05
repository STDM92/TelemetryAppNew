import React from "react";
import type { DashboardNavItem, DashboardViewId } from "./dashboardTypes";

type DashboardSidebarProps = {
    activeView: DashboardViewId;
    onSelectView: (view: DashboardViewId) => void;
};

const NAV_ITEMS: DashboardNavItem[] = [
    { id: "telemetry", label: "Telemetry", shortLabel: "TEL" },
    { id: "standings", label: "Standings", shortLabel: "STD" },
    { id: "pits", label: "Pits", shortLabel: "PIT" },
];

export function DashboardSidebar({ activeView, onSelectView }: DashboardSidebarProps) {
    return (
        <aside className="dashboard-sidebar">
            <div className="dashboard-sidebar__brand">
                <div className="dashboard-sidebar__badge">Telemetry</div>
            </div>

            <nav className="dashboard-sidebar__nav" aria-label="Dashboard views">
                {NAV_ITEMS.map((item) => {
                    const active = item.id === activeView;

                    return (
                        <button
                            key={item.id}
                            type="button"
                            className={active ? "dashboard-nav-button dashboard-nav-button--active" : "dashboard-nav-button"}
                            onClick={() => onSelectView(item.id)}
                            title={item.label}
                        >
                            <span className="dashboard-nav-button__icon">{item.shortLabel}</span>
                            <span className="dashboard-nav-button__label">{item.label}</span>
                        </button>
                    );
                })}
            </nav>
        </aside>
    );
}