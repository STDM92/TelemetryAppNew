import React from "react";
import { PitInfoWidget } from "./PitInfoWidget";
import type { WidgetDefinition } from "../../dashboard/widgetTypes";

export const pitInfoWidgetDefinition: WidgetDefinition = {
  id: "pit-info",
  title: "Pit Info",
  render: () => <PitInfoWidget />,
};