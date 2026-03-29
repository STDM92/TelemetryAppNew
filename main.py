import json
import time
from dataclasses import asdict
from pathlib import Path

from telemetry.administrator import TelemetryStateAdministrator
from telemetry.receivers.iracing_receiver import IRacingReceiver


OUTPUT_PATH = Path("telemetry_stream.jsonl")


def main():
    print("Starting Race Telemetry App...")

    administrator = TelemetryStateAdministrator()
    receiver = IRacingReceiver()

    print("\nWaiting for iRacing to launch...\n")

    with OUTPUT_PATH.open("a", encoding="utf-8") as f:
        i = 0
        while True:
            i += 1
            snapshot = receiver.capture_snapshot()

            if snapshot is not None:
                administrator.apply_snapshot(snapshot)
                latest = administrator.get_latest_snapshot()

                f.write(json.dumps(asdict(latest), ensure_ascii=False) + "\n")
                if i > 60:
                    f.flush()
                    i = 0


            time.sleep(1 / 60)


if __name__ == "__main__":
    main()