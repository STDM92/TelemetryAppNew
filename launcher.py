import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def wait_for_backend_ready(url: str, backend_process: subprocess.Popen, timeout_s: float = 15.0, poll_interval_s: float = 0.2) -> bool:
    """
    Wait until the backend responds to HTTP requests.

    Returns True if the backend is ready before timeout, otherwise False.
    Also returns False immediately if the backend process exits.
    """
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        # If the backend died during startup, stop waiting immediately.
        if backend_process.poll() is not None:
            return False

        try:
            request = Request(url, method="GET")
            with urlopen(request, timeout=1.0) as response:
                if 200 <= response.status < 500:
                    return True
        except (URLError, HTTPError, TimeoutError):
            pass

        time.sleep(poll_interval_s)

    return False


def main():
    print("Welcome to the Telemetry Stack")
    print("---------------------------------")
    print("1. Live Telemetry (Connects to active simulator)")
    print("2. Replay Mode (Streams .ibt file at 60Hz to HUD)")
    print("3. Analysis Mode (Processes .ibt file for Post-Race)")
    print("4. Exit")

    choice = input("\nEnter choice (1-4): ").strip()

    mode = "live"
    file_path = ""

    if choice == "1":
        mode = "live"
    elif choice == "2":
        mode = "replay"
    elif choice == "3":
        mode = "analyze"
    elif choice == "4":
        print("Exiting...")
        return
    else:
        print("Error: Invalid choice. Exiting.")
        return

    if mode in ["replay", "analyze"]:
        print("\nDrag and drop your .ibt file here, or paste the path:")
        file_path = input("> ").strip().strip('"').strip("'")

        if not Path(file_path).exists():
            print(f"Error: Could not find file at '{file_path}'")
            return

    port = 8000

    backend_cmd = [sys.executable, "backend/engine.py", "--mode", mode, "--port", str(port)]
    if mode in ["replay", "analyze"]:
        backend_cmd.extend(["--file", file_path])

    current_env = os.environ.copy()
    existing_pythonpath = current_env.get("PYTHONPATH", "")
    project_root = str(Path.cwd())

    if existing_pythonpath:
        current_env["PYTHONPATH"] = os.pathsep.join([project_root, existing_pythonpath])
    else:
        current_env["PYTHONPATH"] = project_root

    print(f"-> Starting Backend Engine in {mode.upper()} mode...")
    backend = subprocess.Popen(backend_cmd, env=current_env)

    if mode in ["live", "replay"]:
        frontend_url = f"http://localhost:{port}/"
    else:
        frontend_url = f"http://localhost:{port}/analyzer"

    readiness_url = f"http://localhost:{port}/health"
    print("-> Waiting for backend to become ready...")

    if not wait_for_backend_ready(readiness_url, backend, timeout_s=15.0, poll_interval_s=0.2):
        print("Error: Backend did not become ready in time or exited during startup.")

        if backend.poll() is None:
            backend.terminate()

        return

    print(f"-> Opening {frontend_url} in browser...")
    webbrowser.open(frontend_url)

    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\nShutting down Telemetry Stack...")
        backend.terminate()
        print("Done.")


if __name__ == "__main__":
    main()