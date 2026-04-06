#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

import httpx
import websockets

DEFAULT_LOCAL_SIDECAR_WS = "ws://127.0.0.1:8000/ws"
DEFAULT_SERVER_BASE_URL = "http://127.0.0.1:8080"


async def create_session_if_needed(server_base_url: str, session_key: str | None) -> str:
    if session_key:
        return session_key.upper()

    async with httpx.AsyncClient(base_url=server_base_url, timeout=10.0) as client:
        response = await client.post("/api/session/create")
        response.raise_for_status()
        data = response.json()
        return str(data["session_key"]).upper()


async def relay(local_sidecar_ws: str, server_ws_url: str) -> None:
    print(f"[bridge] connecting to local sidecar websocket: {local_sidecar_ws}")
    async with websockets.connect(local_sidecar_ws) as local_ws:
        print(f"[bridge] connecting to web server producer websocket: {server_ws_url}")
        async with websockets.connect(server_ws_url) as server_ws:
            hello = await server_ws.recv()
            print(f"[bridge] server hello: {hello}")

            frame_count = 0
            while True:
                raw_message = await local_ws.recv()
                parsed: Any = json.loads(raw_message)

                if parsed is None or not isinstance(parsed, dict):
                    continue

                envelope = {
                    "type": "telemetry_snapshot",
                    "payload": parsed,
                }
                await server_ws.send(json.dumps(envelope))
                frame_count += 1

                if frame_count % 30 == 0:
                    print(f"[bridge] relayed {frame_count} frames")


async def main_async() -> int:
    parser = argparse.ArgumentParser(
        description="Bridge the local telemetry sidecar websocket into a telemetry web server session."
    )
    parser.add_argument(
        "--local-sidecar-ws",
        default=DEFAULT_LOCAL_SIDECAR_WS,
        help=f"Local sidecar websocket URL. Default: {DEFAULT_LOCAL_SIDECAR_WS}",
    )
    parser.add_argument(
        "--server-base-url",
        default=DEFAULT_SERVER_BASE_URL,
        help=f"Telemetry web server base URL. Default: {DEFAULT_SERVER_BASE_URL}",
    )
    parser.add_argument(
        "--session-key",
        default=None,
        help="Existing session key to publish into. If omitted, a new session is created.",
    )
    args = parser.parse_args()

    session_key = await create_session_if_needed(args.server_base_url.rstrip("/"), args.session_key)
    ws_base = args.server_base_url.rstrip("/").replace("http://", "ws://").replace("https://", "wss://")
    server_ws_url = f"{ws_base}/ws?session_key={session_key}&role=producer"

    print()
    print(f"[bridge] session_key={session_key}")
    print(f"[bridge] engineer_url_hint={args.server_base_url.rstrip('/')}/frontend/session_viewer.html?server={args.server_base_url.rstrip('/')}&session_key={session_key}")
    print()

    await relay(args.local_sidecar_ws, server_ws_url)
    return 0


def main() -> int:
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n[bridge] stopped by user")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
