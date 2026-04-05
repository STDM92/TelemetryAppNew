from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


FILES: dict[str, str] = {
    "src/main.ts": dedent(
        """
        import React from "react";
        import ReactDOM from "react-dom/client";
        import App from "./App";
        import "./styles/app.css";

        ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
          <React.StrictMode>
            <App />
          </React.StrictMode>,
        );
        """
    ).strip()
                   + "\n",
    "src/App.tsx": dedent(
        """
        import React from "react";
        import { DriverShell } from "./app/shell/DriverShell";

        export default function App() {
          return <DriverShell />;
        }
        """
    ).strip()
                   + "\n",
    "src/app/bootstrap/bootstrapTypes.ts": dedent(
        """
        export type BootstrapConfig = {
          backendBaseUrl: string;
          backendWebSocketUrl: string;
          mode: string;
        };
        """
    ).strip()
                                           + "\n",
    "src/app/bootstrap/getBootstrapConfig.ts": dedent(
        """
        import type { BootstrapConfig } from "./bootstrapTypes";

        declare global {
          interface Window {
            __APP_CONFIG__?: Partial<BootstrapConfig>;
          }
        }

        export async function getBootstrapConfig(): Promise<BootstrapConfig> {
          const injected = window.__APP_CONFIG__ ?? {};

          return {
            backendBaseUrl: injected.backendBaseUrl ?? "http://127.0.0.1:8000",
            backendWebSocketUrl: injected.backendWebSocketUrl ?? "ws://127.0.0.1:8000/ws",
            mode: injected.mode ?? "live",
          };
        }
        """
    ).strip()
                                               + "\n",
    "src/app/local-api/runtimeClient.ts": dedent(
        """
        export type RuntimeStatus = {
          status: string;
          last_error?: string | null;
        };

        export async function fetchRuntimeStatus(baseUrl: string): Promise<RuntimeStatus> {
          const response = await fetch(`${baseUrl}/health`, { cache: "no-store" });

          if (!response.ok) {
            throw new Error(`Failed to fetch runtime status: ${response.status}`);
          }

          return (await response.json()) as RuntimeStatus;
        }
        """
    ).strip()
                                          + "\n",
    "src/app/local-api/stateClient.ts": dedent(
        """
        import type { TelemetrySnapshot } from "../../shared/telemetry/telemetryTypes";

        export async function fetchCurrentState(baseUrl: string): Promise<TelemetrySnapshot | null> {
          const response = await fetch(`${baseUrl}/api/state`, { cache: "no-store" });

          if (!response.ok) {
            throw new Error(`Failed to fetch current state: ${response.status}`);
          }

          return (await response.json()) as TelemetrySnapshot | null;
        }
        """
    ).strip()
                                        + "\n",
    "src/app/local-api/processClient.ts": dedent(
        """
        export type SidecarProcessState = {
          status: string;
          pid?: number | null;
          exitCode?: number | null;
          lastError?: string | null;
        };

        export async function getSidecarProcessState(): Promise<SidecarProcessState> {
          return {
            status: "unknown",
            pid: null,
            exitCode: null,
            lastError: null,
          };
        }
        """
    ).strip()
                                          + "\n",
    "src/app/local-api/configClient.ts": dedent(
        """
        import { getBootstrapConfig } from "../bootstrap/getBootstrapConfig";

        export async function getResolvedBackendBaseUrl(): Promise<string> {
          const config = await getBootstrapConfig();
          return config.backendBaseUrl;
        }
        """
    ).strip()
                                         + "\n",
    "src/app/shell/DriverShell.tsx": dedent(
        """
        import React, { useState } from "react";
        import { DashboardPage } from "./pages/DashboardPage";
        import { ShellHomePage } from "./pages/ShellHomePage";
        import { SideNav } from "./components/SideNav";

        export type ShellPageId = "home" | "dashboard";

        export function DriverShell() {
          const [activePage, setActivePage] = useState<ShellPageId>("home");

          return (
            <div className="app-shell">
              <SideNav activePage={activePage} onSelectPage={setActivePage} />
              <main className="app-shell__main">
                {activePage === "home" ? <ShellHomePage /> : <DashboardPage />}
              </main>
            </div>
          );
        }
        """
    ).strip()
                                     + "\n",
    "src/app/shell/components/SideNav.tsx": dedent(
        """
        import React from "react";
        import type { ShellPageId } from "../DriverShell";

        type SideNavProps = {
          activePage: ShellPageId;
          onSelectPage: (page: ShellPageId) => void;
        };

        export function SideNav({ activePage, onSelectPage }: SideNavProps) {
          return (
            <aside className="side-nav">
              <div className="side-nav__brand">
                <div className="side-nav__title">Telemetry Driver App</div>
                <div className="side-nav__subtitle">Shell + shared dashboard</div>
              </div>

              <div className="side-nav__actions">
                <button
                  className={activePage === "home" ? "nav-button nav-button--active" : "nav-button"}
                  onClick={() => onSelectPage("home")}
                >
                  Home
                </button>

                <button
                  className={activePage === "dashboard" ? "nav-button nav-button--active" : "nav-button"}
                  onClick={() => onSelectPage("dashboard")}
                >
                  Dashboard
                </button>
              </div>
            </aside>
          );
        }
        """
    ).strip()
                                            + "\n",
    "src/app/shell/components/SidecarStatusCard.tsx": dedent(
        """
        import React from "react";
        import type { RuntimeStatus } from "../../local-api/runtimeClient";

        type SidecarStatusCardProps = {
          runtimeStatus: RuntimeStatus | null;
          errorText: string | null;
        };

        export function SidecarStatusCard({ runtimeStatus, errorText }: SidecarStatusCardProps) {
          return (
            <section className="card">
              <h2 className="card__title">Sidecar Status</h2>
              <div className="kv-list">
                <div className="kv-row">
                  <span className="kv-row__label">Status</span>
                  <span className="kv-row__value">{runtimeStatus?.status ?? "loading"}</span>
                </div>
                <div className="kv-row">
                  <span className="kv-row__label">Last Error</span>
                  <span className="kv-row__value">{errorText ?? runtimeStatus?.last_error ?? "none"}</span>
                </div>
              </div>
            </section>
          );
        }
        """
    ).strip()
                                                      + "\n",
    "src/app/shell/components/ProcessStateCard.tsx": dedent(
        """
        import React from "react";
        import type { SidecarProcessState } from "../../local-api/processClient";

        type ProcessStateCardProps = {
          processState: SidecarProcessState | null;
        };

        export function ProcessStateCard({ processState }: ProcessStateCardProps) {
          return (
            <section className="card">
              <h2 className="card__title">Process State</h2>
              <div className="kv-list">
                <div className="kv-row">
                  <span className="kv-row__label">Status</span>
                  <span className="kv-row__value">{processState?.status ?? "unknown"}</span>
                </div>
                <div className="kv-row">
                  <span className="kv-row__label">PID</span>
                  <span className="kv-row__value">{processState?.pid ?? "n/a"}</span>
                </div>
                <div className="kv-row">
                  <span className="kv-row__label">Exit Code</span>
                  <span className="kv-row__value">{processState?.exitCode ?? "n/a"}</span>
                </div>
              </div>
            </section>
          );
        }
        """
    ).strip()
                                                     + "\n",
    "src/app/shell/pages/ShellHomePage.tsx": dedent(
        """
        import React, { useEffect, useState } from "react";
        import { getBootstrapConfig } from "../../bootstrap/getBootstrapConfig";
        import { getSidecarProcessState, type SidecarProcessState } from "../../local-api/processClient";
        import { fetchRuntimeStatus, type RuntimeStatus } from "../../local-api/runtimeClient";
        import { ProcessStateCard } from "../components/ProcessStateCard";
        import { SidecarStatusCard } from "../components/SidecarStatusCard";

        export function ShellHomePage() {
          const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus | null>(null);
          const [processState, setProcessState] = useState<SidecarProcessState | null>(null);
          const [errorText, setErrorText] = useState<string | null>(null);
          const [backendBaseUrl, setBackendBaseUrl] = useState<string>("loading...");
          const [backendWebSocketUrl, setBackendWebSocketUrl] = useState<string>("loading...");
          const [mode, setMode] = useState<string>("loading...");

          useEffect(() => {
            let isDisposed = false;

            async function load() {
              try {
                const config = await getBootstrapConfig();

                if (isDisposed) {
                  return;
                }

                setBackendBaseUrl(config.backendBaseUrl);
                setBackendWebSocketUrl(config.backendWebSocketUrl);
                setMode(config.mode);

                const [runtime, process] = await Promise.all([
                  fetchRuntimeStatus(config.backendBaseUrl),
                  getSidecarProcessState(),
                ]);

                if (isDisposed) {
                  return;
                }

                setRuntimeStatus(runtime);
                setProcessState(process);
                setErrorText(null);
              } catch (error) {
                if (isDisposed) {
                  return;
                }

                setErrorText(error instanceof Error ? error.message : String(error));
              }
            }

            void load();
            const handle = window.setInterval(() => void load(), 1500);

            return () => {
              isDisposed = true;
              window.clearInterval(handle);
            };
          }, []);

          return (
            <div className="page-stack">
              <header className="page-header">
                <h1 className="page-header__title">Driver Shell</h1>
                <p className="page-header__text">
                  Local app status, process ownership, and runtime overview.
                </p>
              </header>

              <section className="card">
                <h2 className="card__title">Bootstrap</h2>
                <div className="kv-list">
                  <div className="kv-row">
                    <span className="kv-row__label">Backend Base URL</span>
                    <span className="kv-row__value">{backendBaseUrl}</span>
                  </div>
                  <div className="kv-row">
                    <span className="kv-row__label">Backend WebSocket URL</span>
                    <span className="kv-row__value">{backendWebSocketUrl}</span>
                  </div>
                  <div className="kv-row">
                    <span className="kv-row__label">Mode</span>
                    <span className="kv-row__value">{mode}</span>
                  </div>
                </div>
              </section>

              <div className="card-grid">
                <SidecarStatusCard runtimeStatus={runtimeStatus} errorText={errorText} />
                <ProcessStateCard processState={processState} />
              </div>
            </div>
          );
        }
        """
    ).strip()
                                             + "\n",
    "src/app/shell/pages/DashboardPage.tsx": dedent(
        """
        import React from "react";
        import { DashboardView } from "../../../shared/dashboard/DashboardView";

        export function DashboardPage() {
          return (
            <div className="page-stack">
              <header className="page-header">
                <h1 className="page-header__title">Dashboard</h1>
                <p className="page-header__text">
                  Shared dashboard surface intended to work in both the driver app and the future web UI.
                </p>
              </header>

              <DashboardView />
            </div>
          );
        }
        """
    ).strip()
                                             + "\n",
    "src/shared/components/WidgetFrame.tsx": dedent(
        """
        import React from "react";

        type WidgetFrameProps = {
          title: string;
          children: React.ReactNode;
        };

        export function WidgetFrame({ title, children }: WidgetFrameProps) {
          return (
            <section className="card">
              <h2 className="card__title">{title}</h2>
              {children}
            </section>
          );
        }
        """
    ).strip()
                                             + "\n",
    "src/shared/dashboard/widgetTypes.ts": dedent(
        """
        import type { ReactNode } from "react";

        export type WidgetDefinition = {
          id: string;
          title: string;
          render: () => ReactNode;
        };
        """
    ).strip()
                                           + "\n",
    "src/shared/dashboard/widgetCapability.ts": dedent(
        """
        export type WidgetCapability = "shell" | "dashboard" | "telemetry";
        """
    ).strip()
                                                + "\n",
    "src/shared/dashboard/widgetRegistry.ts": dedent(
        """
        import { backendStatusWidgetDefinition } from "../widgets/backend-status/definition";
        import { driverInputsWidgetDefinition } from "../widgets/driver-inputs/definition";
        import { sessionSummaryWidgetDefinition } from "../widgets/session-summary/definition";
        import type { WidgetDefinition } from "./widgetTypes";

        export const widgetRegistry: WidgetDefinition[] = [
          sessionSummaryWidgetDefinition,
          driverInputsWidgetDefinition,
          backendStatusWidgetDefinition,
        ];
        """
    ).strip()
                                              + "\n",
    "src/shared/dashboard/DashboardView.tsx": dedent(
        """
        import React from "react";
        import { widgetRegistry } from "./widgetRegistry";

        export function DashboardView() {
          return (
            <div className="widget-grid">
              {widgetRegistry.map((widget) => (
                <React.Fragment key={widget.id}>{widget.render()}</React.Fragment>
              ))}
            </div>
          );
        }
        """
    ).strip()
                                              + "\n",
    "src/shared/widgets/session-summary/SessionSummaryWidget.tsx": dedent(
        """
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
        """
    ).strip()
                                                                   + "\n",
    "src/shared/widgets/session-summary/definition.ts": dedent(
        """
        import React from "react";
        import { SessionSummaryWidget } from "./SessionSummaryWidget";
        import type { WidgetDefinition } from "../../dashboard/widgetTypes";

        export const sessionSummaryWidgetDefinition: WidgetDefinition = {
          id: "session-summary",
          title: "Session Summary",
          render: () => <SessionSummaryWidget />,
        };
        """
    ).strip()
                                                        + "\n",
    "src/shared/widgets/driver-inputs/DriverInputsWidget.tsx": dedent(
        """
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
        """
    ).strip()
                                                               + "\n",
    "src/shared/widgets/driver-inputs/definition.ts": dedent(
        """
        import React from "react";
        import { DriverInputsWidget } from "./DriverInputsWidget";
        import type { WidgetDefinition } from "../../dashboard/widgetTypes";

        export const driverInputsWidgetDefinition: WidgetDefinition = {
          id: "driver-inputs",
          title: "Driver Inputs",
          render: () => <DriverInputsWidget />,
        };
        """
    ).strip()
                                                      + "\n",
    "src/shared/widgets/backend-status/BackendStatusWidget.tsx": dedent(
        """
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
        """
    ).strip()
                                                                 + "\n",
    "src/shared/widgets/backend-status/definition.ts": dedent(
        """
        import React from "react";
        import { BackendStatusWidget } from "./BackendStatusWidget";
        import type { WidgetDefinition } from "../../dashboard/widgetTypes";

        export const backendStatusWidgetDefinition: WidgetDefinition = {
          id: "backend-status",
          title: "Backend Status",
          render: () => <BackendStatusWidget />,
        };
        """
    ).strip()
                                                       + "\n",
    "src/shared/telemetry/telemetryTypes.ts": dedent(
        """
        export type TelemetrySnapshot = {
          source?: string | null;
          session_phase?: string | null;
          current_lap?: number | null;
          vehicle_speed_kph?: number | null;
          gear?: number | null;
          throttle?: number | null;
          brake?: number | null;
          clutch?: number | null;
          steering_angle_deg?: number | null;
        };
        """
    ).strip()
                                              + "\n",
    "src/shared/telemetry/useTelemetrySnapshot.ts": dedent(
        """
        import { useEffect, useState } from "react";
        import type { TelemetrySnapshot } from "./telemetryTypes";

        export function useTelemetrySnapshot(): {
          snapshot: TelemetrySnapshot | null;
          isConnected: boolean;
        } {
          const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
          const [isConnected, setIsConnected] = useState(false);

          useEffect(() => {
            setIsConnected(false);
            setSnapshot(null);
          }, []);

          return {
            snapshot,
            isConnected,
          };
        }
        """
    ).strip()
                                                    + "\n",
    "src/styles/app.css": dedent(
        """
        :root {
          color-scheme: dark;
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          line-height: 1.5;
          font-weight: 400;
          background: #0b0d16;
          color: #e5e7eb;
        }

        * {
          box-sizing: border-box;
        }

        html,
        body,
        #root {
          margin: 0;
          min-height: 100%;
          width: 100%;
        }

        body {
          background:
            radial-gradient(circle at top left, rgba(59, 130, 246, 0.14), transparent 28%),
            linear-gradient(180deg, #0b0d16 0%, #0a0f1f 100%);
          color: #e5e7eb;
        }

        button,
        input,
        textarea,
        select {
          font: inherit;
        }

        .app-shell {
          display: flex;
          min-height: 100vh;
        }

        .app-shell__main {
          flex: 1;
          padding: 24px;
        }

        .side-nav {
          width: 260px;
          flex-shrink: 0;
          border-right: 1px solid rgba(255, 255, 255, 0.06);
          background: rgba(13, 16, 32, 0.92);
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .side-nav__brand {
          display: grid;
          gap: 4px;
        }

        .side-nav__title {
          font-size: 14px;
          font-weight: 700;
        }

        .side-nav__subtitle {
          font-size: 12px;
          color: #94a3b8;
        }

        .side-nav__actions {
          display: grid;
          gap: 10px;
        }

        .nav-button {
          width: 100%;
          text-align: left;
          padding: 12px 14px;
          border-radius: 12px;
          border: 1px solid rgba(255, 255, 255, 0.08);
          background: transparent;
          color: #cbd5e1;
          cursor: pointer;
          transition: background-color 140ms ease, border-color 140ms ease, color 140ms ease;
        }

        .nav-button:hover {
          border-color: rgba(96, 165, 250, 0.4);
          background: rgba(96, 165, 250, 0.08);
        }

        .nav-button--active {
          background: rgba(96, 165, 250, 0.16);
          border-color: rgba(96, 165, 250, 0.45);
          color: #dbeafe;
        }

        .page-stack {
          display: grid;
          gap: 16px;
        }

        .page-header {
          display: grid;
          gap: 6px;
        }

        .page-header__title {
          margin: 0;
          font-size: 24px;
        }

        .page-header__text {
          margin: 0;
          color: #94a3b8;
        }

        .card-grid {
          display: grid;
          gap: 16px;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        }

        .widget-grid {
          display: grid;
          gap: 16px;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }

        .card {
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
          padding: 16px;
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(6px);
        }

        .card__title {
          margin: 0 0 12px 0;
          font-size: 16px;
        }

        .kv-list {
          display: grid;
          gap: 10px;
        }

        .kv-row {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          padding-bottom: 8px;
        }

        .kv-row:last-child {
          border-bottom: 0;
          padding-bottom: 0;
        }

        .kv-row__label {
          color: #94a3b8;
          white-space: nowrap;
        }

        .kv-row__value {
          text-align: right;
          word-break: break-word;
        }

        .placeholder-copy {
          color: #cbd5e1;
        }

        @media (max-width: 900px) {
          .app-shell {
            flex-direction: column;
          }

          .side-nav {
            width: 100%;
            border-right: 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
          }
        }
        """
    ).strip()
                          + "\n",
}


DIRECTORIES: list[str] = [
    "src/app/bootstrap",
    "src/app/local-api",
    "src/app/shell/components",
    "src/app/shell/pages",
    "src/shared/components",
    "src/shared/dashboard",
    "src/shared/widgets/session-summary",
    "src/shared/widgets/driver-inputs",
    "src/shared/widgets/backend-status",
    "src/shared/telemetry",
    "src/styles",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a safe starter UI scaffold for the driver app frontend."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(""),
        help="Path to the driver_app repo root. Defaults to current directory.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite files managed by this scaffold script.",
    )
    return parser.parse_args()


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    print(f"[dir]  ensured {path}")


def write_file(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        print(f"[skip] exists   {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    action = "wrote" if overwrite or path.exists() else "created"
    print(f"[file] {action:<8} {path}")


def validate_root(root: Path) -> None:
    expected = [
        root / "package.json",
        root / "src",
        root / "src-tauri",
        ]

    missing = [str(path) for path in expected if not path.exists()]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(
            f"Refusing to run because this does not look like the driver_app root. Missing: {joined}"
        )


def main() -> int:
    args = parse_args()
    root = args.root.resolve()

    validate_root(root)

    print(f"[info] repo root: {root}")
    print(f"[info] overwrite: {args.overwrite}")

    for directory in DIRECTORIES:
        ensure_directory(root / directory)

    for relative_path, content in FILES.items():
        write_file(root / relative_path, content, overwrite=args.overwrite)

    print("[done] UI scaffold complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())