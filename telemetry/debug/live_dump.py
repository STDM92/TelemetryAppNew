import json
import time

from telemetry.receivers.iracing_receiver import IRacingReceiver


CONNECT_TIMEOUT_SECONDS = 15.0
POLL_INTERVAL_SECONDS = 0.5
OUTPUT_PATH = "live_iracing_dump.json"


def make_json_safe(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, tuple):
        return [make_json_safe(v) for v in value]
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    return value


def main():
    receiver = IRacingReceiver()

    print("Waiting for iRacing...")

    start_time = time.monotonic()

    while True:
        try:
            receiver.check_connection()
        except Exception as e:
            print(f"Connection check failed: {e}")
            return

        if receiver.connected:
            break

        elapsed = time.monotonic() - start_time
        if elapsed >= CONNECT_TIMEOUT_SECONDS:
            print(f"Timed out after {CONNECT_TIMEOUT_SECONDS:.1f} seconds waiting for iRacing.")
            return

        time.sleep(POLL_INTERVAL_SECONDS)

    print("Connected. Capturing shared memory snapshot...")

    ir = receiver.ir

    schema = {}
    for header in ir._var_headers:
        schema[header.name] = {
            "desc": header.desc,
            "unit": header.unit,
            "count": header.count,
            "type": header.type,
        }

    ir.freeze_var_buffer_latest()

    try:
        values = {}
        for name in schema.keys():
            try:
                values[name] = make_json_safe(ir[name])
            except Exception as e:
                values[name] = {"_error": str(e)}
    finally:
        ir.unfreeze_var_buffer_latest()

    payload = {
        "_meta": {
            "source": "iracing_shared_memory",
            "captured_at": time.time(),
            "header_count": len(schema),
        },
        "schema": schema,
        "values": values,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Dump written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()