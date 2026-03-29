import time

import irsdk

from telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot


class IRacingReceiver:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.connected = False

    def check_connection(self):
        if self.connected and not (self.ir.is_initialized and self.ir.is_connected):
            self.connected = False
            self.ir.shutdown()
            print("iRacing disconnected.")

        elif not self.connected and self.ir.startup() and self.ir.is_initialized and self.ir.is_connected:
            self.connected = True
            print("iRacing connected. Listening for telemetry...")

    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        self.check_connection()

        if not self.connected:
            return None

        self.ir.freeze_var_buffer_latest()

        try:
            speed_raw = self.ir["Speed"]
            speed_kph = speed_raw * 3.6 if speed_raw is not None else None

            lf_temp = self.ir["LFtempM"]
            rf_temp = self.ir["RFtempM"]
            lr_temp = self.ir["LRtempM"]
            rr_temp = self.ir["RRtempM"]

            surface_temps = None
            if all(t is not None for t in [lf_temp, rf_temp, lr_temp, rr_temp]):
                surface_temps = [lf_temp, rf_temp, lr_temp, rr_temp]

            return UnifiedTelemetrySnapshot(
                source="iracing",
                timestamp=time.time(),
                current_lap=self.ir["Lap"],
                speed_kph=speed_kph,
                gear=self.ir["Gear"],
                fuel_remaining_liters=self.ir["FuelLevel"],
                position=self.ir["PlayerCarPosition"],
                tire_surface_temp_c=surface_temps,
            )

        except KeyError:
            return None

        finally:
            self.ir.unfreeze_var_buffer_latest()