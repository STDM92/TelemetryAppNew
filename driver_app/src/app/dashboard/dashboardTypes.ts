export type DashboardViewId = "telemetry" | "standings" | "pits" | "sessionInfo";

export type DashboardNavItem = {
    id: DashboardViewId;
    label: string;
    shortLabel: string;
};