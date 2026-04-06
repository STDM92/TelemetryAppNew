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
