import os
from pathlib import Path

# The file contents we discussed
ENGINE_CODE = '''\
import asyncio
import json
import time
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from telemetry.administrator import TelemetryStateAdministrator
from telemetry.receivers.iracing_receiver import IRacingReceiver

app = FastAPI()
administrator = TelemetryStateAdministrator()
receiver = IRacingReceiver()

OUTPUT_PATH = Path(__file__).parent / "brake_events.json"
current_snapshot_dict = None

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telemetry_loop())

async def telemetry_loop():
    global current_snapshot_dict
    last_brake = 0.0
    brake_events = []

    print("Backend Engine Started. Waiting for Simulator...")

    while True:
        snapshot = receiver.capture_snapshot()

        if snapshot is not None:
            administrator.apply_snapshot(snapshot)
            latest = administrator.get_latest_snapshot()
            current_snapshot_dict = asdict(latest)

            current_brake = latest.inputs.brake_ratio or 0.0
            if last_brake < 0.02 and current_brake >= 0.02:
                event = {
                    "event_type": "brake_press",
                    "event_time": time.time(),
                    "brake_threshold": 0.02,
                    "snapshot": current_snapshot_dict,
                }
                brake_events.append(event)
                with OUTPUT_PATH.open("w", encoding="utf-8") as f:
                    json.dump(brake_events, f, ensure_ascii=False, indent=2)
                print("Brake event captured & saved!")

            last_brake = current_brake

        await asyncio.sleep(1 / 60)

@app.get("/live")
def get_live_telemetry():
    return current_snapshot_dict
'''

DASHBOARD_CODE = '''\
import time
import requests
import streamlit as st

st.set_page_config(page_title="Race Telemetry", layout="wide")

st.title("🏎️ Live Telemetry Dashboard")

try:
    response = requests.get("http://localhost:8000/live")
    snapshot = response.json()

    if snapshot is None:
        st.warning("Backend is running, but no simulator is connected.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Current Lap Time", f"{snapshot['lap']['current_lap_time_s']} s")
            st.metric("Speed", f"{snapshot['powertrain']['vehicle_speed_kph']:.1f} kph")

        with col2:
            st.write("Throttle")
            st.progress(snapshot['inputs']['throttle_ratio'] or 0.0)
            st.write("Brake")
            st.progress(snapshot['inputs']['brake_ratio'] or 0.0)

except requests.exceptions.ConnectionError:
    st.error("Cannot connect to backend engine. Is it running?")

time.sleep(0.05)
st.rerun()
'''

LAUNCHER_CODE = '''\
import subprocess
import sys
import time

def main():
    print("🚀 Firing up the Telemetry Stack...")

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
        print("\\n🛑 Shutting down the Telemetry Stack...")
        backend.terminate()
        frontend.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
'''


def main():
    base_dir = Path.cwd()

    # Create Directories
    (base_dir / "backend").mkdir(exist_ok=True)
    (base_dir / "frontend").mkdir(exist_ok=True)

    # Write Files
    with open(base_dir / "backend" / "engine.py", "w", encoding="utf-8") as f:
        f.write(ENGINE_CODE)

    with open(base_dir / "frontend" / "dashboard.py", "w", encoding="utf-8") as f:
        f.write(DASHBOARD_CODE)

    with open(base_dir / "launcher.py", "w", encoding="utf-8") as f:
        f.write(LAUNCHER_CODE)

    print("✅ Architecture setup complete!")
    print("Run 'python launcher.py' to start the stack.")


if __name__ == "__main__":
    main()