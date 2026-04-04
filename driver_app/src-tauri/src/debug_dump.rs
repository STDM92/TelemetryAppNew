#[cfg(debug_assertions)]
pub fn debug_dump_json<T: serde::Serialize>(event: &str, value: &T) {
    use serde_json::json;
    use std::fs::OpenOptions;
    use std::io::Write;
    use std::path::PathBuf;

    let path = PathBuf::from("debug-sidecar-state.ndjson");

    let payload = json!({
    "event": event,
    "timestamp": chrono::Utc::now().to_rfc3339(),
    "value": value,
    });

    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(file, "{}", payload);
    }
}

#[cfg(not(debug_assertions))]
pub fn debug_dump_json<T: serde::Serialize>(_event: &str, _value: &T) {}