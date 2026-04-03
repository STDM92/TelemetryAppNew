use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::{AppHandle, Manager};

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BootstrapConfig {
    pub backend_base_url: String,
    pub backend_websocket_url: String,
    pub mode: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AppConfig {
    pub python_command: String,
    pub backend_port: u16,
    pub backend_mode: String,
    pub backend_file_path: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AppConfigUpdate {
    pub python_command: String,
    pub backend_port: u16,
    pub backend_mode: String,
    pub backend_file_path: Option<String>,
}

const CONFIG_FILE_NAME: &str = "driver_app_config.json";

pub fn load_config(app: &AppHandle) -> AppConfig {
    let path = match config_file_path(app) {
        Ok(path) => path,
        Err(_) => return AppConfig::default(),
    };

    let raw = match fs::read_to_string(path) {
        Ok(raw) => raw,
        Err(_) => return AppConfig::default(),
    };

    serde_json::from_str::<AppConfig>(&raw).unwrap_or_default()
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
    Ok(())
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
            python_command: "python".to_string(),
            backend_port: 8000,
            backend_mode: "live".to_string(),
            backend_file_path: None,
        }
    }
}
