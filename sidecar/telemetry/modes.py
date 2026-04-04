from dataclasses import dataclass
from enum import Enum


class SimKind(str, Enum):
    IRACING = "iracing"
    ACC = "acc"
    LMU = "lmu"
    F1 = "f1"
    MOCK = "mock"
    UNKNOWN = "unknown"


class SourceKind(str, Enum):
    LIVE_FEED = "live_feed"


@dataclass(frozen=True)
class StartupRequest:
    port: int
    requested_sim: SimKind | None = None