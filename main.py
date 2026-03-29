import json
import time
from dataclasses import asdict
from pathlib import Path

from telemetry.administrator import TelemetryStateAdministrator
from telemetry.receivers.iracing_receiver import IRacingReceiver


OUTPUT_PATH = Path("brake_events.json")


def main():
    print("Starting Race Telemetry App...")

    administrator = TelemetryStateAdministrator()
    receiver = IRacingReceiver()

    print("\nWaiting for iRacing to launch...\n")

    brake_events = []
    last_brake = 0.0

    while True:
        snapshot = receiver.capture_snapshot()

        if snapshot is not None:
            administrator.apply_snapshot(snapshot)
            latest = administrator.get_latest_snapshot()

            current_brake = latest.inputs.brake_ratio or 0.0

            brake_just_pressed = last_brake < 0.02 and current_brake >= 0.02

            if brake_just_pressed:
                event = {
                    "event_type": "brake_press",
                    "event_time": time.time(),
                    "brake_threshold": 0.02,
                    "snapshot": asdict(latest),
                }

                brake_events.append(event)

                with OUTPUT_PATH.open("w", encoding="utf-8") as f:
                    json.dump(brake_events, f, ensure_ascii=False, indent=2)

                print("Brake event captured.")

            last_brake = current_brake

        time.sleep(1 / 60)


if __name__ == "__main__":
    main()