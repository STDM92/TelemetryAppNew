from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RuntimeMode(str, Enum):
    LIVE = "live"
    ANALYZE = "analyze"
    REPLAY = "replay"


class SimKind(str, Enum):
    IRACING = "iracing"
    ACC = "acc"
    LMU = "lmu"
    F1 = "f1"
    UNKNOWN = "unknown"


class SourceKind(str, Enum):
    LIVE_FEED = "live_feed"
    FILE = "file"
    REPLAY_FILE = "replay_file"


@dataclass(frozen=True)
class StartupRequest:
    mode: RuntimeMode
    port: int
    file_path: Path | None = None
    requested_sim: SimKind | None = None
