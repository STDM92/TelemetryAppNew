from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RuntimeMode(str, Enum):
    LIVE = "live"
    ANALYZE = "analyze"


class SimKind(str, Enum):
    IRACING = "iracing"
    ACC = "acc"
    LMU = "lmu"
    F1 = "f1"
    MOCK = "mock"
    UNKNOWN = "unknown"


class SourceKind(str, Enum):
    LIVE_FEED = "live_feed"
    FILE = "file"


@dataclass(frozen=True)
class StartupRequest:
    mode: RuntimeMode
    port: int
    file_path: Path | None = None
    requested_sim: SimKind | None = None