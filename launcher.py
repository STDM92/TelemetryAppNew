import subprocess
import sys
import time

def main():
    print("Firing up the Telemetry Stack...")

    print("-> Starting Backend Engine on port 8000...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.engine:app", "--port", "8000"]
    )

    time.sleep(2) 

    print("-> Starting Frontend Dashboard...")
    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/dashboard.py"]
    )

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nShutting down the Telemetry Stack...")
        backend.terminate()
        frontend.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
