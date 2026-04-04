import logging

import irsdk
from .iracing_base_parser import IRacingBaseParser

logger = logging.getLogger(__name__)


class IRacingReceiver(IRacingBaseParser):
    def __init__(self):
        super().__init__()
        self.ir = irsdk.IRSDK()
        self._waiting_for_connection_logged = False

    def check_connection(self) -> None:
        if self.connected and not (self.ir.is_initialized and self.ir.is_connected):
            self.connected = False
            self.ir.shutdown()
            self._waiting_for_connection_logged = False
            logger.info("iRacing disconnected.")
        elif not self.connected and self.ir.startup() and self.ir.is_initialized and self.ir.is_connected:
            self.connected = True
            self._waiting_for_connection_logged = False
            logger.info("iRacing connected. Listening for telemetry...")
        elif not self.connected and not self._waiting_for_connection_logged:
            self._waiting_for_connection_logged = True
            logger.info("Waiting for iRacing connection.")

    def _get(self, name: str, default=None):
        try:
            value = self.ir[name]
            return default if value is None else value
        except KeyError:
            return default

    def _pre_capture(self):
        self.ir.freeze_var_buffer_latest()

    def _post_capture(self):
        self.ir.unfreeze_var_buffer_latest()
