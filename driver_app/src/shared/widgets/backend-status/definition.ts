import React from "react";
import { BackendStatusWidget } from "./BackendStatusWidget";
import type { WidgetDefinition } from "../../dashboard/widgetTypes";

export const backendStatusWidgetDefinition: WidgetDefinition = {
  id: "backend-status",
  title: "Backend Status",
  render: () => <BackendStatusWidget />,
};
