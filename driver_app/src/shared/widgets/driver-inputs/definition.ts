import React from "react";
import { DriverInputsWidget } from "./DriverInputsWidget";
import type { WidgetDefinition } from "../../dashboard/widgetTypes";

export const driverInputsWidgetDefinition: WidgetDefinition = {
  id: "driver-inputs",
  title: "Driver Inputs",
  render: () => <DriverInputsWidget />,
};
