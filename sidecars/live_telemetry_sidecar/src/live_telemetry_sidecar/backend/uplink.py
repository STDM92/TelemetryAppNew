from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any
from urllib.parse import quote

import httpx
import websockets

logger = logging.getLogger(__name__)


class SessionUplink:
    def __init__(
        self,
        *,
        enabled: bool,
        server_base_url: str | None,
        configured_session_key: str | None = None,
        reconnect_initial_delay_s: float = 1.0,
        reconnect_max_delay_s: float = 10.0,
    ):
        self._enabled = enabled
        self._server_base_url = self._normalize_server_base_url(server_base_url)
        self._configured_session_key = self._normalize_session_key(configured_session_key)
        self._reconnect_initial_delay_s = reconnect_initial_delay_s
        self._reconnect_max_delay_s = reconnect_max_delay_s

        self._active_session_key: str | None = None
        self._engineer_url: str | None = None
        self._remote_state = "disabled" if not enabled else "created"
        self._last_error: str | None = None
        self._last_connected_at: float | None = None
        self._last_sent_at: float | None = None
        self._frames_sent = 0

        self._snapshot_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=1)
        self._run_task: asyncio.Task | None = None
        self._closed = False

    async def start(self) -> None:
        if not self._enabled:
            logger.info("Session uplink disabled by configuration.")
            self._remote_state = "disabled"
            return

        if self._run_task is not None and not self._run_task.done():
            logger.debug("Session uplink start requested while already running.")
            return

        self._closed = False
        self._remote_state = "starting"
        self._last_error = None
        self._run_task = asyncio.create_task(self._run(), name="session-uplink")
        logger.info(
            "Session uplink starting. server_base_url=%s configured_session_key=%s",
            self._server_base_url,
            self._configured_session_key,
        )

    async def stop(self) -> None:
        self._closed = True
        task = self._run_task
        self._run_task = None

        if task is None:
            if self._enabled:
                self._remote_state = "stopped"
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.debug("Session uplink task cancelled during stop.")
        finally:
            if self._enabled:
                self._remote_state = "stopped"
            logger.info("Session uplink stopped.")

    async def publish_snapshot(self, snapshot: dict) -> None:
        if not self._enabled:
            return

        self._replace_latest_snapshot(snapshot)

    def get_status(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "server_base_url": self._server_base_url,
            "configured_session_key": self._configured_session_key,
            "active_session_key": self._active_session_key,
            "engineer_url": self._engineer_url,
            "remote_state": self._remote_state,
            "last_error": self._last_error,
            "last_connected_at": self._last_connected_at,
            "last_sent_at": self._last_sent_at,
            "frames_sent": self._frames_sent,
        }

    async def _run(self) -> None:
        backoff_s = self._reconnect_initial_delay_s

        while not self._closed:
            try:
                session_key = await self._ensure_session_key()
                server_ws_url = self._build_server_ws_url(session_key)
                self._remote_state = "connecting"
                logger.info(
                    "Connecting session uplink websocket. session_key=%s server_ws_url=%s",
                    session_key,
                    server_ws_url,
                )

                async with websockets.connect(server_ws_url) as server_ws:
                    self._remote_state = "connected"
                    self._last_connected_at = time.time()
                    self._last_error = None
                    backoff_s = self._reconnect_initial_delay_s

                    await self._log_server_hello(server_ws)
                    await self._stream_snapshots(server_ws)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._last_error = str(exc)
                self._remote_state = "retry_wait"
                logger.warning(
                    "Session uplink connection cycle failed. retry_in_s=%.1f error=%s",
                    backoff_s,
                    exc,
                    exc_info=True,
                )
                await asyncio.sleep(backoff_s)
                backoff_s = min(backoff_s * 2, self._reconnect_max_delay_s)

    async def _ensure_session_key(self) -> str:
        if self._configured_session_key:
            session_key = self._normalize_session_key(self._configured_session_key)
            self._active_session_key = session_key
            self._engineer_url = self._build_engineer_url(session_key)
            return session_key

        if self._active_session_key:
            return self._active_session_key

        self._remote_state = "creating_session"
        assert self._server_base_url is not None

        async with httpx.AsyncClient(base_url=self._server_base_url, timeout=10.0) as client:
            response = await client.post("/api/session/create")
            response.raise_for_status()
            data = response.json()

        session_key = self._normalize_session_key(str(data["session_key"]))
        self._active_session_key = session_key
        self._engineer_url = self._build_engineer_url(session_key)

        logger.info(
            "Created remote telemetry session. session_key=%s engineer_url=%s",
            session_key,
            self._engineer_url,
        )
        return session_key


    async def _log_server_hello(self, server_ws: Any) -> None:
        try:
            hello = await asyncio.wait_for(server_ws.recv(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.info("Session uplink websocket connected without initial hello message.")
            return

        logger.info("Session uplink server hello: %s", hello)

    async def _stream_snapshots(self, server_ws: Any) -> None:
        while True:
            snapshot = await self._snapshot_queue.get()
            envelope = {
                "type": "telemetry_snapshot",
                "payload": snapshot,
            }
            await server_ws.send(json.dumps(envelope))
            self._frames_sent += 1
            self._last_sent_at = time.time()

            if self._frames_sent == 1 or self._frames_sent % 30 == 0:
                logger.info(
                    "Session uplink sent telemetry snapshot. session_key=%s frames_sent=%s",
                    self._active_session_key,
                    self._frames_sent,
                )

    def _replace_latest_snapshot(self, snapshot: dict) -> None:
        while True:
            try:
                self._snapshot_queue.put_nowait(snapshot)
                return
            except asyncio.QueueFull:
                try:
                    self._snapshot_queue.get_nowait()
                except asyncio.QueueEmpty:
                    return

    def _build_server_ws_url(self, session_key: str) -> str:
        assert self._server_base_url is not None
        ws_base = (
            self._server_base_url
            .replace("http://", "ws://", 1)
            .replace("https://", "wss://", 1)
        )
        return f"{ws_base}/ws?session_key={quote(session_key)}&role=producer"

    def _build_engineer_url(self, session_key: str) -> str | None:
        if self._server_base_url is None:
            return None

        server = quote(self._server_base_url, safe="")
        key = quote(session_key)
        return f"{self._server_base_url}/frontend/session_viewer.html?server={server}&session_key={key}"

    @staticmethod
    def _normalize_server_base_url(server_base_url: str | None) -> str | None:
        if server_base_url is None:
            return None

        normalized = server_base_url.strip().rstrip("/")
        return normalized or None

    @staticmethod
    def _normalize_session_key(session_key: str | None) -> str | None:
        if session_key is None:
            return None

        normalized = session_key.strip().upper()
        return normalized or None
