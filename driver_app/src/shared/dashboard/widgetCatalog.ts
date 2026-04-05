import type { WidgetDefinition, WidgetId } from "./widgetTypes";
import { backendStatusWidgetDefinition } from "../widgets/backend-status/definition";
import { driverInputsWidgetDefinition } from "../widgets/driver-inputs/definition";
import { sessionSummaryWidgetDefinition } from "../widgets/session-summary/definition";
import { standingsInfoWidgetDefinition } from "../widgets/standings-info/definition";
import { pitInfoWidgetDefinition } from "../widgets/pit-info/definition";
import { lineChartWidgetDefinition } from "../widgets/line-chart/definition";

export const widgetCatalog: Record<WidgetId, WidgetDefinition<any>> = {
  "session-summary": sessionSummaryWidgetDefinition,
  "backend-status": backendStatusWidgetDefinition,
  "driver-inputs": driverInputsWidgetDefinition,
  "standings-info": standingsInfoWidgetDefinition,
  "pit-info": pitInfoWidgetDefinition,
  "line-chart": lineChartWidgetDefinition,
};
