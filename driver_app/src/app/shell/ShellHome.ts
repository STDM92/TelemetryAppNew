import { getAppConfig, updateAppConfig } from "../api/configClient";
import type { BootstrapConfig, SidecarProcessState } from "../../types/api";
import {
  getSidecarProcessState,
  restartSidecar,
  startSidecar,
  stopSidecar,
} from "../api/processClient";
import { fetchRuntimeStatus } from "../api/runtimeClient";
import { fetchState } from "../api/stateClient";
import { getBootstrapConfig } from "../api/bootstrap";

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
    2,);
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
  ];

  return lines.join("\n");
}

export function mountShell(root: HTMLElement, config: BootstrapConfig): void {
  let currentBootstrap = config;
  let isProcessActionInFlight = false;
  let isConfigActionInFlight = false;
  let latestProcessState: SidecarProcessState | null = null;

  root.innerHTML = `
  <div class="app-shell">
    <h1>Driver App</h1>
    <p class="muted">Thin local shell for the telemetry sidecar.</p>

    <section class="card">
      <h2>Launch Config</h2>
      <div class="form-grid">
        <label class="field">
          <span>Python command</span>
          <input id="pythonCommandInput" type="text" />
        </label>
        <label class="field">
          <span>Backend port</span>
          <input id="backendPortInput" type="number" min="1" max="65535" />
        </label>
        <label class="field">
          <span>Mode</span>
          <select id="backendModeSelect">
            <option value="live">live</option>
            <option value="replay">replay</option>
            <option value="analyze">analyze</option>
          </select>
        </label>
        <label class="field field-wide" id="backendFileField">
          <span>Replay/analyze file path</span>
          <input id="backendFilePathInput" type="text" />
        </label>
      </div>
      <div class="button-row">
        <button id="saveConfigButton" type="button">Apply config</button>
      </div>
      <p class="muted" id="configStatusText">Changes apply on next start or restart.</p>
    </section>

    <section class="card">
      <h2>Bootstrap</h2>
      <div><strong>Mode:</strong> <span id="mode"></span></div>
      <div><strong>Backend:</strong> <span id="backend"></span></div>
      <div><strong>WebSocket:</strong> <span id="ws"></span></div>
    </section>

    <section class="card">
      <h2>Sidecar Process</h2>
      <div class="button-row">
        <button id="startSidecarButton" type="button">Start</button>
        <button id="stopSidecarButton" type="button">Stop</button>
        <button id="restartSidecarButton" type="button">Restart</button>
      </div>
      <div class="process-summary">
        <div><strong>Status:</strong> <span id="processStatusValue">loading...</span></div>
        <div><strong>PID:</strong> <span id="processPidValue">—</span></div>
        <div><strong>Exit code:</strong> <span id="processExitCodeValue">—</span></div>
        <div><strong>Last error:</strong> <span id="processLastErrorValue">—</span></div>
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

  function applyBootstrapConfig(bootstrap: BootstrapConfig): void {
    currentBootstrap = bootstrap;
    modeValue.textContent = bootstrap.mode;
    backendValue.textContent = bootstrap.backendBaseUrl;
    wsValue.textContent = bootstrap.backendWebsocketUrl;
  }

  applyBootstrapConfig(config);


  const processState = document.getElementById("processState") as HTMLElement;
  const startButton = document.getElementById("startSidecarButton") as HTMLButtonElement;
  const stopButton = document.getElementById("stopSidecarButton") as HTMLButtonElement;
  const restartButton = document.getElementById("restartSidecarButton") as HTMLButtonElement;
  const processStatusValue = document.getElementById("processStatusValue") as HTMLElement;
  const processPidValue = document.getElementById("processPidValue") as HTMLElement;
  const processExitCodeValue = document.getElementById("processExitCodeValue") as HTMLElement;
  const processLastErrorValue = document.getElementById("processLastErrorValue") as HTMLElement;
  const pythonCommandInput = document.getElementById("pythonCommandInput") as HTMLInputElement;
  const backendPortInput = document.getElementById("backendPortInput") as HTMLInputElement;
  const backendModeSelect = document.getElementById("backendModeSelect") as HTMLSelectElement;
  const backendFileField = document.getElementById("backendFileField") as HTMLElement;
  const backendFilePathInput = document.getElementById("backendFilePathInput") as HTMLInputElement;
  const saveConfigButton = document.getElementById("saveConfigButton") as HTMLButtonElement;
  const configStatusText = document.getElementById("configStatusText") as HTMLElement;


  function updateProcessButtons(): void {
    const status = latestProcessState?.status ?? "not_running";
    const disableAll = isProcessActionInFlight;

    startButton.disabled = disableAll || status === "running";
    stopButton.disabled = disableAll || status !== "running";
    restartButton.disabled = disableAll || status !== "running";
    saveConfigButton.disabled = isConfigActionInFlight;
  }

  function updateFileFieldVisibility(): void {
    const needsFile =
        backendModeSelect.value === "replay" || backendModeSelect.value === "analyze";
    backendFileField.style.display = needsFile ? "flex" : "none";
  }

  function applyProcessState(state: SidecarProcessState): void {
    latestProcessState = state;
    processState.textContent = renderProcessState(state);
    processStatusValue.textContent = formatProcessStatusLabel(state.status);
    processPidValue.textContent = state.pid == null ? "—" : String(state.pid);
    processExitCodeValue.textContent = state.exitCode == null ? "—" : String(state.exitCode);
    processLastErrorValue.textContent = state.lastError ?? "—";
    updateProcessButtons();
  }

  async function loadAppConfig(): Promise<void> {
    try {
      const appConfig = await getAppConfig();
      pythonCommandInput.value = appConfig.pythonCommand;
      backendPortInput.value = String(appConfig.backendPort);
      backendModeSelect.value = appConfig.backendMode;
      backendFilePathInput.value = appConfig.backendFilePath ?? "";
      updateFileFieldVisibility();
    } catch (error) {
      configStatusText.textContent = `Failed to load config: ${String(error)}`;
    }
  }

  backendModeSelect.addEventListener("change", updateFileFieldVisibility);


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
    }
  }

  async function runProcessAction(
    action: () => Promise<SidecarProcessState>,
    failurePrefix: string,
  ): Promise<void> {
    if (isProcessActionInFlight) {
      return;
    }

    isProcessActionInFlight = true;
    updateProcessButtons();

    void (async () => {
      try {
        const state = await action();
        applyProcessState(state);
      } catch (error) {
        processState.textContent = `${failurePrefix}: ${String(error)}`;
        processLastErrorValue.textContent = String(error);
      } finally {
        isProcessActionInFlight = false;
        updateProcessButtons();
      }
    })();
  }

  startButton.addEventListener("click", () => {
    void runProcessAction(startSidecar, "Failed to start sidecar");
    configStatusText.textContent = "Changes apply on next start or restart.";
  });

  stopButton.addEventListener("click", () => {
    void runProcessAction(stopSidecar, "Failed to stop sidecar");
    configStatusText.textContent = "Changes apply on next start or restart.";
  });

  restartButton.addEventListener("click", () => {
    void runProcessAction(restartSidecar, "Failed to restart sidecar");
    configStatusText.textContent = "Changes apply on next start or restart.";
  });

  saveConfigButton.addEventListener("click", () => {
    void (async () => {
      if (isConfigActionInFlight) return;

      isConfigActionInFlight = true;
      configStatusText.textContent = "Applying config...";
      updateProcessButtons();

      try {
        const backendPort = Number(backendPortInput.value);
        if (!Number.isInteger(backendPort) || backendPort < 1 || backendPort > 65535) {
          throw new Error("Backend port must be an integer between 1 and 65535.");
        }

        const updated = await updateAppConfig({
          pythonCommand: pythonCommandInput.value.trim() || "python",
          backendPort,
          backendMode: backendModeSelect.value as "live" | "replay" | "analyze",
          backendFilePath: backendFilePathInput.value.trim() || null,
        });

        pythonCommandInput.value = updated.pythonCommand;
        backendPortInput.value = String(updated.backendPort);
        backendModeSelect.value = updated.backendMode;
        backendFilePathInput.value = updated.backendFilePath ?? "";
        updateFileFieldVisibility();
        configStatusText.textContent = "Config applied. Start or restart sidecar.";
        const refreshedBootstrap = await getBootstrapConfig();
        console.log("refreshedBootstrap", refreshedBootstrap);
        applyBootstrapConfig(refreshedBootstrap);
      } catch (error) {
        configStatusText.textContent = `Failed to apply config: ${String(error)}`;
      } finally {
        isConfigActionInFlight = false;
        updateProcessButtons();
      }
    })();
  });

  async function refresh(): Promise<void> {
    const statusValue = document.getElementById("statusValue") as HTMLElement;
    const statusError = document.getElementById("statusError") as HTMLElement;
    const stateExcerpt = document.getElementById("stateExcerpt") as HTMLElement;

    try {
      const status = await fetchRuntimeStatus(currentBootstrap.backendBaseUrl);
      statusValue.textContent = status.status;
      statusError.textContent = status.last_error ?? "—";
    } catch (error) {
      statusValue.textContent = "unreachable";
      statusError.textContent = String(error);
    }

    try {
      const state = await fetchState(currentBootstrap.backendBaseUrl);
      stateExcerpt.textContent = formatExcerpt(state as Record<string, unknown> | null);
    } catch (error) {
      stateExcerpt.textContent = `Failed to load state: ${String(error)}`;
    }
  }

  void refresh();
  void loadAppConfig();
  void refreshProcessState();
  updateProcessButtons();
  window.setInterval(() => void refresh(), 1000);
  window.setInterval(() => void refreshProcessState(), 1000);
}
