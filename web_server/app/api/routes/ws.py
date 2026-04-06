from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.models.messages import (
    ServerErrorMessage,
    ServerInfoMessage,
    TelemetrySnapshotMessage,
    WebSocketMessageType,
    WebSocketRole,
)

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    session_key = (websocket.query_params.get("session_key") or "").strip().upper()
    role_value = (websocket.query_params.get("role") or "").strip().lower()

    if not session_key:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing session_key.")
        return

    try:
        role = WebSocketRole(role_value)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid role.")
        return

    registry = websocket.app.state.session_registry
    hub = websocket.app.state.connection_hub
    session = registry.get_session(session_key)
    if session is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unknown session_key.")
        return

    await websocket.accept()
    hub.register(session_key, role, websocket)
    _sync_session_connection_state(registry, hub, session_key)

    await websocket.send_json(
        ServerInfoMessage(
            payload={
                "event": "connected",
                "session_key": session_key,
                "role": role.value,
            }
        ).model_dump(mode="json")
    )

    try:
        if role == WebSocketRole.PRODUCER:
            await _run_producer_loop(websocket, registry, hub, session_key)
        else:
            await _run_engineer_loop(websocket)
    except WebSocketDisconnect:
        pass
    finally:
        hub.unregister(session_key, role, websocket)
        _sync_session_connection_state(registry, hub, session_key)


async def _run_producer_loop(websocket: WebSocket, registry, hub, session_key: str) -> None:
    while True:
        raw_message = await websocket.receive_json()
        try:
            message = TelemetrySnapshotMessage.model_validate(raw_message)
        except Exception:
            await websocket.send_json(
                ServerErrorMessage(
                    payload={
                        "event": "invalid_message",
                        "expected_type": WebSocketMessageType.TELEMETRY_SNAPSHOT.value,
                    }
                ).model_dump(mode="json")
            )
            continue

        registry.record_snapshot(
            session_key=session_key,
            snapshot=message.payload,
            message_type=message.type.value,
        )
        await hub.broadcast_to_engineers(
            session_key=session_key,
            message=message.model_dump(mode="json"),
        )


async def _run_engineer_loop(websocket: WebSocket) -> None:
    while True:
        await websocket.receive_text()



def _sync_session_connection_state(registry, hub, session_key: str) -> None:
    counts = hub.get_connection_counts(session_key)
    registry.set_producer_attached(
        session_key,
        counts[WebSocketRole.PRODUCER.value] > 0,
    )
    registry.set_engineer_count(
        session_key,
        counts[WebSocketRole.ENGINEER.value],
    )
