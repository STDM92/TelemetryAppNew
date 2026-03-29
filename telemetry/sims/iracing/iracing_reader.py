import irsdk
from .iracing_base_parser import IRacingBaseParser

class IRacingReader(IRacingBaseParser):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.ibt = irsdk.IBT()
        self.current_tick = 0
        self.total_ticks = 0

    def check_connection(self) -> None:
        if not self.connected:
            try:
                self.ibt.open(self.file_path)
                self.total_ticks = self.ibt._disk_header.session_record_count
                self.connected = True
                print(f"Loaded {self.total_ticks} frames from .ibt file.")
            except Exception as e:
                print(f"Could not load .ibt file. Error: {e}")

    def _get(self, name: str, default=None):
        try:
            value = self.ibt.get(self.current_tick, name)
            return default if value is None else value
        except KeyError:
            return default

    def _pre_capture(self):
        # Loop the file if we reach the end
        if self.current_tick >= self.total_ticks:
            print("Replay finished. Looping back to start!")
            self.current_tick = 0

    def _post_capture(self):
        # Advance playhead to the next frame
        self.current_tick += 1