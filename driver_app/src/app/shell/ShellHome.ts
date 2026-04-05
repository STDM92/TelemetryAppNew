import { getAppConfig, updateAppConfig } from "../api/configClient";
import { getSidecarProcessState } from "../api/processClient";
import { fetchRuntimeStatus } from "../api/runtimeClient";
import type { BootstrapConfig, SidecarProcessState } from "../../types/api";
import { getBootstrapConfig } from "../api/bootstrap";
import { connectTelemetryStream } from "../api/telemetryStreamClient";

function formatExcerpt(state: Record<string, unknown> | null): string {
  if (!state || typeof state !== "object") {
    return "No state available";
  }

  const session = (state.session as Record<string, unknown> | undefined) ?? {};
  const lap = (state.lap as Record<string, unknown> | undefined) ?? {};
  const powertrain = (state.powertrain as Record<string, unknown> | undefined) ?? {};

  return JSON.stringify(
      {
        source: state.source ?? null,
        session_phase: session.session_phase ?? null,
        current_lap: lap.current_lap ?? null,
        speed_kph: powertrain.vehicle_speed_kph ?? null,
        gear: powertrain.gear ?? null,
      },
      null,
      2
  );
}

function formatProcessStatusLabel(status: SidecarProcessState["status"]): string {
  switch (status) {
    case "not_running":
      return "Not running";
    case "running":
      return "Running";
    case "exited":
      return "Exited";
    default:
      return status;
  }
}

function renderProcessState(state: SidecarProcessState): string {
  const lines = [
    `Status: ${formatProcessStatusLabel(state.status)}`,
    `PID: ${state.pid ?? "—"}`,
    `Exit code: ${state.exitCode ?? "—"}`,
    `Last error: ${state.lastError ?? "—"}`,
    `Last exit reason: ${state.lastExitReason ?? "—"}`,
    `stdout tail lines: ${state.stdoutTail.length}`,
    `stderr tail lines: ${state.stderrTail.length}`,
  ];

  return lines.join("\n");
}

export function mountShell(root: HTMLElement, config: BootstrapConfig): void {
  const POLL_INTERVAL_MS = 1000;

  let currentBootstrap = config;
  let isConfigActionInFlight = false;
  let latestProcessState: SidecarProcessState | null = null;
  let telemetryDisconnect: (() => void) | null = null;

  root.innerHTML = `
  <div class="app-shell">
    <h1>Driver App</h1>
    <p class="muted">Thin local shell for the telemetry sidecar.</p>

    <section class="card">
      <h2>Launch Config</h2>
      <div class="form-grid">
        <label class="field field-wide">
          <span>Sidecar executable path</span>
          <input id="sidecarExecutablePathInput" type="text" />
        </label>
        <label class="field">
          <span>Backend port</span>
          <input id="backendPortInput" type="number" min="1" max="65535" />
        </label>
      </div>
      <div class="button-row">
        <button id="saveConfigButton" type="button">Apply config</button>
      </div>
      <p class="muted" id="configStatusText">
        Sidecar is managed automatically by the app. Config changes apply on next launch.
      </p>
    </section>

    <section class="card">
      <h2>Bootstrap</h2>
      <div><strong>Mode:</strong> <span id="mode"></span></div>
      <div><strong>Backend:</strong> <span id="backend"></span></div>
      <div><strong>WebSocket:</strong> <span id="ws"></span></div>
    </section>

    <section class="card">
      <h2>Sidecar Process</h2>
      <div class="process-summary">
        <div><strong>Status:</strong> <span id="processStatusValue">loading...</span></div>
        <div><strong>PID:</strong> <span id="processPidValue">—</span></div>
        <div><strong>Exit code:</strong> <span id="processExitCodeValue">—</span></div>
        <div><strong>Last error:</strong> <span id="processLastErrorValue">—</span></div>
        <div><strong>Last exit reason:</strong> <span id="processLastExitReasonValue">—</span></div>
      </div>
      <pre id="processState">loading...</pre>
    </section>

    <section class="card">
      <h2>Sidecar Status</h2>
      <div><strong>Status:</strong> <span id="statusValue">loading...</span></div>
      <div><strong>Last error:</strong> <span id="statusError">—</span></div>
    </section>

    <section class="card">
      <h2>State Excerpt</h2>
      <pre id="stateExcerpt">loading...</pre>
    </section>
  </div>
`;

  const modeValue = document.getElementById("mode") as HTMLElement;
  const backendValue = document.getElementById("backend") as HTMLElement;
  const wsValue = document.getElementById("ws") as HTMLElement;

  const processState = document.getElementById("processState") as HTMLElement;
  const processStatusValue = document.getElementById("processStatusValue") as HTMLElement;
  const processPidValue = document.getElementById("processPidValue") as HTMLElement;
  const processExitCodeValue = document.getElementById("processExitCodeValue") as HTMLElement;
  const processLastErrorValue = document.getElementById("processLastErrorValue") as HTMLElement;
  const processLastExitReasonValue = document.getElementById("processLastExitReasonValue") as HTMLElement;
  const statusValue = document.getElementById("statusValue") as HTMLElement;
  const statusError = document.getElementById("statusError") as HTMLElement;
  const stateExcerpt = document.getElementById("stateExcerpt") as HTMLElement;

  const sidecarExecutablePathInput = document.getElementById(
      "sidecarExecutablePathInput"
  ) as HTMLInputElement;
  const backendPortInput = document.getElementById("backendPortInput") as HTMLInputElement;
  const saveConfigButton = document.getElementById("saveConfigButton") as HTMLButtonElement;
  const configStatusText = document.getElementById("configStatusText") as HTMLElement;

  function applyBootstrapConfig(bootstrap: BootstrapConfig): void {
    currentBootstrap = bootstrap;
    modeValue.textContent = bootstrap.mode;
    backendValue.textContent = bootstrap.backendBaseUrl;
    wsValue.textContent = bootstrap.backendWebsocketUrl;
  }

  function updateButtons(): void {
    saveConfigButton.disabled = isConfigActionInFlight;
  }

  function applyProcessState(state: SidecarProcessState): void {
    latestProcessState = state;
    processState.textContent = renderProcessState(state);
    processStatusValue.textContent = formatProcessStatusLabel(state.status);
    processPidValue.textContent = state.pid == null ? "—" : String(state.pid);
    processExitCodeValue.textContent = state.exitCode == null ? "—" : String(state.exitCode);
    processLastErrorValue.textContent = state.lastError ?? "—";
    processLastExitReasonValue.textContent = state.lastExitReason ?? "—";
  }

  function applyTelemetrySnapshot(snapshot: Record<string, unknown> | null): void {
    stateExcerpt.textContent = formatExcerpt(snapshot);
  }

  function stopTelemetryStream(): void {
    telemetryDisconnect?.();
    telemetryDisconnect = null;
  }

  function ensureTelemetryStream(): void {
    if (telemetryDisconnect) {
      return;
    }

    stateExcerpt.textContent = "Connecting to telemetry stream...";
    telemetryDisconnect = connectTelemetryStream(currentBootstrap.backendWebsocketUrl, {
      onOpen: () => {
        stateExcerpt.textContent = "Waiting for telemetry frame...";
      },
      onSnapshot: (snapshot) => {
        applyTelemetrySnapshot(snapshot);
      },
      onClose: () => {
        stateExcerpt.textContent = "Telemetry stream disconnected. Reconnecting...";
      },
      onError: () => {
        stateExcerpt.textContent = "Telemetry stream error. Waiting to reconnect...";
      },
    });
  }

  async function loadAppConfig(): Promise<void> {
    try {
      const appConfig = await getAppConfig();
      sidecarExecutablePathInput.value = appConfig.sidecarExecutablePath;
      backendPortInput.value = String(appConfig.backendPort);
    } catch (error) {
      configStatusText.textContent = `Failed to load config: ${String(error)}`;
    }
  }

  async function refreshProcessState(): Promise<void> {
    try {
      const state = await getSidecarProcessState();
      applyProcessState(state);
    } catch (error) {
      processState.textContent = `Failed to load process state: ${String(error)}`;
      processStatusValue.textContent = "Unknown";
      processPidValue.textContent = "—";
      processExitCodeValue.textContent = "—";
      processLastErrorValue.textContent = String(error);
      processLastExitReasonValue.textContent = "—";
    }
  }

  async function refreshRuntimeStatus(): Promise<void> {
    await refreshProcessState();

    if (latestProcessState?.status !== "running") {
      statusValue.textContent = "not_running";
      statusError.textContent = latestProcessState?.lastError ?? "—";
      stopTelemetryStream();
      stateExcerpt.textContent = "Sidecar process is not running.";
      return;
    }

    try {
      const status = await fetchRuntimeStatus(currentBootstrap.backendBaseUrl);
      statusValue.textContent = status.status;
      statusError.textContent = status.last_error ?? "—";

      if (status.status !== "attached" && status.status !== "streaming") {
        stopTelemetryStream();
        stateExcerpt.textContent = "No telemetry source attached yet.";
        return;
      }

      ensureTelemetryStream();
    } catch (error) {
      statusValue.textContent = "unreachable";
      statusError.textContent = String(error);
      stopTelemetryStream();
      stateExcerpt.textContent = "Failed to connect to telemetry stream.";
    }
  }

  saveConfigButton.addEventListener("click", () => {
    void (async () => {
      if (isConfigActionInFlight) {
        return;
      }

      isConfigActionInFlight = true;
      configStatusText.textContent = "Applying config...";
      updateButtons();

      try {
        const backendPort = Number(backendPortInput.value);
        if (!Number.isInteger(backendPort) || backendPort < 1 || backendPort > 65535) {
          throw new Error("Backend port must be an integer between 1 and 65535.");
        }

        const sidecarExecutablePath = sidecarExecutablePathInput.value.trim();
        if (!sidecarExecutablePath) {
          throw new Error("Sidecar executable path is required.");
        }

        const updated = await updateAppConfig({
          sidecarExecutablePath,
          backendPort,
        });

        sidecarExecutablePathInput.value = updated.sidecarExecutablePath;
        backendPortInput.value = String(updated.backendPort);
        configStatusText.textContent =
            "Config applied. Changes will be used on next app launch.";

        const refreshedBootstrap = await getBootstrapConfig();
        applyBootstrapConfig(refreshedBootstrap);
        stopTelemetryStream();
        await refreshRuntimeStatus();
      } catch (error) {
        configStatusText.textContent = `Failed to apply config: ${String(error)}`;
      } finally {
        isConfigActionInFlight = false;
        updateButtons();
      }
    })();
  });

  applyBootstrapConfig(config);
  updateButtons();
  void loadAppConfig();
  void refreshRuntimeStatus();
  window.setInterval(() => void refreshRuntimeStatus(), POLL_INTERVAL_MS);
}