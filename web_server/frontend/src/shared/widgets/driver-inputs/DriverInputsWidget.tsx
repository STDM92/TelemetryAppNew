import React from "react";
import { WidgetFrame } from "../../components/WidgetFrame";

export function DriverInputsWidget() {
  return (
    <WidgetFrame title="Driver Inputs">
      <div className="placeholder-copy">
        Shared inputs widget placeholder. Later this becomes throttle, brake, clutch, steering, gear, and similar.
      </div>
    </WidgetFrame>
  );
}
