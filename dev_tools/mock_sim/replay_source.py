from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Iterator

from sidecar.telemetry.sims.iracing.iracing_reader import IRacingReader


class ReplayFrameSource:
    def __init__(self, file_path: str):
        self._file_path = file_path

    def iter_payloads(self) -> Iterator[dict]:
        reader = IRacingReader(self._file_path)

        while True:
            snapshot = reader.capture_snapshot()
            if snapshot is None:
                break

            if is_dataclass(snapshot):
                yield asdict(snapshot)
            elif isinstance(snapshot, dict):
                yield snapshot
            else:
                raise TypeError(
                    f"Unsupported snapshot type from IRacingReader: {type(snapshot).__name__}"
                )