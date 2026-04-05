import React, { useState } from "react";
import { DashboardPage } from "./pages/DashboardPage";
import { ShellHomePage } from "./pages/ShellHomePage";
import { SideNav } from "./components/SideNav";

export type ShellPageId = "home" | "dashboard";

export function DriverShell() {
  const [activePage, setActivePage] = useState<ShellPageId>("home");

  return (
    <div className="app-shell">
      <SideNav activePage={activePage} onSelectPage={setActivePage} />
      <main className="app-shell__main">
        {activePage === "home" ? <ShellHomePage /> : <DashboardPage />}
      </main>
    </div>
  );
}
