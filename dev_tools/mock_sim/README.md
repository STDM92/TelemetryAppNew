# Mock Sim

Dev-only external mock simulator for exercising the sidecar live pipeline.

## Purpose

This process reads an `.ibt` file and replays it as a live-like telemetry stream over local HTTP/WebSocket endpoints.

It is intended to test:

- adapter probing
- live adapter selection
- receiver connectivity
- runtime state publishing
- websocket state flow

without abusing `analyze` mode or keeping a dedicated `replay` runtime mode in the sidecar.

## Endpoints

- `GET /health`
- `GET /sim-info`
- `GET /status`
- `WS /stream`

## Run

```bash
python main.py --file "replay_files/mercedesamgevogt3_nurburgring combinedshortb 2026-03-15 19-07-40.ibt" --port 8766 --hz 60 --loop