import React from "react";
import { WidgetFrame } from "../../components/WidgetFrame";

export function SessionSummaryWidget() {
  return (
    <WidgetFrame title="Session Summary">
      <div className="placeholder-copy">
        Shared session-level widget placeholder. Later this should bind to normalized telemetry/session data.
      </div>
    </WidgetFrame>
  );
}
