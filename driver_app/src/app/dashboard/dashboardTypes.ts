export type DashboardViewId = "telemetry" | "standings" | "pits";

export type DashboardNavItem = {
    id: DashboardViewId;
    label: string;
    shortLabel: string;
};