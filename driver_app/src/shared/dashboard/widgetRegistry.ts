import { backendStatusWidgetDefinition } from "../widgets/backend-status/definition";
import { driverInputsWidgetDefinition } from "../widgets/driver-inputs/definition";
import { sessionSummaryWidgetDefinition } from "../widgets/session-summary/definition";
import type { WidgetDefinition } from "./widgetTypes";

export const widgetRegistry: WidgetDefinition[] = [
  sessionSummaryWidgetDefinition,
  driverInputsWidgetDefinition,
  backendStatusWidgetDefinition,
];