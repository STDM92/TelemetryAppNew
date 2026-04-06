import React from "react";
import { StandingsInfoWidget } from "./StandingsInfoWidget";
import type { WidgetDefinition } from "../../dashboard/widgetTypes";

export const standingsInfoWidgetDefinition: WidgetDefinition = {
  id: "standings-info",
  title: "Standings",
  render: () => <StandingsInfoWidget />,
};