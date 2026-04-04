use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::{Mutex, OnceLock};
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::{AppHandle, Manager};

static LOG_FILE_PATH: OnceLock<PathBuf> = OnceLock::new();
static LOG_WRITE_LOCK: Mutex<()> = Mutex::new(());

const LOG_FILE_NAME: &str = "driver_app.log";

pub fn init_logging(app: &AppHandle) -> Result<PathBuf, String> {
    let mut dir = app
        .path()
        .app_config_dir()
        .map_err(|e| format!("Failed to resolve app config directory for logging: {e}"))?;

    fs::create_dir_all(&dir)
        .map_err(|e| format!("Failed to create app config directory for logging: {e}"))?;

    dir.push(LOG_FILE_NAME);

    let _ = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&dir)
        .map_err(|e| format!("Failed to open driver app log file: {e}"))?;

    let _ = LOG_FILE_PATH.set(dir.clone());

    log_info(&format!("Driver app logging initialized. log_file={}", dir.display()));

    Ok(dir)
}

pub fn log_info(message: &str) {
    write_log_line("INFO", message);
}

pub fn log_warn(message: &str) {
    write_log_line("WARN", message);
}

pub fn log_error(message: &str) {
    write_log_line("ERROR", message);
}

fn write_log_line(level: &str, message: &str) {
    let timestamp = unix_timestamp_string();
    let line = format!("{timestamp} | {level:<5} | {message}\n");

    #[cfg(debug_assertions)]
    {
        eprint!("{line}");
    }

    let Some(path) = LOG_FILE_PATH.get() else {
        return;
    };

    let _guard = LOG_WRITE_LOCK.lock().unwrap();

    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = file.write_all(line.as_bytes());
    }
}

fn unix_timestamp_string() -> String {
    match SystemTime::now().duration_since(UNIX_EPOCH) {
        Ok(duration) => format!("{}", duration.as_secs()),
        Err(_) => "0".to_string(),
    }
}