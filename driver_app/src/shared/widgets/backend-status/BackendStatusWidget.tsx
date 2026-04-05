import React from "react";
import { WidgetFrame } from "../../components/WidgetFrame";

export function BackendStatusWidget() {
    return (
        <WidgetFrame title="Backend Status">
            <div className="placeholder-copy">
                Shared backend widget placeholder. Later this can show source, connection health, mode, and update cadence.
            </div>
        </WidgetFrame>
    );
}