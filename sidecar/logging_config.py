from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_DEFAULT_FORMAT = "%(levelname)-8s | %(asctime)s | %(name)s | %(message)s"


def configure_logging(*, logs_dir: str | Path | None = None) -> Path:
    base_dir = Path(__file__).resolve().parent
    target_dir = Path(logs_dir) if logs_dir is not None else base_dir / "logs"
    target_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = target_dir / "sidecar.log"
    root_logger = logging.getLogger()

    if getattr(configure_logging, "_configured", False):
        return log_file_path

    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_DEFAULT_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.captureWarnings(True)
    configure_logging._configured = True
    return log_file_path
