# Live Telemetry Sidecar

Standalone telemetry backend sidecar.

## What it owns

- simulator connection
- live telemetry ingestion
- unified telemetry state
- runtime health/status
- local websocket and API publishing

## What it does not own

- desktop shell UI
- offline analysis workflows
- engineer web UI

## Development setup

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -e .
```

```bash
pip install -r requirements-dev.txt
```

## Run locally

```bash
python -m live_telemetry_sidecar
```

Or after installation:

```bash
live-telemetry-sidecar
```

With a custom port:

```bash
python -m live_telemetry_sidecar --port 8000
```

## Publish executable

Default onedir build:

```bash
python build_exe.py --clean --noconfirm
```

Optional onefile build:

```bash
python build_exe.py --clean --noconfirm --onefile
```

## Build output

Onedir build output:

```text
dist/live-telemetry-sidecar/live-telemetry-sidecar.exe
```

Onefile build output:

```text
dist/live-telemetry-sidecar.exe
```

## Tauri launch shape

Example launch arguments for the packaged sidecar:

```text
live-telemetry-sidecar.exe --port 8000
```
