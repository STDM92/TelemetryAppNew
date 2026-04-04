import logging

import irsdk
from .iracing_base_parser import IRacingBaseParser

logger = logging.getLogger(__name__)


class IRacingReceiver(IRacingBaseParser):
    def __init__(self):
        """
        Initializes the IRacingReceiver and the IRSDK instance.
        """
        super().__init__()
        self.ir = irsdk.IRSDK()
        self._waiting_for_connection_logged = False

    def check_connection(self) -> None:
        """
        Checks the connection to iRacing and attempts to start up the SDK if not connected.
        """
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
        """
        Retrieves a live telemetry value from iRacing.

        :param name: The name of the telemetry variable.
        :type name: str

        :param default: The default value if the variable is not found.
        :type default: Any

        :return: The telemetry value or the default.
        :rtype: Any
        """
        try:
            value = self.ir[name]
            return default if value is None else value
        except KeyError:
            return default

    def _pre_capture(self):
        """
        Freezes the iRacing variable buffer to ensure consistent data during capture.
        """
        self.ir.freeze_var_buffer_latest()

    def _post_capture(self):
        """
        Unfreezes the iRacing variable buffer after capture.
        """
        self.ir.unfreeze_var_buffer_latest()
