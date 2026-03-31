class SessionRegistry:
    # In-memory placeholder session registry for the first LAN prototype.

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}
