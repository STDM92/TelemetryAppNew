from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MockSimConfig:
    file_path: str
    port: int = 8766
    hz: float = 60.0
    loop: bool = False


@dataclass(frozen=True)
class StreamFrame:
    sequence: int
    payload: dict