import argparse
import html
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


DEFAULT_BACKEND_PORT = 8000
DEFAULT_HOST_PORT = 8765


class HostState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.backend_pid: int | None = None
        self.backend_exit_code: int | None = None
        self.backend_started_at: float | None = None
        self.backend_ready = False
        self.backend_health: dict | None = None
        self.backend_health_error: str | None = None
        self.backend_state_excerpt: dict | None = None
        self.log_tail: deque[str] = deque(maxlen=60)

    def append_log(self, line: str) -> None:
        with self._lock:
            self.log_tail.append(line.rstrip())

    def snapshot(self) -> dict:
        with self._lock:
            uptime_s = None
            if self.backend_started_at is not None and self.backend_exit_code is None:
                uptime_s = round(time.monotonic() - self.backend_started_at, 1)

            return {
                "backend_pid": self.backend_pid,
                "backend_exit_code": self.backend_exit_code,
                "backend_ready": self.backend_ready,
                "backend_health": self.backend_health,
                "backend_health_error": self.backend_health_error,
                "backend_state_excerpt": self.backend_state_excerpt,
                "backend_uptime_s": uptime_s,
                "log_tail": list(self.log_tail),
            }

    def set_backend_started(self, pid: int) -> None:
        with self._lock:
            self.backend_pid = pid
            self.backend_exit_code = None
            self.backend_started_at = time.monotonic()
            self.backend_ready = False
            self.backend_health = None
            self.backend_health_error = None
            self.backend_state_excerpt = None
            self.log_tail.clear()

    def set_backend_exit(self, exit_code: int) -> None:
        with self._lock:
            self.backend_exit_code = exit_code
            self.backend_ready = False

    def set_health(self, ready: bool, health: dict | None, error: str | None, state_excerpt: dict | None) -> None:
        with self._lock:
            self.backend_ready = ready
            self.backend_health = health
            self.backend_health_error = error
            self.backend_state_excerpt = state_excerpt


class BackendProcessOwner:
    def __init__(self, project_root: Path, ui_file: Path, mode: str, file_path: str | None, backend_port: int):
        self.project_root = project_root
        self.ui_file = ui_file
        self.mode = mode
        self.file_path = file_path
        self.backend_port = backend_port
        self.backend_origin = f"http://127.0.0.1:{backend_port}"
        self.health_url = f"{self.backend_origin}/health"
        self.state_url = f"{self.backend_origin}/api/state"
        self.process: subprocess.Popen[str] | None = None
        self.state = HostState()
        self._stop_event = threading.Event()
        self._log_thread: threading.Thread | None = None
        self._monitor_thread: threading.Thread | None = None

    def start(self) -> None:
        backend_path = self.project_root / "backend" / "engine.py"

        print("[mock-host] starting backend")
        print(f"[mock-host] project_root={self.project_root}")
        print(f"[mock-host] backend_path={backend_path}")
        print(f"[mock-host] cwd={self.project_root}")
        print(f"[mock-host] backend_path_exists={backend_path.is_file()}")

        backend_cmd = [
            sys.executable,
            str(backend_path),
            "--mode",
            self.mode,
            "--port",
            str(self.backend_port),
        ]
        if self.file_path:
            backend_cmd.extend(["--file", self.file_path])

        print(f"[mock-host] cmd={' '.join(backend_cmd)}")

        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "")
        project_root_str = str(self.project_root)
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONPATH"] = (
            os.pathsep.join([project_root_str, existing_pythonpath]) if existing_pythonpath else project_root_str
        )

        try:
            self.process = subprocess.Popen(
                backend_cmd,
                cwd=str(self.project_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            self.state.append_log(f"FAILED TO START BACKEND PROCESS: {exc}")
            raise

        time.sleep(0.2)
        exit_code = self.process.poll()
        if exit_code is not None:
            self.state.set_backend_started(self.process.pid)
            self.state.set_backend_exit(exit_code)
            self.state.append_log(f"Backend exited immediately with code {exit_code}")
            return

        self.state.set_backend_started(self.process.pid)

        self._log_thread = threading.Thread(target=self._pump_logs, name="backend-log-pump", daemon=True)
        self._log_thread.start()

        self._monitor_thread = threading.Thread(target=self._monitor_backend, name="backend-monitor", daemon=True)
        self._monitor_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self.process is None:
            return

        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)

        self.state.set_backend_exit(self.process.returncode)

    def _pump_logs(self) -> None:
        if self.process is None or self.process.stdout is None:
            return

        for line in self.process.stdout:
            self.state.append_log(line)

    def _monitor_backend(self) -> None:
        while not self._stop_event.is_set():
            process = self.process
            if process is None:
                return

            exit_code = process.poll()
            if exit_code is not None:
                self.state.set_backend_exit(exit_code)
                return

            health, health_error = self._fetch_json(self.health_url)
            state_data, _ = self._fetch_json(self.state_url)
            state_excerpt = self._build_state_excerpt(state_data)

            ready = bool(health) and health.get("status") == "running"
            self.state.set_health(ready=ready, health=health, error=health_error, state_excerpt=state_excerpt)
            time.sleep(0.5)

    @staticmethod
    def _build_state_excerpt(state_data: dict | None) -> dict | None:
        if not isinstance(state_data, dict):
            return None

        return {
            "source": state_data.get("source"),
            "session_phase": (state_data.get("session") or {}).get("session_phase"),
            "current_lap": (state_data.get("lap") or {}).get("current_lap"),
            "speed_kph": (state_data.get("powertrain") or {}).get("vehicle_speed_kph"),
            "gear": (state_data.get("powertrain") or {}).get("gear"),
        }

    @staticmethod
    def _fetch_json(url: str) -> tuple[dict | None, str | None]:
        try:
            request = Request(url, method="GET")
            with urlopen(request, timeout=1.0) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload), None
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            return None, str(exc)

    def render_index_html(self) -> str:
        original = self.ui_file.read_text(encoding="utf-8")
        backend_origin_json = json.dumps(self.backend_origin)

        overlay = f"""
<script>
window.__MOCK_BACKEND_ORIGIN__ = {backend_origin_json};

(function() {{
  const mockBackendWsUrl = (window.__MOCK_BACKEND_ORIGIN__ || `${{window.location.protocol}}//${{window.location.host}}`).replace(/^http/, 'ws') + '/ws';

  window.buildWebSocketUrl = function() {{
    return mockBackendWsUrl;
  }};

  const OriginalWebSocket = window.WebSocket;
  window.WebSocket = function(url, protocols) {{
    let rewrittenUrl = url;
    if (typeof url === 'string' && /\\/ws(?:\\?|$)/.test(url)) {{
      rewrittenUrl = mockBackendWsUrl;
      console.log('Mock host rewrote WebSocket URL:', url, '->', rewrittenUrl);
    }}

    return protocols === undefined
      ? new OriginalWebSocket(rewrittenUrl)
      : new OriginalWebSocket(rewrittenUrl, protocols);
  }};
  window.WebSocket.prototype = OriginalWebSocket.prototype;
  Object.setPrototypeOf(window.WebSocket, OriginalWebSocket);

  console.log('Mock host override active:', mockBackendWsUrl);
  const style = document.createElement('style');
  style.textContent = `
    .mock-host-panel {{
      position: fixed;
      right: 16px;
      bottom: 16px;
      width: min(420px, calc(100vw - 32px));
      max-height: 45vh;
      overflow: auto;
      z-index: 9999;
      background: rgba(10, 10, 12, 0.96);
      color: #fff;
      border: 1px solid #2a2b30;
      border-radius: 12px;
      padding: 12px;
      box-shadow: 0 12px 30px rgba(0,0,0,0.35);
      font: 12px/1.45 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    .mock-host-panel h3 {{ margin: 0 0 8px 0; font-size: 13px; }}
    .mock-host-grid {{ display: grid; grid-template-columns: auto 1fr; gap: 4px 10px; }}
    .mock-host-key {{ color: #9ca3af; }}
    .mock-host-value {{ word-break: break-word; }}
    .mock-host-value.ok {{ color: #22c55e; }}
    .mock-host-value.bad {{ color: #ef4444; }}
    .mock-host-log {{ margin-top: 10px; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, monospace; color: #d1d5db; }}
  `;
  document.head.appendChild(style);

  const panel = document.createElement('section');
  panel.className = 'mock-host-panel';
  panel.innerHTML = `
    <h3>Mock Host</h3>
    <div class="mock-host-grid">
      <div class="mock-host-key">Backend</div><div class="mock-host-value" id="mockHostBackend">starting…</div>
      <div class="mock-host-key">Ready</div><div class="mock-host-value" id="mockHostReady">—</div>
      <div class="mock-host-key">PID</div><div class="mock-host-value" id="mockHostPid">—</div>
      <div class="mock-host-key">Exit</div><div class="mock-host-value" id="mockHostExit">—</div>
      <div class="mock-host-key">Health</div><div class="mock-host-value" id="mockHostHealth">—</div>
      <div class="mock-host-key">Error</div><div class="mock-host-value" id="mockHostError">—</div>
      <div class="mock-host-key">State</div><div class="mock-host-value" id="mockHostState">—</div>
    </div>
    <div class="mock-host-log" id="mockHostLog">Waiting for backend output…</div>
  `;
  document.body.appendChild(panel);

  function setText(id, text, klass) {{
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    el.classList.remove('ok', 'bad');
    if (klass) el.classList.add(klass);
  }}

  async function pollHostStatus() {{
    try {{
      const response = await fetch('/host/status', {{ cache: 'no-store' }});
      const status = await response.json();
      setText('mockHostBackend', window.__MOCK_BACKEND_ORIGIN__);
      setText('mockHostReady', String(status.backend_ready), status.backend_ready ? 'ok' : 'bad');
      setText('mockHostPid', status.backend_pid == null ? '—' : String(status.backend_pid));
      setText('mockHostExit', status.backend_exit_code == null ? 'running' : String(status.backend_exit_code), status.backend_exit_code == null ? 'ok' : 'bad');
      setText('mockHostHealth', status.backend_health ? JSON.stringify(status.backend_health) : '—');
      setText('mockHostError', status.backend_health_error || (status.backend_health && status.backend_health.last_error) || '—', (status.backend_health_error || (status.backend_health && status.backend_health.last_error)) ? 'bad' : 'ok');
      setText('mockHostState', status.backend_state_excerpt ? JSON.stringify(status.backend_state_excerpt) : '—');
      setText('mockHostLog', (status.log_tail || []).slice(-12).join('\\n') || 'No backend output yet.');
    }} catch (error) {{
      setText('mockHostError', String(error), 'bad');
    }}
  }}

  window.addEventListener('DOMContentLoaded', function() {{
    pollHostStatus();
    window.setInterval(pollHostStatus, 1000);
  }});
}})();
</script>
"""

        if "</body>" in original:
            return original.replace("</body>", f"{overlay}\n</body>")

        return original + "\n" + overlay


class MockHostHandler(BaseHTTPRequestHandler):
    owner: BackendProcessOwner | None = None

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            assert self.owner is not None
            body = self.owner.render_index_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/host/status":
            assert self.owner is not None
            body = json.dumps(self.owner.state.snapshot()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        body = html.escape(f"Unknown path: {self.path}").encode("utf-8")
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal mock host for telemetry sidecar validation")
    parser.add_argument("--mode", choices=["live", "replay", "analyze"], default="live")
    parser.add_argument("--file", help="Telemetry file path for replay/analyze modes")
    parser.add_argument("--backend-port", type=int, default=DEFAULT_BACKEND_PORT)
    parser.add_argument("--host-port", type=int, default=DEFAULT_HOST_PORT)
    parser.add_argument("--ui-file", default="dev_tools/mock_host/index.html", help="Path to the temporary HTML UI surface")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically")
    args = parser.parse_args(argv)

    if args.mode in {"replay", "analyze"} and not args.file:
        parser.error("--file is required when --mode is replay or analyze.")

    if args.file and not Path(args.file).is_file():
        parser.error(f"--file does not point to a readable file: {args.file}")

    if not Path(args.ui_file).is_file():
        parser.error(f"--ui-file does not point to a readable file: {args.ui_file}")

    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(__file__).resolve().parent.parent.parent
    owner = BackendProcessOwner(
        project_root=project_root,
        ui_file=Path(args.ui_file).resolve(),
        mode=args.mode,
        file_path=args.file,
        backend_port=args.backend_port,
    )

    owner.start()
    MockHostHandler.owner = owner
    server = ThreadingHTTPServer(("127.0.0.1", args.host_port), MockHostHandler)
    host_url = f"http://127.0.0.1:{args.host_port}/"

    print(f"Mock host listening at {host_url}")
    print(f"Backend target: {owner.backend_origin}")

    if not args.no_browser:
        webbrowser.open(host_url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mock host...")
    finally:
        server.shutdown()
        server.server_close()
        owner.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
