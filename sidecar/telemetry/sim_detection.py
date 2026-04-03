from dataclasses import dataclass
from enum import Enum


class SimKind(str, Enum):
    IRACING = "iracing"
    ACC = "acc"
    LMU = "lmu"
    F1 = "f1"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DetectedSim:
    kind: SimKind
    display_name: str


def detect_active_sim(config) -> DetectedSim:
    """
    Placeholder implementation for now.

    Later this becomes the real sim detection/probing entrypoint.
    For now we keep the full pipeline in place while returning a
    hardcoded sim identity.
    """
    if config.mode in {"replay", "analyze"}:
        return DetectedSim(kind=SimKind.IRACING, display_name="iRacing Replay")

    return DetectedSim(kind=SimKind.IRACING, display_name="iRacing")