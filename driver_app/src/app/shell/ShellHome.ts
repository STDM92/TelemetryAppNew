import type { BootstrapConfig, SidecarProcessState } from "../../types/api";
import {
  getSidecarProcessState,
  restartSidecar,
  startSidecar,
  stopSidecar,
} from "../api/processClient";
import { fetchRuntimeStatus } from "../api/runtimeClient";
import { fetchState } from "../api/stateClient";

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
    2,
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
  ];

  return lines.join("\n");
}

export function mountShell(root: HTMLElement, config: BootstrapConfig): void {
  let isProcessActionInFlight = false;
  let latestProcessState: SidecarProcessState | null = null;

  root.innerHTML = `
    <div class="app-shell">
      <h1>Driver App</h1>
      <p class="muted">Thin local shell for the telemetry sidecar.</p>

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

  (document.getElementById("mode") as HTMLElement).textContent = config.mode;
  (document.getElementById("backend") as HTMLElement).textContent = config.backendBaseUrl;
  (document.getElementById("ws") as HTMLElement).textContent = config.backendWebsocketUrl;

  const processState = document.getElementById("processState") as HTMLElement;
  const startButton = document.getElementById("startSidecarButton") as HTMLButtonElement;
  const stopButton = document.getElementById("stopSidecarButton") as HTMLButtonElement;
  const restartButton = document.getElementById("restartSidecarButton") as HTMLButtonElement;
  const processStatusValue = document.getElementById("processStatusValue") as HTMLElement;
  const processPidValue = document.getElementById("processPidValue") as HTMLElement;
  const processExitCodeValue = document.getElementById("processExitCodeValue") as HTMLElement;
  const processLastErrorValue = document.getElementById("processLastErrorValue") as HTMLElement;

  function updateProcessButtons(): void {
    const status = latestProcessState?.status ?? "not_running";
    const disableAll = isProcessActionInFlight;

    startButton.disabled = disableAll || status === "running";
    stopButton.disabled = disableAll || status !== "running";
    restartButton.disabled = disableAll || status !== "running";
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
  });

  stopButton.addEventListener("click", () => {
    void runProcessAction(stopSidecar, "Failed to stop sidecar");
  });

  restartButton.addEventListener("click", () => {
    void (async () => {
      try {
        const state = await restartSidecar();
        processState.textContent = renderProcessState(state);
      } catch (error) {
        processState.textContent = `Failed to restart sidecar: ${String(error)}`;
      }
    })();
  });

  async function refresh(): Promise<void> {
    const statusValue = document.getElementById("statusValue") as HTMLElement;
    const statusError = document.getElementById("statusError") as HTMLElement;
    const stateExcerpt = document.getElementById("stateExcerpt") as HTMLElement;

    try {
      const status = await fetchRuntimeStatus(config.backendBaseUrl);
      statusValue.textContent = status.status;
      statusError.textContent = status.last_error ?? "—";
    } catch (error) {
      statusValue.textContent = "unreachable";
      statusError.textContent = String(error);
    }

    try {
      const state = await fetchState(config.backendBaseUrl);
      stateExcerpt.textContent = formatExcerpt(state as Record<string, unknown> | null);
    } catch (error) {
      stateExcerpt.textContent = `Failed to load state: ${String(error)}`;
    }
  }

  void refresh();
  void refreshProcessState();
  updateProcessButtons();
  window.setInterval(() => void refresh(), 1000);
  window.setInterval(() => void refreshProcessState(), 1000);
}
