import React from "react";
import { widgetRegistry } from "./widgetRegistry";

export function DashboardView() {
  return (
    <div className="widget-grid">
      {widgetRegistry.map((widget) => (
        <React.Fragment key={widget.id}>{widget.render()}</React.Fragment>
      ))}
    </div>
  );
}
