import time

from telemetry.administrator import TelemetryStateAdministrator
from telemetry.receivers.iracing_receiver import IRacingReceiver


def main():
    print("Starting Race Telemetry App...")

    administrator = TelemetryStateAdministrator()
    receiver = IRacingReceiver()

    print("\nWaiting for iRacing to launch...\n")

    while True:
        snapshot = receiver.capture_snapshot()

        if snapshot is not None:
            administrator.apply_snapshot(snapshot)

            latest = administrator.get_latest_snapshot()
            print(
                f"\rSource: {latest.source} | "
                f"Lap: {latest.current_lap} | "
                f"Speed: {latest.speed_kph:.1f} km/h | "
                f"Gear: {latest.gear} | "
                f"Fuel: {latest.fuel_remaining_liters:.1f} L | "
                f"Position: P{latest.position}   ",
                end="",
                flush=True,
            )

        time.sleep(1 / 60)


if __name__ == "__main__":
    main()
