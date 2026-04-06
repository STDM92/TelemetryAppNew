from fastapi.testclient import TestClient

from app.main import app


def test_health_smoke() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_session_create_and_lookup() -> None:
    client = TestClient(app)

    create_response = client.post("/api/session/create")
    assert create_response.status_code == 200
    session_key = create_response.json()["session_key"]

    lookup_response = client.get(f"/api/session/{session_key}")
    assert lookup_response.status_code == 200
    assert lookup_response.json()["session_key"] == session_key



def test_websocket_producer_to_engineer_relay() -> None:
    client = TestClient(app)
    create_response = client.post("/api/session/create")
    session_key = create_response.json()["session_key"]

    with client.websocket_connect(f"/ws?session_key={session_key}&role=engineer") as engineer_ws:
        engineer_connected = engineer_ws.receive_json()
        assert engineer_connected["type"] == "server_info"

        with client.websocket_connect(f"/ws?session_key={session_key}&role=producer") as producer_ws:
            producer_connected = producer_ws.receive_json()
            assert producer_connected["type"] == "server_info"

            producer_ws.send_json(
                {
                    "type": "telemetry_snapshot",
                    "payload": {
                        "speed_kph": 123.4,
                        "gear": 4,
                    },
                }
            )

            relayed = engineer_ws.receive_json()
            assert relayed["type"] == "telemetry_snapshot"
            assert relayed["payload"]["speed_kph"] == 123.4
