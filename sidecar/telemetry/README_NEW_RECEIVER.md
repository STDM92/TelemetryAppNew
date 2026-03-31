# Adding a New Telemetry Receiver

This project uses a **simulator-agnostic unified telemetry model**. A receiver is responsible for reading raw telemetry from one game or simulator and translating it into a `UnifiedTelemetrySnapshot`.

The rest of the app must **not** depend on game-specific field names.

## Goal

A receiver should:

1. Connect to one telemetry source.
2. Read the latest available values.
3. Convert those values into the unified model.
4. Return a `UnifiedTelemetrySnapshot`.
5. Leave unsupported values as `None`.

## Design Rules

### 1. Keep game-specific logic inside the receiver

Good:
- `iRacing Speed -> powertrain.vehicle_speed_kph`
- `ACC fuel -> powertrain.fuel_remaining_l`

Bad:
- exposing raw source names like `LFtempCM` or `CarIdxLapDistPct` outside the receiver.

### 2. Do not invent data

If the source does not expose a channel, return `None`.

### 3. Normalize units before creating the snapshot

Receivers must convert raw source values into the project’s canonical units.

Examples:
- speed -> `kph`
- ride height -> `mm`
- damper velocity -> `mm/s`
- tire pressures -> `kPa`
- angles -> `rad`
- temperatures -> `C`
- lap times / gaps -> `s`
- distances -> `m`
- acceleration -> `m/s^2`

### 4. Prefer semantic names, not source names

The unified snapshot uses domain concepts:
- `inputs`
- `lap`
- `powertrain`
- `tires`
- `brakes`
- `suspension`
- `dynamics`
- `environment`
- `pit`
- `track_map`

### 5. Be defensive

A receiver should never crash because one channel is temporarily missing.

Recommended pattern:
- helper methods like `_get_float`, `_get_int`, `_get_bool`
- return `None` on missing or invalid values
- use `try/finally` when the source API needs buffer freeze/unfreeze behavior

## Receiver Interface Shape

A receiver should expose at least:

```python
class SomeGameReceiver:
    def check_connection(self) -> None:
        ...

    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        ...
```

Expected behavior:
- return `None` if disconnected
- return `None` if no valid sample is available
- return a populated `UnifiedTelemetrySnapshot` when data is available

## Recommended Build Order

When writing a new receiver, wire fields in this order:

1. `session`
2. `lap`
3. `race`
4. `inputs`
5. `powertrain`
6. `tires`
7. `brakes`
8. `suspension`
9. `dynamics`
10. `environment`
11. `pit`
12. `track_map`

This keeps the receiver usable early, even before all advanced channels are mapped.

## Mapping Example

Raw source:

```python
speed_mps = raw["Speed"]
```

Unified snapshot:

```python
powertrain = PowertrainData(
    vehicle_speed_kph=speed_mps * 3.6,
)
```

## Track Map Rules

If a simulator exposes per-car arrays or opponent lists:
- map them into `TrackMapData`
- skip invalid entries
- do not include placeholder rows for unavailable cars

For sources like iRacing where array slots can be present but invalid, treat sentinel values like `-1` as missing.

## Enum and Bitfield Rules

Raw telemetry often uses integer enums or bitfields.

Receiver responsibilities:
- decode them into stable string values for the unified snapshot
- keep the output semantic and readable

Examples:
- session state `4 -> "racing"`
- track location `3 -> "on_track"`
- flag bitfield -> `"green|start_go"`

## Session Metadata

Some games split telemetry into:
- fast live values
- slower session metadata

If richer metadata exists in a separate API or session document, the receiver may combine both.

Examples:
- track name
n- session type
- car info
- driver list

## Testing Checklist

Before considering a receiver done, verify:

- it connects and disconnects cleanly
- it returns `None` while disconnected
- it survives missing channels
- units are converted correctly
- unsupported data stays `None`
- enums are readable
- track map ignores invalid car slots
- snapshot creation does not leak source-specific names

## Common Mistakes

Do not:
- leak raw source names into shared models
- keep source units when they differ from project units
- fill missing values with fake zeros
- assume all cars expose the same sensors
- assume every source provides opponent data

## Minimal Template

```python
from sidecar.telemetry.models.unified_snapshot import UnifiedTelemetrySnapshot


class ExampleReceiver:
    def __init__(self) -> None:
        self.connected = False

    def check_connection(self) -> None:
        # update self.connected
        ...

    def capture_snapshot(self) -> UnifiedTelemetrySnapshot | None:
        self.check_connection()
        if not self.connected:
            return None

        # read raw values
        # convert units
        # map enums
        # return snapshot
        return UnifiedTelemetrySnapshot(
            source="example_game",
            timestamp=0.0,
        )
```
