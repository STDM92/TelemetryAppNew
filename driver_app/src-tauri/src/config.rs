use crate::driver_logging::{log_error, log_info};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::{AppHandle, Manager};

#[derive(Debug, Clone, Serialize)]
pub struct BootstrapConfig {
    #[serde(rename = "backendBaseUrl")]
    pub backend_base_url: String,

    #[serde(rename = "backendWebSocketUrl")]
    pub backend_websocket_url: String,

    #[serde(rename = "mode")]
    pub mode: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AppConfig {
    pub sidecar_executable_path: String,
    pub backend_port: u16,
    pub uplink_enabled: bool,
    pub uplink_server_base_url: String,
    pub uplink_session_key: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AppConfigUpdate {
    pub sidecar_executable_path: String,
    pub backend_port: u16,
    pub uplink_enabled: bool,
    pub uplink_server_base_url: String,
    pub uplink_session_key: String,
}

const CONFIG_FILE_NAME: &str = "driver_app_config.json";

pub fn load_config(app: &AppHandle) -> AppConfig {
    let path = match config_file_path(app) {
        Ok(path) => path,
        Err(err) => {
            log_warn_fallback(&format!("Failed to resolve config path. Using defaults. error={err}"));
            return AppConfig::default();
        }
    };

    let raw = match fs::read_to_string(path) {
        Ok(raw) => raw,
        Err(err) => {
            log_info(&format!("Config file not loaded. Using defaults. error={err}"));
            return AppConfig::default();
        }
    };

    serde_json::from_str::<AppConfig>(&raw).unwrap_or_else(|err| {
        log_error(&format!("Failed to parse config file. Using defaults. error={err}"));
        AppConfig::default()
    })
}

pub fn save_config(app: &AppHandle, config: &AppConfig) -> Result<(), String> {
    let path = config_file_path(app)?;

    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create config directory: {e}"))?;
    }

    let raw = serde_json::to_string_pretty(config)
        .map_err(|e| format!("Failed to serialize app config: {e}"))?;

    fs::write(&path, raw).map_err(|e| format!("Failed to write config file: {e}"))?;
    log_info(&format!(
        "Saved app config. sidecar_executable_path={} backend_port={} uplink_enabled={} uplink_server_base_url={} uplink_session_key={}",
        config.sidecar_executable_path,
        config.backend_port,
        config.uplink_enabled,
        config.uplink_server_base_url,
        config.uplink_session_key,
    ));
    Ok(())
}

fn log_warn_fallback(message: &str) {
    log_info(message);
}

fn config_file_path(app: &AppHandle) -> Result<PathBuf, String> {
    let mut dir = app
        .path()
        .app_config_dir()
        .map_err(|e| format!("Failed to resolve app config directory: {e}"))?;

    dir.push(CONFIG_FILE_NAME);
    Ok(dir)
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            sidecar_executable_path:
            "sidecars/live_telemetry_sidecar/dist/live-telemetry-sidecar/live-telemetry-sidecar.exe"
                .to_string(),
            backend_port: 8000,
            uplink_enabled: false,
            uplink_server_base_url: "http://18.198.45.251:8080".to_string(),
            uplink_session_key: String::new(),
        }
    }
}
