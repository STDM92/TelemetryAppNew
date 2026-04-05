import React, { useEffect, useMemo, useRef, useState } from "react";
import { getBootstrapConfig } from "../bootstrap/getBootstrapConfig";
import { getSidecarProcessState, type SidecarProcessState } from "../local-api/processClient";
import { fetchBackendStatus, type BackendStatus } from "../local-api/statusClient";
import { fetchCurrentState } from "../local-api/stateClient";
import type { TelemetrySnapshot } from "../../shared/telemetry/telemetryTypes";
import { DashboardPage } from "./pages/DashboardPage";
import { ShellHomePage } from "./pages/ShellHomePage";
import { StartupPage, type StartupViewModel } from "./pages/StartupPage";

type ShellSurface = "startup" | "dashboard" | "control";

const SHOW_DEV_CONTROL_PAGE = false;
const POLL_INTERVAL_MS = 1500;
const CONNECTED_SUCCESS_HOLD_MS = 4000;

function buildStartupViewModel(args: {
    processState: SidecarProcessState | null;
    backendStatus: BackendStatus | null;
    errorText: string | null;
}): StartupViewModel {
    const { processState, backendStatus, errorText } = args;

    if (errorText) {
        return {
            stage: "failed",
            title: "Startup problem detected",
            subtitle: errorText,
            detectedSim: null,
        };
    }

    if (processState?.status === "exited") {
        return {
            stage: "failed",
            title: "Telemetry service exited",
            subtitle:
                processState.lastError ??
                processState.lastExitReason ??
                "The sidecar exited before the app could attach.",
            detectedSim: null,
        };
    }

    if (processState?.status === "not_running" && processState.lastError) {
        return {
            stage: "failed",
            title: "Failed to start telemetry service",
            subtitle: processState.lastError,
            detectedSim: null,
        };
    }

    if (backendStatus?.status === "failed") {
        return {
            stage: "failed",
            title: "Backend runtime failed",
            subtitle: backendStatus.last_error ?? "The telemetry backend reported a failure state.",
            detectedSim: null,
        };
    }

    if (
        backendStatus?.status === "running" &&
        backendStatus.source_attachment_state === "attached"
    ) {
        const displayName =
            backendStatus.source_display_name?.trim() ||
            backendStatus.sim?.trim() ||
            "simulator";

        return {
            stage: "connected",
            title: `Successfully connected to ${displayName}`,
            subtitle:
                backendStatus.stream_state === "streaming"
                    ? "Telemetry stream detected. Preparing dashboard..."
                    : "Simulator detected. Preparing dashboard...",
            detectedSim: displayName,
        };
    }

    if (
        processState?.status === "running" &&
        backendStatus?.status === "running" &&
        backendStatus.source_attachment_state === "waiting"
    ) {
        return {
            stage: "waiting_for_sim",
            title: "Looking for running simulator",
            subtitle: "Telemetry service is running. Waiting for a supported sim to attach.",
            detectedSim: null,
        };
    }

    return {
        stage: "booting",
        title: "Starting telemetry service",
        subtitle: "Initializing local runtime and checking backend availability.",
        detectedSim: null,
    };
}

export function DriverShell() {
    const [surface, setSurface] = useState<ShellSurface>("startup");
    const [processState, setProcessState] = useState<SidecarProcessState | null>(null);
    const [backendStatus, setBackendStatus] = useState<BackendStatus | null>(null);
    const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
    const [errorText, setErrorText] = useState<string | null>(null);

    const connectedTimerRef = useRef<number | null>(null);
    const hasTransitionedToDashboardRef = useRef(false);

    useEffect(() => {
        let isDisposed = false;

        async function load() {
            try {
                const config = await getBootstrapConfig();
                const process = await getSidecarProcessState();

                if (isDisposed) {
                    return;
                }

                setProcessState(process);

                if (process.status !== "running") {
                    setBackendStatus(null);
                    setSnapshot(null);
                    setErrorText(null);
                    hasTransitionedToDashboardRef.current = false;
                    return;
                }

                const status = await fetchBackendStatus(config.backendBaseUrl);

                if (isDisposed) {
                    return;
                }

                setBackendStatus(status);

                if (
                    status.status === "running" &&
                    status.source_attachment_state === "attached" &&
                    (status.stream_state === "streaming" || status.has_received_snapshot)
                ) {
                    try {
                        const currentState = await fetchCurrentState(config.backendBaseUrl);

                        if (isDisposed) {
                            return;
                        }

                        setSnapshot(currentState);
                    } catch {
                        if (isDisposed) {
                            return;
                        }

                        setSnapshot(null);
                    }
                } else {
                    setSnapshot(null);
                }

                setErrorText(null);
            } catch (error) {
                if (isDisposed) {
                    return;
                }

                setBackendStatus(null);
                setSnapshot(null);
                setErrorText(error instanceof Error ? error.message : String(error));
                hasTransitionedToDashboardRef.current = false;
            }
        }

        void load();
        const handle = window.setInterval(() => void load(), POLL_INTERVAL_MS);

        return () => {
            isDisposed = true;
            window.clearInterval(handle);

            if (connectedTimerRef.current !== null) {
                window.clearTimeout(connectedTimerRef.current);
            }
        };
    }, []);

    const startupViewModel = useMemo(
        () =>
            buildStartupViewModel({
                processState,
                backendStatus,
                errorText,
            }),
        [processState, backendStatus, errorText],
    );

    useEffect(() => {
        if (surface === "control") {
            return;
        }

        if (startupViewModel.stage !== "connected") {
            if (connectedTimerRef.current !== null) {
                window.clearTimeout(connectedTimerRef.current);
                connectedTimerRef.current = null;
            }

            if (!hasTransitionedToDashboardRef.current) {
                setSurface("startup");
            }

            return;
        }

        if (hasTransitionedToDashboardRef.current) {
            return;
        }

        if (connectedTimerRef.current !== null) {
            window.clearTimeout(connectedTimerRef.current);
        }

        setSurface("startup");

        connectedTimerRef.current = window.setTimeout(() => {
            hasTransitionedToDashboardRef.current = true;
            setSurface("dashboard");
        }, CONNECTED_SUCCESS_HOLD_MS);
    }, [startupViewModel.stage, surface]);

    if (surface === "dashboard") {
        return (
            <div className="app-screen">
                <DashboardPage snapshot={snapshot} backendStatus={backendStatus} />
            </div>
        );
    }

    if (surface === "control" && SHOW_DEV_CONTROL_PAGE) {
        return (
            <div className="app-shell">
                <main className="app-shell__main">
                    <ShellHomePage />
                </main>
            </div>
        );
    }

    return (
        <div className="app-screen">
            <StartupPage model={startupViewModel} />
        </div>
    );
}