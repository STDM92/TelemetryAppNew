import logging

import irsdk
from .iracing_base_parser import IRacingBaseParser

logger = logging.getLogger(__name__)


class IRacingReader(IRacingBaseParser):
    def __init__(self, file_path: str|None):
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
                logger.info("Loaded %s frames from .ibt file.", self.total_ticks)
            except Exception as e:
                logger.exception("Failed to load replay file: %s", self.file_path)
                raise RuntimeError(f"Could not load .ibt file: {self.file_path}") from e

    def _get(self, name: str, default=None):
        try:
            value = self.ibt.get(self.current_tick, name)
            return default if value is None else value
        except KeyError:
            return default

    def _pre_capture(self):
        # Loop the file if we reach the end
        if self.current_tick >= self.total_ticks:
            logger.info("Replay finished. Looping back to start.")
            self.current_tick = 0

    def _post_capture(self):
        # Advance playhead to the next frame
        self.current_tick += 1