import React from "react";
import { SessionSummaryWidget } from "./SessionSummaryWidget";
import type { WidgetDefinition } from "../../dashboard/widgetTypes";

export const sessionSummaryWidgetDefinition: WidgetDefinition = {
  id: "session-summary",
  title: "Session Summary",
  render: (context) => (
      <SessionSummaryWidget backendStatus={context.backendStatus} snapshot={context.snapshot} />
  ),
};